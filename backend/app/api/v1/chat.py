import httpx
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi import APIRouter, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool
from app.api.deps import get_current_user
from app.agents.omni_agent import OmniAgent
from app.core.config import settings
from app.database.repositories.agent_run_repository import AgentRunRepository
from app.database.repositories.chat_repository import ChatRepository
from app.database.repositories.task_repository import TaskRepository
from app.database.client import get_supabase_client
from app.llm.openai_provider import get_llm_provider
from app.schemas.chat import ChatRequest, ChatResponse


router = APIRouter()


def current_llm_model() -> str:
    if settings.llm_provider == "openrouter" and settings.openrouter_model:
        return settings.openrouter_model
    return settings.openai_model

def print_agent_start(agent_name: str, user_email: str, input_data: any) -> datetime:
    print(f"\n=======================Input====================")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Agent: {agent_name} | User: {user_email}")
    print(f"Input:  {input_data}")
    print(f"[Calling LLM...]")
    return datetime.now()

def print_agent_end(agent_name: str, start_time: datetime, output_data: any):
    latency = (datetime.now() - start_time).total_seconds()
    print(f"\n=======================Output====================")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Agent: {agent_name} | Response received in {latency:.2f}s")
    print(f"Output: {output_data}")
    print(f"=======================================================\n")


@router.get("/")
def chat_status() -> dict[str, str]:
    return {"status": "chat api ready"}

@router.get("/history")
def get_chat_history(
    limit: int = 20, 
    offset: int = 0, 
    user_id: str = Depends(get_current_user)
) -> dict:
    repo = ChatRepository()
    messages = repo.list_recent(user_id, limit=limit, offset=offset)
    return {"messages": messages}


@router.post("/", response_model=ChatResponse)
async def create_chat_message(
    payload: ChatRequest,
    user_id: str = Depends(get_current_user)
) -> ChatResponse:
    chat_repository = ChatRepository()
    task_repository = TaskRepository()
    agent_run_repository = AgentRunRepository()
    llm_provider = get_llm_provider()

    user_message = chat_repository.create("user", payload.message, user_id)
    chat_history = chat_repository.list_recent(user_id)
    
    # Truncate history to last 4 messages (2 interactions) to drastically save LLM tokens and latency
    if chat_history and len(chat_history) > 4:
        chat_history = chat_history[-4:]
        
    omni_agent = OmniAgent(llm_provider)

    try:
        # Run the synchronous auth fetch in a threadpool to prevent event loop deadlocks
        user_obj = await run_in_threadpool(get_supabase_client().auth.admin.get_user_by_id, user_id)
        user_email = user_obj.user.email if user_obj and user_obj.user else user_id
    except Exception:
        user_email = user_id

    try:
        open_tasks = task_repository.list_by_status("open", user_id)
        
        t0 = print_agent_start("omni_agent", user_email, {"message": payload.message})
        extraction = await omni_agent.process(payload.message, open_tasks, chat_history)
        print_agent_end("omni_agent", t0, extraction)
        
        extraction_status = "needs_follow_up" if extraction.get("needs_follow_up") else "success"
        agent_run_id = agent_run_repository.create(
            chat_message_id=user_message["id"],
            user_id=user_id,
            agent_name="omni_agent",
            llm_provider=settings.llm_provider,
            llm_model=current_llm_model(),
            status=extraction_status,
            input_data={"message": payload.message},
            output_data=extraction,
        )["id"]

        if extraction.get("needs_follow_up"):
            reply = extraction.get("follow_up_question") or "Could you clarify what you want to do?"
            chat_repository.create("assistant", reply, user_id, {"extraction": extraction})
            return ChatResponse(message=reply, needs_follow_up=True)

        action = extraction.get("action")

        if action not in ("create_task", "create_problem", "update_task"):
            msg_lower = payload.message.lower()
            if any(greet in msg_lower for greet in ["hi", "hello", "hey", "morning", "evening"]):
                reply = "Hi there! What can I schedule or track for you today?"
            else:
                reply = "I saved your message! Tell me with 'remind me' when you want a todo created, or ask me to track a problem."
            chat_repository.create("assistant", reply, user_id, {"extraction": extraction})
            return ChatResponse(message=reply)

        if action == "update_task":
            if not extraction.get("task_id"):
                reply = "Which task did you want to update?"
                chat_repository.create("assistant", reply, user_id, {"extraction": extraction})
                return ChatResponse(message=reply, needs_follow_up=True)

            task_id = extraction["task_id"]
            
            item_type = None
            metadata = None
            if extraction.get("move_to_scheduler"):
                item_type = "problem"
                metadata = {"revision_count": 1}
            elif extraction.get("move_to_todo"):
                item_type = "task"
                
            updated_task = task_repository.update_task_details(
                task_id=task_id,
                user_id=user_id,
                title=extraction.get("title") or "Untitled",
                todo_at=extraction.get("todo_at"),
                reminder_start_at=extraction.get("reminder_start_at"),
                item_type=item_type,
                metadata=metadata
            )

            if not updated_task:
                reply = "I couldn't find that task to update."
                chat_repository.create("assistant", reply, user_id)
                return ChatResponse(message=reply)

            todo_datetime = datetime.fromisoformat(updated_task['todo_at'])
            local_datetime = todo_datetime.astimezone(ZoneInfo(updated_task['timezone']))
            formatted_date = local_datetime.strftime("%b %d, %Y at %I:%M %p")

            reply = f"Task updated! '{updated_task['title']}' is now scheduled for {formatted_date}."
            chat_repository.create("assistant", reply, user_id, {"task_id": updated_task["id"]})
            return ChatResponse(message=reply, task_created=False, task=updated_task)

        if action == "create_problem":
            problem_url = extraction.get("problem_url")
            title = extraction.get("title") or "Review Problem"
            if problem_url and not title.lower().startswith("review"):
                title = f"Review: {title}"
                
            now = datetime.now()
            todo_at = now + timedelta(days=3)
            
            task_data = {
                "title": title,
                "todo_at": todo_at.isoformat(),
                "reminder_start_at": now.isoformat(),
                "timezone": settings.app_timezone,
                "target_time": None
            }
            
            task = task_repository.create_from_extraction(
                extraction=task_data,
                source_chat_message_id=user_message["id"],
                user_id=user_id,
                agent_run_id=agent_run_id,
                item_type="problem",
                extra_metadata={"url": problem_url, "revision_count": 1}
            )
            
            reply = f"Problem scheduled for spaced repetition! First review is in 3 days (on {todo_at.strftime('%b %d')})."
            chat_repository.create("assistant", reply, user_id, {"task_id": task["id"]})
            return ChatResponse(message=reply, task_created=True, task=task)

        if action == "create_task":
            if not extraction.get("title"):
                extraction["title"] = "Untitled Reminder"
                
            if not extraction.get("todo_at"):
                now = datetime.now(ZoneInfo(settings.app_timezone))
                extraction["todo_at"] = now.isoformat()
                extraction["reminder_start_at"] = now.isoformat()
                extraction["timezone"] = settings.app_timezone
                
            extra_metadata = {}
            if extraction.get("problem_url"):
                extra_metadata["url"] = extraction["problem_url"]
                
            task = task_repository.create_from_extraction(
                extraction=extraction,
                source_chat_message_id=user_message["id"],
                user_id=user_id,
                agent_run_id=agent_run_id,
                extra_metadata=extra_metadata if extra_metadata else None
            )
            
            todo_datetime = datetime.fromisoformat(task['todo_at'])
            local_datetime = todo_datetime.astimezone(ZoneInfo(task['timezone']))
            formatted_date = local_datetime.strftime("%b %d, %Y at %I:%M %p")
            
            reply = (
                f"Reminder created: {task['title']}. "
                f"Todo date: {formatted_date}."
            )
            chat_repository.create("assistant", reply, user_id, {"task_id": task["id"]})
            return ChatResponse(message=reply, task_created=True, task=task)

    except (ValueError, httpx.HTTPStatusError) as exc:
        reply = "Network error. Please try again later."
        chat_repository.create("assistant", reply, user_id)
        return ChatResponse(message=reply)
    except Exception as exc:
        import traceback
        traceback.print_exc()
        reply = "An unexpected error occurred. Please try again later."
        chat_repository.create("assistant", reply, user_id)
        return ChatResponse(message=reply)

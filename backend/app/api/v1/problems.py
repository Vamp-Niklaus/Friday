from datetime import date, datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.core.config import settings
from app.database.repositories.task_repository import TaskRepository
from app.database.repositories.user_settings_repository import UserSettingsRepository
from app.schemas.problems import ProblemQueueResponse, QueueSettingsUpdateRequest

router = APIRouter()

@router.get("/queue", response_model=ProblemQueueResponse)
def get_problem_queue(user_id: str = Depends(get_current_user)) -> dict:
    settings_repo = UserSettingsRepository()
    task_repo = TaskRepository()
    
    # Get or create user settings
    user_settings = settings_repo.get_or_create(user_id)
    daily_quota = user_settings["daily_quota"]
    
    # Calculate days since start using local timezone
    tz = ZoneInfo(settings.app_timezone)
    today = datetime.now(tz).date()
    start_date_str = user_settings["queue_start_date"]
    
    if isinstance(start_date_str, str):
        start_date = date.fromisoformat(start_date_str)
    else:
        start_date = start_date_str
        
    days_since_start = (today - start_date).days
    
    # If somehow negative (e.g. timezone edge cases), clamp to 0
    if days_since_start < 0:
        days_since_start = 0

    expected_completed = days_since_start * daily_quota
    actual_completed = task_repo.count_completed_problems(user_id)
    
    # Due today is the backlog (expected - actual) plus today's quota
    backlog = expected_completed - actual_completed
    if backlog < 0:
        backlog = 0 # No positive balance for working ahead
        
    due_today_count = backlog + daily_quota

    open_problems = task_repo.list_open_problems(user_id)
    
    due_today_list = []
    upcoming_list = []
    past_due_list = []
    solved_today_list = []
    
    for p in open_problems:
        p_dt = datetime.fromisoformat(p["todo_at"]).astimezone(tz)
        p_date = p_dt.date()
        p["formatted_date"] = p_dt.strftime("%b %d")
        
        # Check if solved today
        meta = p.get("metadata") or {}
        last_revised = meta.get("last_revised_at")
        if last_revised:
            lr_date = datetime.fromisoformat(last_revised).astimezone(tz).date()
            if lr_date == today:
                solved_today_list.append(p)
        
        if p_date < today:
            past_due_list.append(p)
        elif p_date == today:
            due_today_list.append(p)
        else:
            upcoming_list.append(p)
            
    # Combine past_due and due_today for quota application
    due_queue = past_due_list + due_today_list
    
    # Apply quota
    allowed_due = due_queue[:due_today_count]
    overflow = due_queue[due_today_count:]
    
    upcoming = overflow + upcoming_list
    
    # Separate allowed_due back into past_due and due_today
    final_past_due = [p for p in allowed_due if datetime.fromisoformat(p["todo_at"]).astimezone(tz).date() < today]
    final_due_today = [p for p in allowed_due if datetime.fromisoformat(p["todo_at"]).astimezone(tz).date() == today]
    
    # Sort solved today by last_revised_at descending
    solved_today_list.sort(
        key=lambda x: datetime.fromisoformat((x.get("metadata") or {}).get("last_revised_at")), 
        reverse=True
    )
    
    # Override actual_completed to show the count of solved today in the UI
    solved_today_count = len(solved_today_list)
    
    return {
        "daily_quota": daily_quota,
        "days_since_start": days_since_start,
        "expected_completed": expected_completed,
        "actual_completed": solved_today_count,
        "due_today_count": due_today_count,
        "past_due": final_past_due,
        "due_today": final_due_today,
        "upcoming": upcoming,
        "solved_today": solved_today_list
    }


@router.get("/completed")
def get_completed_problems(user_id: str = Depends(get_current_user)) -> dict:
    task_repo = TaskRepository()
    completed = task_repo.list_completed_problems(user_id)
    tz = ZoneInfo(settings.app_timezone)
    
    for p in completed:
        if p.get("completed_at"):
            p_dt = datetime.fromisoformat(p["completed_at"]).astimezone(tz)
            p["formatted_date"] = p_dt.strftime("%b %d, %Y")
            
    return {"completed": completed}

@router.patch("/settings")
def update_queue_settings(
    payload: QueueSettingsUpdateRequest,
    user_id: str = Depends(get_current_user)
) -> dict:
    if payload.daily_quota < 1:
        raise HTTPException(status_code=400, detail="Daily quota must be at least 1")
        
    repo = UserSettingsRepository()
    updated = repo.update_quota(user_id, payload.daily_quota)
    return {"status": "success", "settings": updated}

@router.post("/{task_id}/revise")
def revise_problem(task_id: str, user_id: str = Depends(get_current_user)) -> dict:
    task_repo = TaskRepository()
    task = task_repo.get_by_id(task_id, user_id)
    
    if not task or task["item_type"] != "problem":
        raise HTTPException(status_code=404, detail="Problem not found")
        
    metadata = task.get("metadata") or {}
    revision_count = metadata.get("revision_count", 1)
    
    import random
    from datetime import timedelta
    
    if revision_count == 1:
        days_to_add = 7
    elif revision_count == 2:
        days_to_add = 21
    else:
        days_to_add = random.randint(25, 40)
        
    # We base the new date off TODAY, not the old todo_at, so they don't get punished for being late
    tz = ZoneInfo(settings.app_timezone)
    now = datetime.now(tz)
    new_todo_at = now + timedelta(days=days_to_add)
    
    updated_task = task_repo.update_problem_revision(
        task_id=task_id, 
        todo_at=new_todo_at.isoformat(), 
        new_revision_count=revision_count + 1, 
        user_id=user_id
    )
    
    return {"status": "success", "task": updated_task, "next_review_days": days_to_add}

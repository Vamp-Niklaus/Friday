import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.llm.base import LLMProvider


class OmniAgent:
    """Unified agent that routes and extracts tasks/problems using Persona Debate (Chain of Thought)."""

    def __init__(self, llm_provider: LLMProvider) -> None:
        self.llm_provider = llm_provider

    async def process(
        self,
        message: str,
        open_tasks: list[dict],
        chat_history: list[dict] | None = None,
    ) -> dict:
        now = datetime.now(ZoneInfo(settings.app_timezone))
        
        # Minified task details to save tokens
        tasks_context = [
            {"id": t["id"], "title": t["title"], "date": t["todo_at"][:10]}
            for t in open_tasks
        ]
        tasks_json = json.dumps(tasks_context, separators=(',', ':'))

        system_prompt = (
            "You are the Omni-Agent for a personal assistant. You must analyze the user's message using a 'Persona Debate' (Chain of Thought) before deciding on an action.\n\n"
            "=== THE PERSONAS ===\n"
            "1. Scheduler Persona: Evaluates if this is a Spaced Repetition problem or a standard reminder. "
            "If the user shares a URL/problem and does NOT mention a specific time, it argues for 'create_problem' (it will automatically be scheduled 3 days later). "
            "If they specify a strict time/date (even with a URL), it argues for a strict schedule ('create_task').\n"
            "2. Todo Maker Persona: Checks the user's Open Tasks. If the message implies changing, postponing, or renaming an existing task, it argues for 'update_task' and identifies the task_id. Otherwise, it argues for a new task.\n\n"
            f"The current local date and time is {now.isoformat()} in {settings.app_timezone}.\n"
            f"User's Open Tasks: {tasks_json}\n\n"
            "=== FEW-SHOT EXAMPLES ===\n"
            "Example 1: 'remind me to call father tomorrow instead of the day after'\n"
            "debate_log: 'Scheduler: The user mentions a strict time (tomorrow), so it's a task. Todo Maker: They said \"instead of\", implying a change. I checked Open Tasks and found \"call father\". Action should be update_task.'\n"
            "action: 'update_task'\n"
            "task_id: '<uuid>'\n\n"
            "Example 2: 'schedule this problem https://leetcode.com/problems/two-sum/'\n"
            "debate_log: 'Scheduler: A URL is provided with no specific time. This should be added to the Spaced Repetition queue for 3 days later. Todo Maker: No existing task matches this intent. Action should be create_problem.'\n"
            "action: 'create_problem'\n"
            "title: 'Solve Two Sum (LeetCode)'\n"
            "problem_url: 'https://leetcode.com/problems/two-sum/'\n\n"
            "Example 3: 'remind me to solve https://leetcode.com/problems/zigzag-conversion/ tomorrow at 5pm'\n"
            "debate_log: 'Scheduler: A URL is provided, but a strict time (tomorrow at 5pm) is explicitly given. Therefore, this must bypass the spaced repetition queue and be a standard reminder. Todo Maker: This is a new task. Action should be create_task.'\n"
            "action: 'create_task'\n"
            "title: 'Solve Zigzag Conversion (LeetCode)'\n"
            "problem_url: 'https://leetcode.com/problems/zigzag-conversion/'\n\n"
            "=== OUTPUT FORMAT ===\n"
            "Return ONLY JSON with these exact keys:\n"
            "- debate_log (string: the personas discussing the input)\n"
            "- action (string: 'create_task', 'create_problem', 'update_task', or 'general')\n"
            "- task_id (string or null: UUID of the task to update, if action is update_task)\n"
            "- title (string: extracted concise title without 'remind me'. If a URL is provided, extract a human-readable name like 'Solve Zigzag Conversion (LeetCode)'. DO NOT leave raw URLs in the title.)\n"
            "- problem_url (string or null: the URL if provided in the prompt, regardless of whether action is create_task or create_problem)\n"
            "- target_time (string or null: ISO8601 string e.g. YYYY-MM-DDTHH:MM:SS if a specific time is requested for create_task/update_task. Default to 09:00:00 if only a date is given)\n"
            "- move_to_scheduler (boolean: true if action is update_task and the user explicitly wants to move this task to the Spaced Repetition Scheduler)\n"
            "- move_to_todo (boolean: true if action is update_task and the user explicitly wants to move this from the Scheduler to the standard ToDo list)\n"
            "- needs_follow_up (boolean: true if intent is extremely unclear and you cannot determine if it belongs in ToDo or Spaced Repetition)\n"
            "- follow_up_question (string or null: the question to ask if needs_follow_up is true. MUST include a helpful hint like: \"Tip: Say 'remind me to...' to add to your ToDo list, or say 'add revision for...' to add to the Scheduler.\")"
        )

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(chat_history or [])
        if not chat_history:
            messages.append({"role": "user", "content": message})

        extracted = await self.llm_provider.chat_json(messages)

        # Post-processing time values
        target_time = extracted.get("target_time")
        if target_time:
            todo_at = datetime.fromisoformat(target_time)
            if todo_at.tzinfo is None:
                todo_at = todo_at.replace(tzinfo=ZoneInfo(settings.app_timezone))
            
            reminder_start_at = max(now, todo_at - timedelta(days=1))
            extracted["todo_at"] = todo_at.isoformat()
            extracted["reminder_start_at"] = reminder_start_at.isoformat()
            extracted["timezone"] = settings.app_timezone
            
        return extracted

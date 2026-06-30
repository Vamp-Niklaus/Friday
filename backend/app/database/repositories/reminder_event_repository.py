from datetime import datetime, timezone, timedelta

from app.database.client import get_supabase_client


class ReminderEventRepository:
    """Persistence methods for reminder delivery events."""

    def __init__(self) -> None:
        self.client = get_supabase_client()

    def get_open_tasks_due(self, current_time: str, min_time: str | None = None) -> list[dict]:
        """Return open tasks whose todo_at is exactly now or in the past. Optional min_time to bound past lookups."""
        query = self.client.table("tasks").select("*").eq("status", "open").lte("todo_at", current_time)
        
        if min_time:
            query = query.gte("todo_at", min_time)
            
        result = query.order("todo_at", desc=False).execute()
        return result.data

    def was_already_sent(self, task_id: str, scheduled_for: str) -> bool:
        """Check if a reminder was already sent for this exact task's due time."""
        result = (
            self.client.table("reminder_events")
            .select("id")
            .eq("task_id", task_id)
            .eq("scheduled_for", scheduled_for)
            .eq("channel", "telegram")
            .eq("status", "sent")
            .limit(1)
            .execute()
        )
        return len(result.data) > 0

    def has_been_sent_in_last_x_hours(self, task_id: str, hours: float) -> bool:
        """Check if a reminder was sent for this task within the last X hours."""
        threshold_time = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        result = (
            self.client.table("reminder_events")
            .select("id")
            .eq("task_id", task_id)
            .eq("channel", "telegram")
            .eq("status", "sent")
            .gte("sent_at", threshold_time)
            .limit(1)
            .execute()
        )
        return len(result.data) > 0

    def log_sent(self, task_id: str, scheduled_for: str, message: str, user_id: str) -> dict:
        """Log a successfully sent reminder."""
        result = (
            self.client.table("reminder_events")
            .insert(
                {
                    "user_id": user_id,
                    "task_id": task_id,
                    "scheduled_for": scheduled_for,
                    "sent_at": datetime.now(timezone.utc).isoformat(),
                    "channel": "telegram",
                    "status": "sent",
                    "message": message,
                }
            )
            .execute()
        )
        return result.data[0]

    def log_failed(self, task_id: str, scheduled_for: str, error: str, user_id: str) -> dict:
        """Log a failed reminder attempt."""
        result = (
            self.client.table("reminder_events")
            .insert(
                {
                    "user_id": user_id,
                    "task_id": task_id,
                    "scheduled_for": scheduled_for,
                    "channel": "telegram",
                    "status": "failed",
                    "error": error,
                }
            )
            .execute()
        )
        return result.data[0]

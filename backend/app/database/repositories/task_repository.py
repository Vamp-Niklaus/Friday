from datetime import datetime, timezone

from app.database.client import get_supabase_client


class TaskRepository:
    """Persistence methods for reminder tasks."""

    def __init__(self) -> None:
        self.client = get_supabase_client()

    def create_from_extraction(
        self,
        extraction: dict,
        source_chat_message_id: str,
        user_id: str,
        agent_run_id: str | None = None,
        item_type: str = "task",
        extra_metadata: dict | None = None,
    ) -> dict:
        metadata = {"target_time": extraction.get("target_time")}
        if extra_metadata:
            metadata.update(extra_metadata)
            
        result = (
            self.client.table("tasks")
            .insert(
                {
                    "user_id": user_id,
                    "source_chat_message_id": source_chat_message_id,
                    "agent_run_id": agent_run_id,
                    "title": extraction["title"],
                    "todo_at": extraction["todo_at"],
                    "reminder_start_at": extraction["reminder_start_at"],
                    "timezone": extraction["timezone"],
                    "item_type": item_type,
                    "metadata": metadata,
                }
            )
            .execute()
        )
        return result.data[0]

    def get_by_id(self, task_id: str, user_id: str) -> dict | None:
        result = (
            self.client.table("tasks")
            .select("*")
            .eq("id", task_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    def list_by_status(self, status: str, user_id: str, item_type: str = "task") -> list[dict]:
        result = (
            self.client.table("tasks")
            .select("*")
            .eq("status", status)
            .eq("item_type", item_type)
            .eq("user_id", user_id)
            .order("todo_at", desc=False)
            .order("created_at", desc=False)
            .execute()
        )
        return result.data

    def count_completed_problems(self, user_id: str) -> int:
        result = (
            self.client.table("tasks")
            .select("id", count="exact")
            .eq("status", "completed")
            .eq("item_type", "problem")
            .eq("user_id", user_id)
            .execute()
        )
        return result.count if result.count is not None else 0

    def list_completed_problems(self, user_id: str) -> list[dict]:
        result = (
            self.client.table("tasks")
            .select("*")
            .eq("status", "completed")
            .eq("item_type", "problem")
            .eq("user_id", user_id)
            .order("completed_at", desc=True)
            .execute()
        )
        return result.data

    def list_open_problems(self, user_id: str) -> list[dict]:
        result = (
            self.client.table("tasks")
            .select("*")
            .eq("status", "open")
            .eq("item_type", "problem")
            .eq("user_id", user_id)
            .order("created_at", desc=False)
            .execute()
        )
        return result.data

    def update_title(self, task_id: str, title: str, user_id: str) -> dict | None:
        result = (
            self.client.table("tasks")
            .update({"title": title.strip()})
            .eq("id", task_id)
            .eq("user_id", user_id)
            .execute()
        )
        return result.data[0] if result.data else None

    def mark_completed(self, task_id: str, user_id: str) -> dict | None:
        result = (
            self.client.table("tasks")
            .update(
                {
                    "status": "completed",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            .eq("id", task_id)
            .eq("user_id", user_id)
            .execute()
        )
        return result.data[0] if result.data else None

    def update_problem_revision(self, task_id: str, todo_at: str, new_revision_count: int, user_id: str) -> dict | None:
        # First get the current metadata to merge
        task = self.get_by_id(task_id, user_id)
        if not task:
            return None
            
        metadata = task.get("metadata") or {}
        metadata["revision_count"] = new_revision_count
        metadata["last_revised_at"] = datetime.now(timezone.utc).isoformat()
        
        result = (
            self.client.table("tasks")
            .update({
                "todo_at": todo_at,
                "metadata": metadata
            })
            .eq("id", task_id)
            .eq("user_id", user_id)
            .execute()
        )
        return result.data[0] if result.data else None

    def delete_task(self, task_id: str, user_id: str) -> bool:
        result = (
            self.client.table("tasks")
            .delete()
            .eq("id", task_id)
            .eq("user_id", user_id)
            .execute()
        )
        return len(result.data) > 0

    def update_task_details(
        self,
        task_id: str,
        user_id: str,
        title: str,
        todo_at: str | None = None,
        reminder_start_at: str | None = None,
        item_type: str | None = None,
        metadata: dict | None = None,
    ) -> dict | None:
        updates = {"title": title}
        if todo_at:
            updates["todo_at"] = todo_at
        if reminder_start_at:
            updates["reminder_start_at"] = reminder_start_at
        if item_type:
            updates["item_type"] = item_type
        if metadata is not None:
            # We fetch existing metadata to merge
            task = self.get_by_id(task_id, user_id)
            existing_meta = task.get("metadata") or {} if task else {}
            existing_meta.update(metadata)
            updates["metadata"] = existing_meta

        result = (
            self.client.table("tasks")
            .update(updates)
            .eq("id", task_id)
            .eq("user_id", user_id)
            .execute()
        )
        return result.data[0] if result.data else None

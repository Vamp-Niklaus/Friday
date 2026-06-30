from pydantic import BaseModel
from app.schemas.todos import TaskResponse

class QueueSettingsUpdateRequest(BaseModel):
    daily_quota: int

class ProblemQueueResponse(BaseModel):
    daily_quota: int
    days_since_start: int
    expected_completed: int
    actual_completed: int
    due_today_count: int
    past_due: list[TaskResponse]
    due_today: list[TaskResponse]
    upcoming: list[TaskResponse]
    solved_today: list[TaskResponse]

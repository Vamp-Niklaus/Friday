from pydantic import BaseModel, Field


class TaskUpdateRequest(BaseModel):
    title: str = Field(min_length=1)


class TaskResponse(BaseModel):
    id: str
    title: str
    item_type: str
    notes: str | None = None
    status: str
    todo_at: str
    next_revision_at: str | None = None
    reminder_start_at: str
    timezone: str
    completed_at: str | None = None
    created_at: str
    updated_at: str
    metadata: dict


class TaskGroup(BaseModel):
    date: str
    tasks: list[TaskResponse]


class TaskGroupResponse(BaseModel):
    groups: list[TaskGroup]

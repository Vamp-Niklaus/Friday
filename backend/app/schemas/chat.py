from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    message: str
    task_created: bool = False
    task: dict | None = None
    needs_follow_up: bool = False

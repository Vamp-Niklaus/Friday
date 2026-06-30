from pydantic import BaseModel, Field


class TelegramTestRequest(BaseModel):
    message: str = Field(default="Doraemon Telegram test message.", min_length=1)


class TelegramTestResponse(BaseModel):
    status: str
    telegram_response: dict

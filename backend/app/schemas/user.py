from pydantic import BaseModel
from typing import Optional

class UserSettingsResponse(BaseModel):
    display_name: Optional[str] = None
    daily_quota: int
    telegram_chat_id: Optional[str] = None
    telegram_is_verified: bool

class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = None
    daily_quota: int

class TelegramVerifyRequest(BaseModel):
    telegram_chat_id: str

class TelegramVerifyConfirm(BaseModel):
    otp: str

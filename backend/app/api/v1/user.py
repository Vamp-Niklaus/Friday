from fastapi import APIRouter, Depends, HTTPException
import secrets
from datetime import datetime, timedelta, timezone

from app.api.deps import get_current_user
from app.database.repositories.user_settings_repository import UserSettingsRepository
from app.schemas.user import UserSettingsResponse, UpdateProfileRequest, TelegramVerifyRequest, TelegramVerifyConfirm
from app.services.telegram_service import TelegramService

router = APIRouter()

@router.get("/settings", response_model=UserSettingsResponse)
async def get_settings(user_id: str = Depends(get_current_user)):
    repo = UserSettingsRepository()
    settings = repo.get_or_create(user_id)
    return UserSettingsResponse(
        display_name=settings.get("display_name"),
        daily_quota=settings.get("daily_quota", 5),
        telegram_chat_id=settings.get("telegram_chat_id"),
        telegram_is_verified=settings.get("telegram_is_verified", False)
    )

@router.put("/settings/profile", response_model=UserSettingsResponse)
async def update_profile(
    payload: UpdateProfileRequest,
    user_id: str = Depends(get_current_user)
):
    repo = UserSettingsRepository()
    settings = repo.update_profile(user_id, payload.display_name, payload.daily_quota)
    return UserSettingsResponse(
        display_name=settings.get("display_name"),
        daily_quota=settings.get("daily_quota", 5),
        telegram_chat_id=settings.get("telegram_chat_id"),
        telegram_is_verified=settings.get("telegram_is_verified", False)
    )

@router.post("/settings/telegram/verify_request")
async def request_telegram_verification(
    payload: TelegramVerifyRequest,
    user_id: str = Depends(get_current_user)
):
    repo = UserSettingsRepository()
    telegram_service = TelegramService()
    
    otp = str(secrets.randbelow(1000000)).zfill(6)
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    
    try:
        await telegram_service.send_message(
            f"Your Antigravity Verification Code is: {otp}\n\nThis code will expire in 10 minutes.", 
            chat_id=payload.telegram_chat_id
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400, 
            detail="Failed to send Telegram message. Please verify the Chat ID is correct and you have messaged the bot first."
        ) from exc
        
    repo.set_telegram_otp(user_id, payload.telegram_chat_id, otp, expires_at)
    return {"status": "success", "message": "Verification code sent via Telegram"}

@router.post("/settings/telegram/verify_confirm", response_model=UserSettingsResponse)
async def confirm_telegram_verification(
    payload: TelegramVerifyConfirm,
    user_id: str = Depends(get_current_user)
):
    repo = UserSettingsRepository()
    settings = repo.get_or_create(user_id)
    
    if not settings.get("telegram_otp"):
        raise HTTPException(status_code=400, detail="No verification requested.")
        
    expires_at = datetime.fromisoformat(settings["telegram_otp_expires_at"].replace("Z", "+00:00"))
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="Verification code has expired. Please request a new one.")
        
    if settings["telegram_otp"] != payload.otp:
        raise HTTPException(status_code=400, detail="Incorrect verification code.")
        
    updated = repo.confirm_telegram_verification(user_id)
    return UserSettingsResponse(
        display_name=updated.get("display_name"),
        daily_quota=updated.get("daily_quota", 5),
        telegram_chat_id=updated.get("telegram_chat_id"),
        telegram_is_verified=updated.get("telegram_is_verified", False)
    )

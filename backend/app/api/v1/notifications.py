import httpx
from fastapi import APIRouter, HTTPException

from app.schemas.notifications import TelegramTestRequest, TelegramTestResponse
from app.services.telegram_service import TelegramService
from app.scheduler.reminder_scheduler import ReminderScheduler


router = APIRouter()


@router.post("/telegram/test", response_model=TelegramTestResponse)
async def send_telegram_test(payload: TelegramTestRequest) -> dict:
    try:
        result = await TelegramService().send_message(payload.message)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Telegram request failed: {exc.response.text}",
        ) from exc

    return {"status": "sent", "telegram_response": result}


@router.post("/reminders/trigger")
async def trigger_reminders() -> dict:
    """Manually trigger a reminder cycle for testing."""
    scheduler = ReminderScheduler()
    await scheduler._send_reminders()
    return {"status": "ok", "message": "Reminder cycle executed"}

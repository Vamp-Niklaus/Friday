from fastapi import APIRouter
from app.services.reminders import run_reminder_cycle

router = APIRouter()

@router.get("/reminders")
async def trigger_reminders():
    """
    Public stateless endpoint to trigger the reminder cycle.
    Designed to be called by external cron services (e.g., cron-job.org) every 5 minutes.
    """
    # We pass window_minutes=5 so that if the cron hits at 5:05, 
    # it grabs tasks scheduled up to 5:10, guaranteeing tasks aren't missed or sent late.
    result = await run_reminder_cycle(window_minutes=5)
    return result

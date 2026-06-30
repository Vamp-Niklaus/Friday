from fastapi import APIRouter, BackgroundTasks
from app.services.reminders import run_reminder_cycle

router = APIRouter()

@router.api_route("/reminders", methods=["GET", "HEAD"])
async def trigger_reminders(background_tasks: BackgroundTasks):
    """
    Public stateless endpoint to trigger the reminder cycle.
    Designed to be called by external cron services (e.g., cron-job.org) every 5 minutes.
    """
    # Trigger the reminder cycle in the background so UptimeRobot gets an instant response
    background_tasks.add_task(run_reminder_cycle, window_minutes=5)
    return {"status": "ok", "message": "Reminder cycle triggered in background"}

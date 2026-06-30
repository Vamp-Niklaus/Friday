import asyncio
import logging
from datetime import datetime

from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.database.repositories.reminder_event_repository import ReminderEventRepository
from app.services.telegram_service import TelegramService

logger = logging.getLogger(__name__)


class ReminderScheduler:
    """Schedules reminder delivery for active tasks."""

    def __init__(self) -> None:
        self.tz = ZoneInfo(settings.app_timezone)
        self.scheduler = BackgroundScheduler()
        self.repo = ReminderEventRepository()
        self.telegram = TelegramService()

    def start(self) -> None:
        """Register cron jobs and start the scheduler."""
        self.scheduler.add_job(
            self._run_reminder_cycle,
            trigger=CronTrigger(minute="*"), # Run every single minute
            id="reminder_every_minute",
            replace_existing=True,
        )
        logger.info("Scheduled reminder job to run every minute")

        self.scheduler.start()
        logger.info("Reminder scheduler started")

    def shutdown(self) -> None:
        """Gracefully shut down the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Reminder scheduler shut down")

    def _run_reminder_cycle(self) -> None:
        """Fetch due tasks and send reminders. Runs in APScheduler thread."""
        asyncio.run(self._send_reminders())

    async def _send_reminders(self) -> None:
        """Core logic: find open tasks due right now, send Telegram reminders."""
        now = datetime.now(self.tz)
        current_time_str = now.isoformat()
        
        # We round down to the nearest minute so we don't send duplicates if it runs twice in a minute
        scheduled_for = now.replace(second=0, microsecond=0).isoformat()

        logger.info("Running reminder cycle at %s", scheduled_for)

        tasks = self.repo.get_open_tasks_due(current_time_str)
        logger.info("Found %d open tasks due for reminders", len(tasks))

        sent_count = 0
        skip_count = 0
        fail_count = 0

        for task in tasks:
            task_id = task["id"]

            if self.repo.was_already_sent(task_id, scheduled_for):
                skip_count += 1
                continue

            try:
                message = self.telegram.build_task_reminder_message(task)
                await self.telegram.send_message(message)
                self.repo.log_sent(task_id, scheduled_for, message)
                sent_count += 1
                logger.info("Sent reminder for task %s: %s", task_id, task["title"])
            except Exception:
                error_msg = f"Failed to send reminder for task {task_id}"
                logger.exception(error_msg)
                self.repo.log_failed(task_id, scheduled_for, error_msg)
                fail_count += 1

        logger.info(
            "Reminder cycle done: %d sent, %d skipped, %d failed",
            sent_count,
            skip_count,
            fail_count,
        )

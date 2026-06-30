import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.database.repositories.reminder_event_repository import ReminderEventRepository
from app.services.telegram_service import TelegramService

logger = logging.getLogger(__name__)


async def run_reminder_cycle(window_minutes: int = 5) -> dict:
    """
    Stateless core logic: find open tasks due now or in the near future, send Telegram reminders.
     window_minutes: Looks ahead this many minutes to catch tasks (useful for external cronjobs that run every X minutes).
    """
    tz = ZoneInfo(settings.app_timezone)
    now = datetime.now(tz)
    
    # --- NIGHT MODE SLEEP (00:01 to 05:59) ---
    if now.hour >= 0 and now.hour < 6:
        # If it's exactly 00:00 to 00:05, we do the Midnight digest
        if not (now.hour == 0 and now.minute <= 5):
            logger.info("Cron sleeping: night mode active (00:01 to 05:59).")
            return {
                "status": "sleeping",
                "sent_count": 0, "skip_count": 0, "fail_count": 0,
                "window_looked_ahead_minutes": 0
            }

    # --- MIDNIGHT 6-HOUR LOOKAHEAD ---
    is_midnight_digest = (now.hour == 0 and now.minute <= 5)
    if is_midnight_digest:
        window_minutes = 360  # 6 hours lookahead
    
    # Determine if current time is a "digest hour" AND early in the hour (<= 5 min)
    is_digest_time = is_midnight_digest or (now.hour in [9, 12, 15, 18, 21] and now.minute <= 5)
    
    # We look ahead by window_minutes
    future_window = now + timedelta(minutes=window_minutes)
    current_time_str = future_window.isoformat()
    
    # Optimization: If not a digest hour, only fetch tasks due within the last 15 minutes
    min_time_str = None
    if not is_digest_time:
        min_time_str = (now - timedelta(minutes=15)).isoformat()
    
    repo = ReminderEventRepository()
    telegram = TelegramService()
    
    # We need a client to fetch user settings
    from app.database.client import get_supabase_client
    db_client = get_supabase_client()

    logger.info("Running stateless reminder cycle looking up to %s", current_time_str)

    tasks = repo.get_open_tasks_due(current_time_str, min_time=min_time_str)
    logger.info("Found %d open tasks due for reminders in this window", len(tasks))

    # Group tasks by user
    from collections import defaultdict
    user_tasks = defaultdict(list)
    for task in tasks:
        user_tasks[task["user_id"]].append(task)

    sent_count = 0
    skip_count = 0
    fail_count = 0

    for user_id, tasks_for_user in user_tasks.items():
        settings_res = db_client.table("user_settings").select("telegram_chat_id, telegram_is_verified").eq("user_id", user_id).execute()
        if not settings_res.data or not settings_res.data[0].get("telegram_is_verified") or not settings_res.data[0].get("telegram_chat_id"):
            logger.info(f"Skipping user {user_id}: No verified telegram chat ID.")
            skip_count += len(tasks_for_user)
            continue
            
        user_chat_id = settings_res.data[0]["telegram_chat_id"]

        immediate = []
        past_due = []
        problems = []

        for task in tasks_for_user:
            todo_at = datetime.fromisoformat(task["todo_at"].replace("Z", "+00:00")).astimezone(tz)
            time_diff_minutes = (todo_at - now).total_seconds() / 60.0

            # Immediate: Due between 15 mins ago and 5 mins from now AND never sent
            if -15 <= time_diff_minutes <= 5 and not repo.was_already_sent(task["id"], task["todo_at"]):
                immediate.append(task)
            # Past Due: Older than 15 minutes, check throttle
            elif time_diff_minutes < -15:
                # We check the 2.5 hour throttle
                if not repo.has_been_sent_in_last_x_hours(task["id"], 2.5):
                    if task.get("item_type") == "problem":
                        problems.append(task)
                    else:
                        past_due.append(task)
                else:
                    skip_count += 1
            else:
                skip_count += 1

        # We only send a message if there's an immediate task, OR if it's a digest time and there's something to send
        if not immediate and not (is_digest_time and (past_due or problems)):
            # None of the past due tasks qualify right now
            skip_count += len(past_due) + len(problems)
            continue

        if not immediate and not past_due and not problems:
            continue

        try:
            message = telegram.build_grouped_reminder_message(immediate, past_due, problems)
            await telegram.send_message(message, chat_id=user_chat_id)
            
            # Log all sent tasks
            for t in immediate + past_due + problems:
                repo.log_sent(t["id"], t["todo_at"], message, user_id=user_id)
                sent_count += 1
                
            logger.info(f"Sent grouped reminder to user {user_id} with {len(immediate)} immediate, {len(past_due)} past due, {len(problems)} problems.")
        except Exception as e:
            error_msg = f"Failed to send grouped reminder for user {user_id}: {str(e)}"
            logger.exception(error_msg)
            for t in immediate + past_due + problems:
                repo.log_failed(t["id"], t["todo_at"], error_msg, user_id=user_id)
                fail_count += 1

    return {
        "status": "success",
        "sent_count": sent_count,
        "skip_count": skip_count,
        "fail_count": fail_count,
        "window_looked_ahead_minutes": window_minutes
    }

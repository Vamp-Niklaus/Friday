import asyncio
import httpx
from datetime import datetime, timedelta

from app.core.config import settings


class TelegramService:
    """Sends outbound reminder messages through Telegram."""

    def __init__(self) -> None:
        self.bot_token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id
        self.base_url = "https://api.telegram.org"

    async def send_message(self, text: str, chat_id: str = None) -> dict:
        if not self.bot_token:
            raise ValueError("Missing TELEGRAM_BOT_TOKEN.")

        target_chat_id = chat_id or self.chat_id
        if not target_chat_id:
            raise ValueError("Missing Telegram Chat ID. Pass one as an argument or set TELEGRAM_CHAT_ID in .env")

        async with httpx.AsyncClient(timeout=30) as client:
            for attempt in range(3):
                try:
                    response = await client.post(
                        f"{self.base_url}/bot{self.bot_token}/sendMessage",
                        json={
                            "chat_id": target_chat_id,
                            "text": text,
                            "disable_web_page_preview": True,
                        },
                    )
                    response.raise_for_status()
                    return response.json()
                except httpx.RequestError as exc:
                    if attempt == 2:
                        raise
                    print(f"Telegram network error: {exc}. Retrying...")
                    await asyncio.sleep(2)

    async def send_task_reminder(self, task: dict, chat_id: str = None) -> dict:
        return await self.send_message(self.build_task_reminder_message(task), chat_id=chat_id)

    def build_task_reminder_message(self, task: dict) -> str:
        return (
            f"Reminder: {task['title']}\n"
            f"Todo date: {task['todo_at']}\n"
            f"Created on: {task['created_at'][:10]}"
        )

    def build_grouped_reminder_message(self, immediate: list[dict], past_due: list[dict], problems: list[dict]) -> str:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(settings.app_timezone)

        def format_time(iso_str: str) -> str:
            dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00")).astimezone(tz)
            now = datetime.now(tz)
            if dt.date() == now.date():
                return dt.strftime("%I:%M %p")
            elif dt.date() == (now.date() - timedelta(days=1)):
                return "Yesterday"
            else:
                return dt.strftime("%b %d")

        lines = []

        if immediate:
            lines.append("🚨 IMMEDIATE:")
            for t in immediate:
                lines.append(f"- [{format_time(t['todo_at'])}] {t['title']}")
            lines.append("")

        if past_due:
            lines.append("⚠️ PAST DUE:")
            for t in past_due:
                lines.append(f"- [{format_time(t['todo_at'])}] {t['title']}")
            lines.append("")

        if problems:
            lines.append("🧠 TODAY'S PROBLEMS:")
            for t in problems:
                lines.append(f"- {t['title']}")
            lines.append("")

        return "\n".join(lines).strip()

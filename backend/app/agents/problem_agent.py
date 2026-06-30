from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.llm.base import LLMProvider


class ProblemAgent:
    """Extracts recurring problems (spaced repetition) from user messages."""

    def __init__(self, llm_provider: LLMProvider) -> None:
        self.llm_provider = llm_provider

    async def extract_problem(
        self,
        message: str,
        chat_history: list[dict] | None = None,
    ) -> dict:
        today = datetime.now(ZoneInfo(settings.app_timezone)).date()
        messages = [
            {
                "role": "system",
                "content": (
                    "Extract a recurring problem/topic for spaced repetition from the conversation. "
                    f"Today's date is {today.isoformat()} in {settings.app_timezone}. "
                    "Return only JSON with keys: has_problem, needs_follow_up, "
                    "follow_up_question, title. "
                    "has_problem is true when the user wants to add a topic to study, "
                    "or when the user is answering a recent assistant follow-up about a problem. "
                    "title must be a concise title of the topic or problem to revise. "
                    "If the intent exists but the actual problem/topic is unclear, "
                    "set needs_follow_up true and write a short follow_up_question."
                ),
            }
        ]
        messages.extend(chat_history or [])
        if not chat_history:
            messages.append({"role": "user", "content": message})

        extracted = await self.llm_provider.chat_json(messages)

        if extracted.get("needs_follow_up") or not extracted.get("has_problem"):
            return extracted

        # The ScheduleAnalyzer will determine the actual next_revision_date later
        # For now, we set a default flag so the repo knows it's a problem
        extracted["item_type"] = "problem"
        extracted["timezone"] = settings.app_timezone
        return extracted

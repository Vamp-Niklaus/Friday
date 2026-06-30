from app.database.client import get_supabase_client


class AgentRunRepository:
    """Persistence methods for agent routing and extraction runs."""

    def __init__(self) -> None:
        self.client = get_supabase_client()

    def create(
        self,
        chat_message_id: str,
        user_id: str,
        agent_name: str,
        llm_provider: str,
        llm_model: str,
        status: str,
        input_data: dict,
        output_data: dict,
        error: str | None = None,
    ) -> dict:
        result = (
            self.client.table("agent_runs")
            .insert(
                {
                    "user_id": user_id,
                    "chat_message_id": chat_message_id,
                    "agent_name": agent_name,
                    "llm_provider": llm_provider,
                    "llm_model": llm_model,
                    "status": status,
                    "input": input_data,
                    "output": output_data,
                    "error": error,
                }
            )
            .execute()
        )
        return result.data[0]

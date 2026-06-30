from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Doraemon"
    app_env: str = "development"
    app_timezone: str = "Asia/Kolkata"

    llm_provider: str = "openai"
    llm_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    openrouter_api_key: str = ""
    openrouter_model: str = ""

    supabase_url: str = ""
    supabase_service_role_key: str = ""

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    cors_allow_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

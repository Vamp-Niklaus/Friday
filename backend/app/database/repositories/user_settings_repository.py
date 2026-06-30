from datetime import date

from app.database.client import get_supabase_client


class UserSettingsRepository:
    def __init__(self) -> None:
        self.client = get_supabase_client()

    def get_or_create(self, user_id: str) -> dict:
        # Try to select
        result = (
            self.client.table("user_settings")
            .select("*")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0]

        # Create if missing
        insert_result = (
            self.client.table("user_settings")
            .insert({"user_id": user_id})
            .execute()
        )
        return insert_result.data[0]

    def update_quota(self, user_id: str, daily_quota: int) -> dict:
        # Backward compatibility for old method
        return self.update_profile(user_id, None, daily_quota)

    def update_profile(self, user_id: str, display_name: str | None, daily_quota: int) -> dict:
        data = {"user_id": user_id, "daily_quota": daily_quota}
        if display_name is not None:
            data["display_name"] = display_name
            
        result = (
            self.client.table("user_settings")
            .upsert(data, on_conflict="user_id")
            .select("*")
            .execute()
        )
        return result.data[0]

    def set_telegram_otp(self, user_id: str, telegram_chat_id: str, otp: str, expires_at: str) -> dict:
        result = (
            self.client.table("user_settings")
            .upsert({
                "user_id": user_id, 
                "telegram_chat_id": telegram_chat_id,
                "telegram_otp": otp,
                "telegram_otp_expires_at": expires_at,
                "telegram_is_verified": False
            }, on_conflict="user_id")
            .select("*")
            .execute()
        )
        return result.data[0]
        
    def confirm_telegram_verification(self, user_id: str) -> dict:
        result = (
            self.client.table("user_settings")
            .update({
                "telegram_is_verified": True,
                "telegram_otp": None,
                "telegram_otp_expires_at": None
            })
            .eq("user_id", user_id)
            .select("*")
            .execute()
        )
        if not result.data:
            return None
        return result.data[0]

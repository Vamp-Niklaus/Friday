import asyncio
import os
import sys

from app.database.repositories.user_settings_repository import UserSettingsRepository
from app.database.client import get_supabase_client
from dotenv import load_dotenv

load_dotenv()

async def test():
    repo = UserSettingsRepository()
    try:
        # find a valid user_id
        client = get_supabase_client()
        users = client.table("tasks").select("user_id").limit(1).execute()
        if not users.data:
            print("No users found")
            return
        
        user_id = users.data[0]["user_id"]
        print(f"Testing with user_id: {user_id}")
        
        settings = repo.get_or_create(user_id)
        print("Settings fetched:")
        print(settings)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())

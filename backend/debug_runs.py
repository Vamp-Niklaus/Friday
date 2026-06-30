import asyncio
import os
import sys

from app.database.client import get_supabase_client
from dotenv import load_dotenv

load_dotenv()

async def main():
    client = get_supabase_client()
    try:
        res = client.table('agent_runs').select('*').order('created_at', desc=True).limit(2).execute()
        for row in res.data:
            print(f"Agent: {row['agent_name']}")
            print(f"Status: {row['status']}")
            print(f"Input: {row.get('input')}")
            print(f"Output: {row.get('output')}")
            print("-" * 40)
    except Exception as e:
        print(f"Error querying DB: {e}")

if __name__ == "__main__":
    asyncio.run(main())

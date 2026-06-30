import asyncio
from app.agents.master_agent import MasterAgent
from app.agents.reminder_agent import ReminderAgent
from app.llm.openai_provider import get_llm_provider
from dotenv import load_dotenv

load_dotenv()

async def main():
    llm_provider = get_llm_provider()
    reminder_agent = ReminderAgent(llm_provider)
    
    msg1 = "schedule this problem https://leetcode.com/problems/two-sum/"
    msg2 = "remind me tomorrow to solve https://leetcode.com/problems/two-sum/"
    
    print("Extracting Msg 1...")
    try:
        master_agent = MasterAgent(llm_provider)
        route1 = await master_agent.route(msg1, [])
        print(route1)
        
        print("\nExtracting Msg 2...")
        route2 = await master_agent.route(msg2, [])
        print(route2)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

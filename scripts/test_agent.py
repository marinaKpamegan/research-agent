import asyncio
from app.agents.research_agent import ResearchAgent


async def main():
    agent = ResearchAgent()
    answer = await agent.handle_question("What is the capital of France?")
    print("Answer:", answer)


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
from app.agents.research_agent import ResearchAgent

async def test():
    agent = ResearchAgent()
    async for event in agent.graph.astream_events(
        {"question": "Quel est le taux de chomage à lyon", "selected_source": "datagouv"},
        version="v2"
    ):
        kind = event["event"]
        name = event["name"]
        print(f"Event: {kind} | Name: {name}")
        if kind == "on_tool_start":
            print("TOOL ARGS:", event["data"].get("input"))

asyncio.run(test())

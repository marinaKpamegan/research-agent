import asyncio
from app.agents.research_agent import ResearchAgent

async def test():
    agent = ResearchAgent()
    async for event in agent.graph.astream_events(
        {"question": "Qu'est ce que Python?", "selected_source": "arxiv"},
        version="v2"
    ):
        kind = event["event"]
        name = event["name"]
        if kind == "on_chat_model_stream":
            chunk = event["data"]["chunk"].content
            if chunk:
                print(f"Stream({name}): {repr(chunk)}")
        elif kind == "on_chat_model_end":
            print(f"End({name})")

asyncio.run(test())

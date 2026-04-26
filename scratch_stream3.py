import asyncio
from app.agents.research_agent import ResearchAgent

async def test():
    agent = ResearchAgent()
    async for event in agent.graph.astream_events(
        {"question": "What is Python?", "selected_source": "arxiv"},
        version="v2"
    ):
        kind = event["event"]
        name = event["name"]
        if kind == "on_chain_start" and name in ["route_query", "search_arxiv", "search_datagouv", "generate_answer"]:
            print(f"Workflow node started: {name}")
        elif kind == "on_tool_start":
            print(f"Tool started: {name}")
        elif kind == "on_chat_model_stream":
            chunk = event["data"]["chunk"].content
            if chunk:
                print(chunk, end="", flush=True)

asyncio.run(test())

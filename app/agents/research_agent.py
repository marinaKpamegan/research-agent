from typing import Any
from app.agents.tools import search, summarize
from app.memory.simple_memory import SimpleMemory


class ResearchAgent:
    def __init__(self):
        self.memory = SimpleMemory()

    async def handle_question(self, question: str) -> str:
        # Very small agent loop: search → summarize → store
        results = await search(question)
        summary = await summarize(results)
        self.memory.add({"question": question, "summary": summary})
        return summary

from fastapi import APIRouter
from app.schemas.query import Query
from app.agents.research_agent import ResearchAgent

router = APIRouter()
agent = ResearchAgent()

@router.post("/query")
async def post_query(payload: Query):
    """Accepts JSON {"question": "..."} and returns an answer."""
    answer = await agent.handle_question(payload.question)
    return {"question": payload.question, "answer": answer}

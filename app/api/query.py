from fastapi import APIRouter
from app.schemas.query import Query, ResearchResponse
from app.agents.research_agent import ResearchAgent

router = APIRouter()
agent = ResearchAgent()


@router.post(
    "/query",
    response_model=ResearchResponse,
    summary="Ask a research question",
    description="Provide a question (and optional context) and receive a short answer with source items.",
    tags=["query"],
)
async def post_query(payload: Query):
    """Accepts JSON with `question` and optional metadata and returns an answer with sources."""
    answer = await agent.handle_question(payload.question)
    # Return minimal ResearchResponse-compatible dict
    return {
        "answer": answer,
        "sources": [],
        "used_context": payload.area_of_interest,
    }

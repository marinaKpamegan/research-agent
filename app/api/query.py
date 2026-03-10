from fastapi import APIRouter, Depends
from app.schemas.query import Query, ResearchResponse
from app.schemas.user import User
from app.agents.research_agent import ResearchAgent
from app.api.deps import get_current_user

router = APIRouter()
agent = ResearchAgent()


@router.post(
    "/query",
    response_model=ResearchResponse,
    summary="Ask a research question",
    description="Provide a question (and optional context) and receive a short answer with source items.",
    tags=["query"],
)
async def post_query(payload: Query, current_user: User = Depends(get_current_user)):
    """Accepts JSON with `question` and optional metadata and returns an answer with sources."""
    answer = await agent.handle_question(payload.question)
    # Return minimal ResearchResponse-compatible dict
    return {
        "answer": answer,
        "sources": [],
        "used_context": payload.area_of_interest,
    }

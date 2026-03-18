from fastapi import APIRouter, Depends
from typing import List
from app.schemas.query import Query, ResearchResponse
from app.schemas.user import User
from app.api.deps import get_current_user, get_preference_repository, get_preferred_link_repository, get_research_agent
from app.db.repositories.preference import PreferenceRepository
from app.db.repositories.preferred_link import PreferredLinkRepository
from app.agents.research_agent import ResearchAgent

router = APIRouter()


@router.post(
    "/query",
    response_model=ResearchResponse,
    summary="Ask a research question",
    description="Provide a question (and optional context) and receive a short answer with source items.",
    tags=["query"],
)
async def post_query(
    payload: Query, 
    current_user: User = Depends(get_current_user),
    pref_repo: PreferenceRepository = Depends(get_preference_repository),
    link_repo: PreferredLinkRepository = Depends(get_preferred_link_repository),
    research_agent: ResearchAgent = Depends(get_research_agent)
):
    """Accepts JSON with `question` and optional metadata and returns an answer with sources."""
    # Get user preferences
    prefs = pref_repo.get_by_user_id(user_id=current_user.id)
    interests = prefs.interests if prefs and prefs.interests else []
    if isinstance(interests, str):
        interests = [i.strip() for i in interests.split(",") if i.strip()]
        
    # Get preferred links
    links = link_repo.get_user_preferred_links(user_id=current_user.id)
    preferred_urls = [link.url for link in links]

    # Handle question with personalization
    result = await research_agent.handle_question(
        question=payload.question,
        interests=interests,
        preferred_links=preferred_urls
    )
    
    # Determine the used context message
    used_context = f"Interests: {', '.join(interests)}" if interests else payload.area_of_interest
    
    # Generate metadata about results
    crawled = result.get('content', [])
    
    return {
        "answer": result.get("answer", "Erreur lors de la génération de la réponse."),
        "sources": [
            {"title": c.get("title", f"Source {i+1}"), "url": c["url"]} 
            for i, c in enumerate(crawled[:5])
        ],
        "used_context": used_context,
    }

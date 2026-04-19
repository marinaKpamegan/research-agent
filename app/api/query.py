from fastapi import APIRouter, Depends, BackgroundTasks

from typing import List
from app.schemas.query import Query, ResearchResponse
from app.schemas.user import User
from app.api.deps import get_current_user, get_preference_repository, get_preferred_link_repository, get_research_agent, get_feed_repository
from app.db.repositories.preference import PreferenceRepository
from app.db.repositories.preferred_link import PreferredLinkRepository
from app.db.repositories.feed import FeedRepository
from app.schemas.feed import FeedCreate
from app.agents.research_agent import ResearchAgent
from sse_starlette.sse import EventSourceResponse
import json

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


def save_history_task(feed_repo: FeedRepository, user_id: int, question: str, answer: str, contexts: list):
    try:
        from app.services.evaluation_service import EvaluationService
        evaluator = EvaluationService()
        
        scores = {}
        # Avoid evaluating if everything is empty or missing keys
        if len(answer.strip()) > 5:
            scores = evaluator.run_evaluation(question, answer, [c.get("text", c.get("url", "")) for c in contexts])
            
        feed = FeedCreate(
            title=question, 
            ai_summary=answer, 
            source_ids=[],
            ragas_faithfulness=scores.get("ragas_faithfulness"),
            ragas_answer_relevance=scores.get("ragas_answer_relevance")
        )
        feed_repo.create_feed(feed, user_id)
    except Exception as e:
        import logging
        logging.error(f"Failed to save history: {e}")

@router.post(
    "/query/stream",
    summary="Stream research query events",
    description="Streams Server-Sent Events (SSE) representing the execution steps of the agent.",
    tags=["query"],
)
async def post_query_stream(
    payload: Query, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    pref_repo: PreferenceRepository = Depends(get_preference_repository),
    feed_repo: FeedRepository = Depends(get_feed_repository),
    research_agent: ResearchAgent = Depends(get_research_agent)
):
    prefs = pref_repo.get_by_user_id(user_id=current_user.id)
    interests = prefs.interests if prefs and prefs.interests else []
    if isinstance(interests, str):
        interests = [i.strip() for i in interests.split(",") if i.strip()]

    async def event_generator():
        async for chunk in research_agent.stream_question(question=payload.question, interests=interests):
            parsed = json.loads(chunk)
            if parsed.get("step") == "complete":
                answer = parsed.get("data", {}).get("answer", "")
                contexts = parsed.get("data", {}).get("_raw_crawled", []) # We need to pass the raw contexts somehow...
                background_tasks.add_task(
                    save_history_task,
                    feed_repo=feed_repo,
                    user_id=current_user.id,
                    question=payload.question,
                    answer=answer,
                    contexts=contexts
                )
            yield {"event": "message", "data": chunk}
            
    return EventSourceResponse(event_generator())


@router.get(
    "/history",
    summary="Get user search history",
    description="Returns previous research queries and answers.",
    tags=["query"],
)
async def get_history(
    current_user: User = Depends(get_current_user),
    feed_repo: FeedRepository = Depends(get_feed_repository)
):
    feeds = feed_repo.get_user_feeds(current_user.id)
    feeds.sort(key=lambda x: x.date, reverse=True)
    return [
        {
            "id": f.id,
            "question": f.title,
            "answer": f.ai_summary,
            "date": f.date.isoformat() if f.date else None,
            "ragas_faithfulness": getattr(f, "ragas_faithfulness", None),
            "ragas_answer_relevance": getattr(f, "ragas_answer_relevance", None)
        }
        for f in feeds
    ]

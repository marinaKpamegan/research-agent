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
import asyncio

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


async def save_history_and_process_bg_tasks(feed_repo: FeedRepository, user_id: int, question: str, answer: str, contexts: list, bg_tasks: list):
    try:
        # from app.services.evaluation_service import EvaluationService
        # evaluator = EvaluationService()
        
        scores = {} # Evaluation disabled
            
        feed = FeedCreate(
            title=question, 
            ai_summary=answer, 
            source_ids=[],
            ragas_faithfulness=scores.get("ragas_faithfulness"),
            ragas_answer_relevance=scores.get("ragas_answer_relevance"),
            bm25_relevance=scores.get("bm25_relevance"),
            crawled_sources=json.dumps(contexts) if contexts else None
        )
        created_feed = feed_repo.create_feed(feed, user_id)
        
        if bg_tasks and created_feed and getattr(created_feed, "id", None):
            import logging
            from app.services.pdf_rag_service import PdfRagService
            from app.schemas.feed import FeedUpdate
            
            logger = logging.getLogger(__name__)
            pdf_service = PdfRagService()
            updated_summary = answer
            
            for task in bg_tasks:
                if task.get("type") == "pdf_visual":
                    pdf_url = task.get("url")
                    search_query = task.get("query")
                    try:
                        logger.info(f"Démarrage tâche de fond PDF pour {pdf_url}")
                        pdf_answer = await pdf_service.process_and_query_pdf(pdf_url, search_query)
                        updated_summary += f"\n\n---\n**Résultat Analyse Asynchrone PDF ({pdf_url}) :**\n{pdf_answer}"
                    except Exception as e:
                        logger.error(f"Erreur tâche asynchrone PDF: {e}")
                        
            if updated_summary != answer:
                feed_repo.update_feed(created_feed, FeedUpdate(ai_summary=updated_summary))
                logger.info(f"Historique {created_feed.id} mis à jour avec les résultats asynchrones.")
                
    except Exception as e:
        import logging
        logging.error(f"Failed to process history/bg_tasks: {e}")

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
                bg_tasks = parsed.get("data", {}).get("pending_backgroundtasks", [])
                
                # We use asyncio.create_task directly to detach from the HTTP lifecycle.
                # BackgroundTasks in Starlette prevents the TCP socket from closing until the task completes,
                # which causes the frontend UI to "spin" natively.
                asyncio.create_task(
                    save_history_and_process_bg_tasks(
                        feed_repo=feed_repo,
                        user_id=current_user.id,
                        question=payload.question,
                        answer=answer,
                        contexts=contexts,
                        bg_tasks=bg_tasks
                    )
                )
                # We don't want to send the huge raw content to the frontend
                del parsed["data"]["_raw_crawled"]
                chunk = json.dumps(parsed)
                
            yield {"event": "message", "data": chunk}
            await asyncio.sleep(0.01) # Force flush
            
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
    result = []
    for f in feeds:
        sources = []
        try:
            if getattr(f, "crawled_sources", None):
                sources = json.loads(f.crawled_sources)
        except Exception:
            pass
            
        result.append({
            "id": f.id,
            "question": f.title,
            "answer": f.ai_summary,
            "date": f.date.isoformat() if f.date else None,
            "ragas_faithfulness": getattr(f, "ragas_faithfulness", None),
            "ragas_answer_relevance": getattr(f, "ragas_answer_relevance", None),
            "bm25_relevance": getattr(f, "bm25_relevance", None),
            "sources": sources
        })
    return result

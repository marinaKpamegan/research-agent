import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.api.deps import get_current_user, get_preferred_link_repository, get_crawling_service, get_embedding_service, get_faiss_service
from app.db.repositories.preferred_link import PreferredLinkRepository
from app.services.crawling_service import CrawlingService
from app.services.embedding_service import EmbeddingService
from app.services.faiss_service import FaissService
from app.schemas.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/scrape-sources", response_model=Dict[str, Any])
async def scrape_user_sources(
    current_user: User = Depends(get_current_user),
    link_repo: PreferredLinkRepository = Depends(get_preferred_link_repository),
    crawler: CrawlingService = Depends(get_crawling_service),
    embed_service: EmbeddingService = Depends(get_embedding_service),
    faiss_service: FaissService = Depends(get_faiss_service)
):
    """
    Scrape toutes les sources (preferred links) de l'utilisateur,
    effectue un chunking de 1000 caractères et renvoie les résultats.
    """
    # 1. Récupérer les liens de l'utilisateur
    db_links = link_repo.get_user_preferred_links(user_id=current_user.id)
    if not db_links:
        return {"message": "Aucune source trouvée pour cet utilisateur", "chunks": []}
    
    urls = [link.url for link in db_links]
    
    # 2. Scraper les URLs
    scraped_data = await crawler.scrape_urls(urls=urls)
    
    # 3. Initialiser le splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=10,
        length_function=len,
        is_separator_regex=False,
    )
    
    # 4. Effectuer le chunking
    logger.info(f"Chunking {len(scraped_data)} sources")
    all_chunks = []
    for item in scraped_data:
        content = item.get("markdown", "")
        if not content:
            continue
            
        chunks = text_splitter.split_text(content)
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "source_url": item["url"],
                "source_title": item["title"],
                "chunk_index": i,
                "content": chunk,
            })
            
    # 5. Indexation dans FAISS
    if all_chunks:
        try:
            logger.info(f"Indexation de {len(all_chunks)} chunks dans FAISS")
            faiss_service.add_chunks(all_chunks)
        except Exception as e:
            logger.error(f"Erreur lors de l'indexation FAISS: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de l'indexation sémantique : {str(e)}"
            )
            
    return {
        "user_id": current_user.id,
        "sources_scraped": len(scraped_data),
        "total_chunks_indexed": len(all_chunks),
        "message": "Sources scannées, chunkées et indexées dans FAISS avec succès."
    }

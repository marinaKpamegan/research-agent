from fastapi import Depends, HTTPException, status, Request
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.db.repositories.user import UserRepository
from app.db.repositories.preference import PreferenceRepository
from app.db.repositories.feed import FeedRepository
from app.db.repositories.preferred_link import PreferredLinkRepository
from app.schemas.user import User
from app.services.crawling_service import CrawlingService
from app.services.embedding_service import EmbeddingService
from app.services.faiss_service import FaissService
from app.services.reranking_service import RerankingService
from app.agents.research_agent import ResearchAgent


# Global instances to avoid reloading the models every request
_embedding_service = None
_reranking_service = None

def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


def get_reranking_service() -> RerankingService:
    global _reranking_service
    if _reranking_service is None:
        _reranking_service = RerankingService()
    return _reranking_service


def get_faiss_service(
    embed_service: EmbeddingService = Depends(get_embedding_service)
) -> FaissService:
    return FaissService(embedding_service=embed_service)


def get_crawling_service() -> CrawlingService:
    return CrawlingService()


def get_research_agent(
    faiss: FaissService = Depends(get_faiss_service),
    reranker: RerankingService = Depends(get_reranking_service)
) -> ResearchAgent:
    return ResearchAgent(faiss_service=faiss, reranker=reranker)


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_preference_repository(db: Session = Depends(get_db)) -> PreferenceRepository:
    return PreferenceRepository(db)


def get_feed_repository(db: Session = Depends(get_db)) -> FeedRepository:
    return FeedRepository(db)


def get_preferred_link_repository(db: Session = Depends(get_db)) -> PreferredLinkRepository:
    return PreferredLinkRepository(db)


def get_current_user(
    request: Request,
    user_repo: UserRepository = Depends(get_user_repository),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Try fetching the token from cookies first
    token = request.cookies.get("access_token")
    if not token:
        # Fallback to Authorization header if you still need it to be API compatible
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise credentials_exception
        token = auth_header
 
    # Clean off "Bearer " if it's there
    if token.startswith("Bearer "):
        token = token.replace("Bearer ", "", 1)
        
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = user_repo.get_by_username(username=username)
    if user is None:
        raise credentials_exception
    return user

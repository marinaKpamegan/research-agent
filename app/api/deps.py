from fastapi import Depends, HTTPException, status, Request
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.db.repositories.user import UserRepository
from app.schemas.user import User


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


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

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas.user import UserCreate, User
from app.core.security import create_access_token
from app.core.config import settings
from app.api.deps import get_user_repository, get_current_user
from app.repositories.user import UserRepository

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(
    user: UserCreate, 
    response: Response,
    user_repo: UserRepository = Depends(get_user_repository)
):
    db_user = user_repo.get_by_username(username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    user_repo.create(user=user)
    
    access_token = create_access_token(data={"sub": user.username})
    
    # Set the HttpOnly cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        samesite="lax",
        secure=False, # Set to True in production with HTTPS
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    
    return {"message": "Successfully registered and logged in"}


@router.post("/login")
def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_repo: UserRepository = Depends(get_user_repository),
):
    user = user_repo.get_by_username(username=form_data.username)
    if not user or not user.verify_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    
    # Set the HttpOnly cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        samesite="lax",
        secure=False, # Set to True in production with HTTPS
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    
    return {"message": "Successfully logged in"}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax",
        secure=False # Match the flags used in set_cookie
    )
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=User)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current logged in user.
    Useful for the frontend to check if the user is authenticated 
    and retrieve their details since the token is stored in an HttpOnly cookie.
    """
    return current_user

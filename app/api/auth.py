from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas.user import UserCreate
from app.core.security import create_access_token
from app.api.deps import get_user_repository
from app.repositories.user import UserRepository

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(
    user: UserCreate, 
    user_repo: UserRepository = Depends(get_user_repository)
):
    db_user = user_repo.get_by_username(username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    return user_repo.create(user=user)


@router.post("/token")
def login_for_access_token(
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
    return {"access_token": access_token, "token_type": "bearer"}

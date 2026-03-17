from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.preference import Preference, PreferenceCreate, PreferenceUpdate
from app.db.session import get_db
from app.db.repositories.preference import (
    get_preferences,
    create_user_preferences,
    update_user_preferences,
)
from app.api.deps import get_current_user
from app.schemas.user import User

router = APIRouter()


@router.get("/", response_model=Preference)
def read_preferences(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    preferences = get_preferences(db, user_id=current_user.id)
    if not preferences:
        raise HTTPException(status_code=404, detail="Preferences not found")
    return preferences


@router.post("/", response_model=Preference)
def create_preferences(
    preferences: PreferenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_preferences = get_preferences(db, user_id=current_user.id)
    if db_preferences:
        raise HTTPException(
            status_code=400, detail="Preferences already exist for this user"
        )
    return create_user_preferences(
        db=db, preferences=preferences, user_id=current_user.id
    )


@router.put("/", response_model=Preference)
def update_preferences(
    preferences: PreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_preferences = get_preferences(db, user_id=current_user.id)
    if not db_preferences:
        raise HTTPException(status_code=404, detail="Preferences not found")
    return update_user_preferences(
        db=db, db_preferences=db_preferences, preferences=preferences
    )

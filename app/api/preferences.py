from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.preference import Preference, PreferenceCreate, PreferenceUpdate
from app.db.session import get_db
from app.api.deps import get_current_user, get_preference_repository
from app.db.repositories.preference import PreferenceRepository
from app.schemas.user import User

router = APIRouter()


@router.get("/", response_model=Preference)
def read_preferences(
    current_user: User = Depends(get_current_user),
    pref_repo: PreferenceRepository = Depends(get_preference_repository),
):
    preferences = pref_repo.get_by_user_id(user_id=current_user.id)
    if not preferences:
        raise HTTPException(status_code=404, detail="Preferences not found")
    return preferences


@router.post("/", response_model=Preference)
def create_preferences(
    preferences: PreferenceCreate,
    current_user: User = Depends(get_current_user),
    pref_repo: PreferenceRepository = Depends(get_preference_repository),
):
    db_preferences = pref_repo.get_by_user_id(user_id=current_user.id)
    if db_preferences:
        return pref_repo.update(
            db_preferences=db_preferences, preferences=preferences
        )
    return pref_repo.create(
        preferences=preferences, user_id=current_user.id
    )


@router.put("/", response_model=Preference)
def update_preferences(
    preferences: PreferenceUpdate,
    current_user: User = Depends(get_current_user),
    pref_repo: PreferenceRepository = Depends(get_preference_repository),
):
    db_preferences = pref_repo.get_by_user_id(user_id=current_user.id)
    if not db_preferences:
        raise HTTPException(status_code=404, detail="Preferences not found")
    return pref_repo.update(
        db_preferences=db_preferences, preferences=preferences
    )

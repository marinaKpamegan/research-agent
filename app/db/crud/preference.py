from sqlalchemy.orm import Session
from app.schemas.preference import PreferenceCreate, PreferenceUpdate
from app.db.models.preference import Preference


def get_preferences(db: Session, user_id: int):
    return db.query(Preference).filter(Preference.owner_id == user_id).first()


def create_user_preferences(
    db: Session, preferences: PreferenceCreate, user_id: int
):
    db_preferences = Preference(
        **preferences.dict(),
        owner_id=user_id,
        interests=",".join(preferences.interests),
        preferred_links=",".join(preferences.preferred_links)
    )
    db.add(db_preferences)
    db.commit()
    db.refresh(db_preferences)
    return db_preferences


def update_user_preferences(
    db: Session, db_preferences: Preference, preferences: PreferenceUpdate
):
    db_preferences.interests = ",".join(preferences.interests)
    db_preferences.preferred_links = ",".join(preferences.preferred_links)
    db.commit()
    db.refresh(db_preferences)
    return db_preferences

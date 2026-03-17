from sqlalchemy.orm import Session
from app.schemas.preference import PreferenceCreate, PreferenceUpdate
from app.db.models.preference import Preference


def get_preferences(db: Session, user_id: int):
    return db.query(Preference).filter(Preference.owner_id == user_id).first()


def create_user_preferences(
    db: Session, preferences: PreferenceCreate, user_id: int
):
    # Enlever les champs qu'on va passer explicitement en tant que strings
    pref_dict = preferences.dict(exclude={"interests", "preferred_links"})
    
    db_preferences = Preference(
        **pref_dict,
        owner_id=user_id,
        interests=",".join(preferences.interests) if preferences.interests else "",
        preferred_links=",".join(preferences.preferred_links) if preferences.preferred_links else ""
    )
    db.add(db_preferences)
    db.commit()
    db.refresh(db_preferences)
    return db_preferences


def update_user_preferences(
    db: Session, db_preferences: Preference, preferences: PreferenceUpdate
):
    db_preferences.interests = ",".join(preferences.interests) if preferences.interests else ""
    db_preferences.preferred_links = ",".join(preferences.preferred_links) if preferences.preferred_links else ""
    db.commit()
    db.refresh(db_preferences)
    return db_preferences

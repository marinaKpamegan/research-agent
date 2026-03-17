from sqlalchemy.orm import Session
from app.schemas.preference import PreferenceCreate, PreferenceUpdate
from app.db.models.preference import Preference


class PreferenceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: int) -> Preference | None:
        return self.db.query(Preference).filter(Preference.user_id == user_id).first()

    def create(self, preferences: PreferenceCreate, user_id: int) -> Preference:
        # Enlever les champs qu'on va passer explicitement en tant que strings
        pref_dict = preferences.dict(exclude={"interests"})
        
        db_preferences = Preference(
            **pref_dict,
            user_id=user_id,
            interests=",".join(preferences.interests) if preferences.interests else ""
        )
        self.db.add(db_preferences)
        self.db.commit()
        self.db.refresh(db_preferences)
        return db_preferences

    def update(self, db_preferences: Preference, preferences: PreferenceUpdate) -> Preference:
        db_preferences.interests = ",".join(preferences.interests) if preferences.interests else ""
        self.db.commit()
        self.db.refresh(db_preferences)
        return db_preferences

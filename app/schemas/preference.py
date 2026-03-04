from pydantic import BaseModel
from typing import List, Optional


class PreferenceBase(BaseModel):
    interests: Optional[List[str]] = []
    preferred_links: Optional[List[str]] = []


class PreferenceCreate(PreferenceBase):
    pass


class PreferenceUpdate(PreferenceBase):
    pass


class Preference(PreferenceBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True

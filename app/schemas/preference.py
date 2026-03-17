from pydantic import BaseModel, field_validator
from typing import List, Optional


class PreferenceBase(BaseModel):
    interests: Optional[List[str]] = []


class PreferenceCreate(PreferenceBase):
    pass


class PreferenceUpdate(PreferenceBase):
    pass


class Preference(PreferenceBase):
    id: int
    user_id: int

    @field_validator("interests", mode="before")
    @classmethod
    def split_interests(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    class Config:
        from_attributes = True

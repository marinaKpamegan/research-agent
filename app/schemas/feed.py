from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime
from app.schemas.preferred_link import PreferredLink

class FeedBase(BaseModel):
    title: str
    interests: Optional[List[str]] = None
    tag: Optional[str] = None
    ai_summary: Optional[str] = None
    ragas_faithfulness: Optional[float] = None
    ragas_answer_relevance: Optional[float] = None

class FeedCreate(FeedBase):
    source_ids: List[int]

class FeedUpdate(FeedBase):
    title: Optional[str] = None
    source_ids: Optional[List[int]] = None

class Feed(FeedBase):
    id: int
    date: datetime
    user_id: int
    sources: List[PreferredLink] = []

    @field_validator("interests", mode="before")
    @classmethod
    def split_interests(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    class Config:
        from_attributes = True

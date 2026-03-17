from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.schemas.preferred_link import PreferredLink

class FeedBase(BaseModel):
    title: str
    interests: Optional[List[str]] = None
    tag: Optional[str] = None
    ai_summary: Optional[str] = None

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

    class Config:
        from_attributes = True

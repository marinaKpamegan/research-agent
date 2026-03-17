from pydantic import BaseModel
from typing import Optional

class PreferredLinkBase(BaseModel):
    url: str
    name: Optional[str] = None
    is_trusted: bool = False  # ← Indicates if the source is from trusted_sources

class PreferredLinkCreate(PreferredLinkBase):
    pass

class PreferredLinkUpdate(PreferredLinkBase):
    url: Optional[str] = None
    name: Optional[str] = None

class PreferredLink(PreferredLinkBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
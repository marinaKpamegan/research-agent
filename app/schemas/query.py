from pydantic import BaseModel
from typing import List, Optional
from app.schemas.preferred_link import PreferredLink

class ResearchQuery(BaseModel):
    question: str
    area_of_interest: Optional[str] = None
    trusted_sources: Optional[List[str]] = None  # e.g., ["@karpathy", "https://huggingface.co/blog"]

class Source(BaseModel):
    title: str
    url: str

class ResearchResponse(BaseModel):
    answer: str
    sources: List[Source]
    used_context: Optional[str] = None  # e.g., "Focused on: Edge AI"

# Backwards-compatible alias expected by other modules
Query = ResearchQuery
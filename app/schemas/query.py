from c import BaseModel
from typing import List, Optional

class ResearchQuery(BaseModel):
    question: str
    area_of_interest: Optional[str] = None
    trusted_sources: Optional[List[str]] = None  # e.g., ["@karpathy", "https://huggingface.co/blog"]

class SourceItem(BaseModel):
    title: str
    url: str
    snippet: str
    is_trusted: bool = False  # ← NEW FIELD

class ResearchResponse(BaseModel):
    answer: str
    sources: List[SourceItem]
    used_context: Optional[str] = None  # e.g., "Focused on: Edge AI"
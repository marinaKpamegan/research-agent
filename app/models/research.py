import operator
from typing import TypedDict, List, Annotated, Dict, Any
from pydantic import BaseModel, Field

# --- Research Model ---
class ResearchResult(BaseModel):
    """
    Modèle représentant le résultat final d'une recherche.
    """
    question: str
    interests: List[str] = Field(default_factory=list)
    preferred_links: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    urls: List[str] = Field(default_factory=list)
    content: List[Dict[str, Any]] = Field(default_factory=list)
    answer: str = Field(default="")

# --- State Definition ---
class AgentState(TypedDict):
    """
    État du graphe pour l'agent de recherche.
    """
    question: str
    interests: List[str]
    preferred_links: List[str]
    keywords: List[str]
    urls: List[str]
    # Annotated with operator.add allows results from multiple nodes/iterations to accumulate
    crawled_content: Annotated[List[Dict[str, Any]], operator.add]
    pending_backgroundtasks: Annotated[List[Dict[str, Any]], operator.add]
    selected_source: str
    fallback_to: str
    answer: str

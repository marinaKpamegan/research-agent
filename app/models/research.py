import operator
from typing import TypedDict, List, Annotated, Dict, Any
from pydantic import BaseModel, Field

# --- Research Model ---
class ResearchResult(BaseModel):
    """
    Modèle représentant le résultat final d'une recherche.
    """
    question: str
    keywords: List[str] = Field(default_factory=list)
    urls: List[str] = Field(default_factory=list)
    content: List[Dict[str, Any]] = Field(default_factory=list)

# --- State Definition ---
class AgentState(TypedDict):
    """
    État du graphe pour l'agent de recherche.
    """
    question: str
    keywords: List[str]
    urls: List[str]
    # Annotated with operator.add allows results from multiple nodes/iterations to accumulate
    crawled_content: Annotated[List[Dict[str, Any]], operator.add]

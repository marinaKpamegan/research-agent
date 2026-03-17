from sentence_transformers import CrossEncoder
from langchain_core.documents import Document
from typing import List
import logging
import torch

logger = logging.getLogger(__name__)

class RerankingService:
    """
    Service pour ré-évaluer la pertinence des documents en utilisant un modèle Cross-Encoder.
    Contrairement aux Bi-Encoders (comme SigLIP), un Cross-Encoder prend (query, doc) en entrée
    et calcule un score de pertinence direct, ce qui est beaucoup plus précis mais plus lent.
    """
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        logger.info(f"Chargement du modèle Cross-Encoder ({model_name}) sur {self.device}")
        
        try:
            self.model = CrossEncoder(model_name, device=self.device)
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle Cross-Encoder: {e}")
            raise

    def rerank(self, query: str, documents: List[Document], k: int = 5) -> List[Document]:
        """
        Ré-ordonne une liste de documents selon leur pertinence par rapport à une requête.
        """
        if not documents:
            return []

        # Préparer les paires (query, document_content)
        pairs = [[query, doc.page_content] for doc in documents]
        
        try:
            # Calculer les scores de similarité
            scores = self.model.predict(pairs)
            
            # Attacher les scores aux documents pour le tri
            for doc, score in zip(documents, scores):
                doc.metadata["relevance_score"] = float(score)
            
            # Trier par score décroissant
            ranked_docs = sorted(documents, key=lambda x: x.metadata["relevance_score"], reverse=True)
            
            # Retourner les top-k documents
            return ranked_docs[:k]
            
        except Exception as e:
            logger.error(f"Erreur lors du reranking: {e}")
            # En cas d'erreur, on retourne au moins les documents originaux (non triés ou tronqués)
            return documents[:k]

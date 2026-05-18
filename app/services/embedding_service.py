from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings
import torch
from typing import List
import logging

logger = logging.getLogger(__name__)

class EmbeddingService(Embeddings):
    """
    Service pour générer des embeddings en utilisant un modèle optimisé pour le texte.
    Compatible avec LangChain.
    """
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        logger.info(f"Chargement du modèle d'embedding ({model_name}) sur {self.device}")
        
        try:
            self.embeddings_model = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={'device': self.device},
                encode_kwargs={'normalize_embeddings': True}
            )
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle d'embedding: {e}")
            raise

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of strings.
        """
        if not texts:
            return []

        logger.info(f"Génération d'embeddings pour {len(texts)} textes")
        try:
            embeddings = self.embeddings_model.embed_documents(texts)
            logger.info(f"Embeddings générés avec succès. Dimension: {len(embeddings[0]) if embeddings else 0}")
            return embeddings
        except Exception as e:
            logger.error(f"Erreur CRITIQUE lors de la génération des embeddings: {e}", exc_info=True)
            raise

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single string.
        """
        try:
            return self.embeddings_model.embed_query(text)
        except Exception as e:
            logger.error(f"Erreur lors de la génération de l'embedding pour la requête: {e}")
            raise ValueError("La génération d'embedding pour la requête a échoué.")

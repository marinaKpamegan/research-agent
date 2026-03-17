from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from typing import List, Dict, Any, Optional
import os
import logging

logger = logging.getLogger(__name__)

class FaissService:
    def __init__(self, embedding_service):
        self.embeddings = embedding_service
        self.index_path = "data/faiss_index"
        self.vectorstore = None
        self._load_or_create()

    def _load_or_create(self):
        """Charge l'index existant ou en crée un nouveau s'il n'existe pas."""
        if os.path.exists(self.index_path):
            try:
                self.vectorstore = FAISS.load_local(
                    self.index_path, 
                    self.embeddings, 
                    allow_dangerous_deserialization=True
                )
                logger.info(f"Index FAISS chargé depuis {self.index_path}")
            except Exception as e:
                logger.error(f"Erreur lors du chargement de l'index FAISS: {e}")
                self.vectorstore = None
        else:
            logger.info("Aucun index FAISS trouvé. Il sera créé lors du premier ajout.")

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Ajoute des chunks au vector store avec leurs métadonnées.
        """
        documents = []
        for chunk in chunks:
            doc = Document(
                page_content=chunk["content"],
                metadata={
                    "source_url": chunk["source_url"],
                    "source_title": chunk["source_title"],
                    **chunk.get("metadata", {})
                }
            )
            documents.append(doc)

        if not documents:
            return

        if self.vectorstore is None:
            self.vectorstore = FAISS.from_documents(documents, self.embeddings)
        else:
            self.vectorstore.add_documents(documents)
        
        self.save()
        logger.info(f"{len(documents)} documents ajoutés et indexés avec succès.")

    def search(self, query: str, k: int = 5, reranker: Any = None) -> List[Document]:
        """Effectue une recherche de similarité, avec reranking optionnel."""
        if self.vectorstore is None:
            logger.warning("Tentative de recherche sur un index vide.")
            return []
        
        # Si un reranker est fourni, on récupère plus de candidats initialement (ex: k * 4)
        initial_k = k * 4 if reranker else k
        docs = self.vectorstore.similarity_search(query, k=initial_k)
        
        if reranker and docs:
            logger.info(f"Reranking de {len(docs)} documents pour la requête: {query}")
            return reranker.rerank(query, docs, k=k)
        
        return docs[:k]

    def save(self):
        """Sauvegarde l'index localement."""
        if self.vectorstore:
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            self.vectorstore.save_local(self.index_path)
            logger.info(f"Index FAISS sauvegardé dans {self.index_path}")
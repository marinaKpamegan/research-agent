from langchain_core.embeddings import Embeddings
import torch
from typing import List
from transformers import AutoProcessor, SiglipModel
import logging

logger = logging.getLogger(__name__)

class EmbeddingService(Embeddings):
    """
    Service pour générer des embeddings en utilisant le modèle SigLIP.
    Compatible avec LangChain.
    """
    def __init__(self, model_name: str = "google/siglip-base-patch16-224"):
        self.device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        logger.info(f"Chargement du modèle SigLIP ({model_name}) sur {self.device}")
        
        try:
            self.processor = AutoProcessor.from_pretrained(model_name)
            self.model = SiglipModel.from_pretrained(model_name).to(self.device)
            self.model.eval()
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle SigLIP: {e}")
            raise

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of strings.
        """
        if not texts:
            return []

        logger.info(f"Génération d'embeddings pour {len(texts)} textes")
        try:
            with torch.no_grad():
                # SigLIP processor gère le padding et la troncature
                inputs = self.processor(
                    text=texts, 
                    padding="max_length", 
                    truncation=True, 
                    return_tensors="pt"
                )
                
                # Move all tensors in inputs to the device
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                # On utilise l'encodeur de texte du modèle SigLIP directement
                # On force return_dict=False pour obtenir un tuple, ou on gère l'objet de sortie
                outputs = self.model.get_text_features(**inputs)
                
                # Extraction du tenseur s'il s'agit d'un objet de sortie HuggingFace
                if hasattr(outputs, "pooler_output"):
                    text_outputs = outputs.pooler_output
                elif isinstance(outputs, (list, tuple)):
                    text_outputs = outputs[0]
                else:
                    text_outputs = outputs

                # Vérification finale que c'est bien un tenseur
                if not isinstance(text_outputs, torch.Tensor):
                    logger.error(f"Format de sortie inattendu pour SigLIP: {type(text_outputs)}")
                    raise ValueError(f"Le modèle a renvoyé un type inattendu: {type(text_outputs)}")
                
                # Normalisation des embeddings (L2)
                text_outputs = text_outputs / text_outputs.norm(p=2, dim=-1, keepdim=True)
                
                embeddings = text_outputs.cpu().tolist()
                logger.info(f"Embeddings générés avec succès. Dimension: {len(embeddings[0]) if embeddings else 0}")
                return embeddings
        except Exception as e:
            logger.error(f"Erreur CRITIQUE lors de la génération des embeddings: {e}", exc_info=True)
            raise  # On laisse l'exception remonter pour éviter des erreurs silencieuses en aval

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single string.
        """
        embeddings = self.embed_documents([text])
        if not embeddings:
            raise ValueError("La génération d'embedding pour la requête a échoué.")
        return embeddings[0]

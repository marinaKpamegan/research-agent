import os
import io
import requests
import tempfile
import base64
import logging
from typing import Dict, Any

from PIL import Image
import fitz

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from app.core.config import settings

logger = logging.getLogger(__name__)

class PdfRagService:
    def __init__(self):
        # Initialisation du LLM Multimodal Gemini 1.5 Pro via OpenRouter
        self.llm = ChatOpenAI(
            model="openai/gpt-4o-mini",
            base_url=settings.OPENROUTER_API_URL,
            api_key=settings.OPENROUTER_API_KEY,
            temperature=0.0,
            max_tokens=2000
        )
        self.MAX_PAGES = 30 # Pour éviter de dépasser la charge utile d'images en une seule fois.

    async def process_and_query_pdf(self, pdf_url: str, query: str) -> str:
        """
        Télécharge le fichier PDF, le convertit en images (Base64), 
        et envoie le tout au LLM Multimodal (Gemini 1.5 Pro) pour une lecture directe visuelle.
        """
        logger.info(f"Downloading and processing PDF visually from URL: {pdf_url}")
        
        # 1. Télécharger le PDF dans un fichier temporaire
        try:
            response = requests.get(pdf_url, stream=True, timeout=15)
            response.raise_for_status()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name
                
        except Exception as e:
            logger.error(f"Failed to download PDF {pdf_url}: {e}")
            return f"Erreur de téléchargement du PDF : {e}"

        # 2. Lire le PDF, convertir en images Base64 via PyMuPDF
        try:
            pdf_document = fitz.open(tmp_path)
            num_pages = len(pdf_document)
            
            if num_pages == 0:
                return "Le document PDF semble vide."
                
            pages_to_process = min(num_pages, self.MAX_PAGES)
            logger.info(f"Processing {pages_to_process}/{num_pages} pages visually via LLM.")
            
            content_blocks = [
                {"type": "text", "text": f"Instruction: Tu dois extraire la réponse à la question suivante en te basant sur les pages de ce PDF (fourni ci-dessous en images).\nQuestion : '{query}'"}
            ]
            
            for page_num in range(pages_to_process):
                page = pdf_document.load_page(page_num)
                # dpi=100 suffit au LLM pour lire le texte, limite le poids base64
                pix = page.get_pixmap(dpi=150)
                
                # Convertir PyMuPDF pixmap en PIL Image
                mode = "RGBA" if pix.alpha else "RGB"
                img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
                
                # Sauvegarder en JPEG format binaire et base64
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG", quality=85)
                img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                
                # Ajouter au bloc de message multimodal
                content_blocks.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_str}"}
                    }
                )
                
            pdf_document.close()
            os.remove(tmp_path)
            
            if len(content_blocks) <= 1:
                return "Impossible de créer les images depuis le PDF."
                
            # 3. Invoquer le LLM Multimodal
            logger.info("Sending multi-modal payload to OpenRouter LLM...")
            human_msg = HumanMessage(content=content_blocks)
            response = await self.llm.ainvoke([human_msg])
            
            return f"Réponse tirée du PDF via analyse de Gemini :\n{response.content}"
            
        except Exception as e:
            logger.error(f"Failed to process PDF visually {pdf_url}: {e}")
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            return f"Erreur de traitement LLM du PDF : {e}"

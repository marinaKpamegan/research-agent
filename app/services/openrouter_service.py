from typing import List, Dict, Optional, Any, AsyncIterator
from app.core.config import settings
import logging
logger = logging.getLogger(__name__)
from langchain_openrouter import ChatOpenRouter
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage

class OpenRouterService:
    """Service pour gérer les interactions avec OpenRouter via LangChain"""
    
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_API_URL
        self.default_model = settings.DEFAULT_AI_MODEL
        self.chat_model = ChatOpenRouter(
            model=self.default_model,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=0.8,
            max_tokens=1000, # Default limit to avoid credit issues
            streaming=True
        )

    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[BaseMessage]:
        """Convertit les dictionnaires de messages en objets LangChain"""
        lc_messages = []
        for m in messages:
            role = m.get("role")
            content = m.get("content", "")
            if role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "system":
                lc_messages.append(SystemMessage(content=content))
            else:
                # On pourrait ajouter AIMessage etc. mais ici on reste simple
                lc_messages.append(HumanMessage(content=content))
        return lc_messages

    async def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.8,
        max_tokens: Optional[int] = None,
        purpose: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Crée une completion de chat via OpenRouter en utilisant LangChain.
        """
        effective_model = model or self.default_model
        
        logger.info(f"Création chat completion - model: {effective_model}, purpose: {purpose}, nb_messages: {len(messages)}")
        
        # On utilise une instance locale si le modèle ou la température change
        llm = self.chat_model
        if model or temperature != 0.8 or max_tokens:
            llm = ChatOpenRouter(
                model=effective_model,
                api_key=self.api_key,
                base_url=self.base_url,
                temperature=temperature,
                max_tokens=max_tokens or 1000, # Reasonable default to avoid credit issues
                streaming=True
            )

        try:
            lc_messages = self._convert_messages(messages)
            response = await llm.ainvoke(lc_messages)
            
            # Formatage pour rester compatible avec le code existant qui attendait une réponse brute API
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": response.content
                        }
                    }
                ],
                "usage": {
                    "total_tokens": 0 # LangChain n'expose pas toujours les tokens de la même façon selon le provider
                }
            }
                
        except Exception as e:
            logger.error(f"Erreur OpenRouter (LangChain): {str(e)}", exc_info=True)
            raise
    
    async def stream_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """
        Crée une completion de chat en streaming.
        """
        effective_model = model or self.default_model
        logger.info(f"Streaming chat completion - model: {effective_model}")
        
        llm = self.chat_model
        if model or temperature != 0.7:
            llm = ChatOpenRouter(
                model=effective_model,
                api_key=self.api_key,
                base_url=self.base_url,
                temperature=temperature,
                max_tokens=1000, # Reasonable default
                streaming=True
            )
        
        try:
            lc_messages = self._convert_messages(messages)
            async for chunk in llm.astream(lc_messages):
                yield chunk.content
                            
        except Exception as e:
            logger.error(f"Erreur streaming OpenRouter (LangChain): {str(e)}", exc_info=True)
            raise
    
    def extract_response_content(self, response: Dict) -> str:
        """
        Extrait le contenu de la réponse.
        """
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return ""
    
    def get_tokens_used(self, response: Dict) -> int:
        """
        Récupère le nombre de tokens utilisés.
        """
        return response.get("usage", {}).get("total_tokens", 0)

from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from ragas.metrics import faithfulness, answer_relevancy
from ragas import evaluate
from datasets import Dataset
import os
import logging
from app.core.config import settings
from rank_bm25 import BM25Okapi

class EvaluationService:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_API_URL
        self.chat_model = ChatOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            model="openai/gpt-4o-mini",
            temperature=0.8,
            max_tokens=1000 # Reasonable default
        )
        
        # answer_relevancy requires embeddings. Using a lightweight free, local model!
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )

    def run_evaluation(self, question: str, answer: str, contexts: list[str]) -> dict:
        try:
            if not contexts:
                contexts = ["No external context found."]
                
            data = {
                "question": [question],
                "answer": [answer],
                "contexts": [contexts]
            }
            dataset = Dataset.from_dict(data)
            
            result = evaluate(
                dataset,
                metrics=[faithfulness, answer_relevancy],
                llm=self.chat_model,
                embeddings=self.embeddings,
                raise_exceptions=False
            )
            
            final_scores = {
                "ragas_faithfulness": result.get("faithfulness", None),
                "ragas_answer_relevance": result.get("answer_relevancy", None)
            }
            
            try:
                if contexts and contexts[0] != "No external context found.":
                    tokenized_query = question.lower().split()
                    tokenized_contexts = [doc.lower().split() for doc in contexts]
                    
                    bm25 = BM25Okapi(tokenized_contexts)
                    scores = bm25.get_scores(tokenized_query)
                    
                    max_score = max(scores) if len(scores) > 0 else 0.0
                    norm_bm25 = min(max_score * 1.5, 10.0)
                    
                    final_scores["bm25_relevance"] = norm_bm25
            except Exception as e:
                logging.error(f"BM25 evaluation failed: {e}")

            return final_scores
        except Exception as e:
            logging.error(f"RAGAs evaluation failed: {e}")
            return {}

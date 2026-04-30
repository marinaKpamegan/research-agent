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
    _chat_model = None
    _embeddings = None

    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_API_URL
        
        if EvaluationService._chat_model is None:
            EvaluationService._chat_model = ChatOpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
                model="openai/gpt-4o-mini",
                temperature=0.8,
                max_tokens=1000
            )
            
        if EvaluationService._embeddings is None:
            # answer_relevancy requires embeddings. Using a lightweight free, local model!
            EvaluationService._embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2"
            )
        
        self.chat_model = EvaluationService._chat_model
        self.embeddings = EvaluationService._embeddings

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
            
            final_scores = {}
            if hasattr(result, "to_pandas"):
                # Convertir EvaluationResult en dict via Pandas pour Ragas récent
                df = result.to_pandas()
                if not df.empty:
                    final_scores["ragas_faithfulness"] = df["faithfulness"].iloc[0] if "faithfulness" in df.columns else None
                    final_scores["ragas_answer_relevance"] = df["answer_relevancy"].iloc[0] if "answer_relevancy" in df.columns else None
            else:
                final_scores["ragas_faithfulness"] = result["faithfulness"] if "faithfulness" in result else None
                final_scores["ragas_answer_relevance"] = result["answer_relevancy"] if "answer_relevancy" in result else None
            
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

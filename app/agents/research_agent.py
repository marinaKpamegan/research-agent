import logging
from typing import List, Dict, Any
from langgraph.graph import StateGraph, START, END
from duckduckgo_search import DDGS
from app.services.openrouter_service import OpenRouterService
from app.services.crawling_service import CrawlingService
from app.memory.simple_memory import SimpleMemory
from app.models.research import AgentState

logger = logging.getLogger(__name__)

class ResearchAgent:
    def __init__(self, faiss_service=None, reranker=None):
        self.memory = SimpleMemory()
        self.openrouter = OpenRouterService()
        self.crawler_service = CrawlingService()
        self.faiss_service = faiss_service
        self.reranker = reranker
        self.graph = self._create_research_graph()

    def _create_research_graph(self):
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("generate_keywords", self._generate_keywords)
        workflow.add_node("search_local", self._search_local)
        workflow.add_node("search_web", self._search_web)
        workflow.add_node("crawl_sources", self._crawl_sources)
        
        # Define edges
        workflow.add_edge(START, "generate_keywords")
        workflow.add_edge("generate_keywords", "search_local")
        workflow.add_edge("search_local", "search_web")
        workflow.add_edge("search_web", "crawl_sources")
        workflow.add_edge("crawl_sources", END)
        
        return workflow.compile()

    # --- Nodes ---

    async def _search_local(self, state: AgentState) -> Dict[str, Any]:
        """Node: Search in FAISS index and rerank results."""
        if not self.faiss_service:
            return {"crawled_content": []}
            
        question = state["question"]
        logger.info(f"Searching local FAISS index for: {question}")
        
        # Search with reranking (k=5 by default in search method)
        docs = self.faiss_service.search(question, k=5, reranker=self.reranker)
        
        local_content = []
        for doc in docs:
            local_content.append({
                "url": doc.metadata.get("source_url", "Local Source"),
                "title": doc.metadata.get("source_title", "Local Document"),
                "content": doc.page_content,
                "score": doc.metadata.get("relevance_score", 0.0)
            })
            
        logger.info(f"Found {len(local_content)} relevant local chunks")
        return {"crawled_content": local_content}

    async def _generate_keywords(self, state: AgentState) -> Dict[str, Any]:
        """Node: Generate 3-5 keywords from the question."""
        question = state["question"]
        interests = state.get("interests", [])
        
        logger.info(f"Generating keywords for: {question} with interests: {interests}")
        
        interests_str = f"User interests: {', '.join(interests)}\n" if interests else ""
        prompt = f"""Generate 3 to 5 optimized search keywords for the following research question:
{interests_str}Question: {question}

Return ONLY the keywords as a comma-separated list, without any other text or explanation."""
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.openrouter.create_chat_completion(messages)
        content = self.openrouter.extract_response_content(response)
        
        keywords = [k.strip() for k in content.split(",") if k.strip()]
        logger.info(f"Generated keywords: {keywords}")
        
        return {"keywords": keywords}

    async def _search_web(self, state: AgentState) -> Dict[str, Any]:
        """Node: Search the web for URLs using keywords."""
        keywords = state["keywords"]
        preferred_links = state.get("preferred_links", [])
        
        logger.info(f"Searching web for keywords: {keywords}. Preferred links: {preferred_links}")
        
        urls = []
        # Add preferred links first if they match keywords (simple prioritization)
        # For now, let's just add them as candidates
        urls.extend(preferred_links)
        
        try:
            with DDGS() as ddgs:
                query = " ".join(keywords)
                results = ddgs.text(query, max_results=5)
                for r in results:
                    if r["href"] not in urls:
                        urls.append(r["href"])
        except Exception as e:
            logger.error(f"Search failed: {e}")
        
        logger.info(f"Combined URLs: {urls}")
        return {"urls": urls}

    async def _crawl_sources(self, state: AgentState) -> Dict[str, Any]:
        """Node: Crawl each URL and extract text."""
        urls = state["urls"]
        keywords = state["keywords"]
        existing_content = state.get("crawled_content", [])
        
        logger.info(f"Crawling sources: {urls}")
        
        new_content = existing_content.copy()
        # Limit crawling to top 3 to keep it fast if we already have local content
        limit = 3 if existing_content else 5
        
        for url in urls[:limit]:
            # Skip if already in content (e.g. from preferred links that were also in FAISS)
            if any(c["url"] == url for c in existing_content):
                continue
                
            try:
                results = await self.crawler_service.crawl_with_keywords(
                    start_url=url, 
                    keywords=keywords, 
                    max_depth=0, 
                    max_pages=1
                )
                
                for res in results:
                    new_content.append({
                        "url": res["url"],
                        "title": res.get("title", url),
                        "content": res["markdown"],
                        "score": res["score"]
                    })
            except Exception as e:
                logger.error(f"Failed to crawl {url}: {e}")
                continue
                
        return {"crawled_content": new_content}

    async def handle_question(self, question: str, interests: List[str] = None, preferred_links: List[str] = None) -> Dict[str, Any]:
        """Main entry point: Run the LangGraph workflow and return a structured result."""
        initial_state = {
            "question": question,
            "interests": interests or [],
            "preferred_links": preferred_links or [],
            "keywords": [],
            "urls": [],
            "crawled_content": []
        }
        
        # Execute the graph
        final_state = await self.graph.ainvoke(initial_state)
        
        # Create a structured result
        from app.models.research import ResearchResult
        result = ResearchResult(
            question=question,
            interests=final_state["interests"],
            preferred_links=final_state["preferred_links"],
            keywords=final_state["keywords"],
            urls=final_state["urls"],
            content=final_state["crawled_content"]
        )
        
        # Store in memory
        self.memory.add(result.dict())
        
        return result.dict()

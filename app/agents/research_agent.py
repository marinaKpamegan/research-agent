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
    def __init__(self):
        self.memory = SimpleMemory()
        self.openrouter = OpenRouterService()
        self.crawler_service = CrawlingService()
        self.graph = self._create_research_graph()

    def _create_research_graph(self):
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("generate_keywords", self._generate_keywords)
        workflow.add_node("search_web", self._search_web)
        workflow.add_node("crawl_sources", self._crawl_sources)
        
        # Define edges
        workflow.add_edge(START, "generate_keywords")
        workflow.add_edge("generate_keywords", "search_web")
        workflow.add_edge("search_web", "crawl_sources")
        workflow.add_edge("crawl_sources", END)
        
        return workflow.compile()

    # --- Nodes ---

    async def _generate_keywords(self, state: AgentState) -> Dict[str, Any]:
        """Node: Generate 3-5 keywords from the question."""
        question = state["question"]
        logger.info(f"Generating keywords for: {question}")
        
        prompt = f"""Generate 3 to 5 optimized search keywords for the following research question:
Question: {question}

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
        logger.info(f"Searching web for keywords: {keywords}")
        
        urls = []
        try:
            with DDGS() as ddgs:
                query = " ".join(keywords)
                results = ddgs.text(query, max_results=5)
                for r in results:
                    urls.append(r["href"])
        except Exception as e:
            logger.error(f"Search failed: {e}")
        
        logger.info(f"Found URLs: {urls}")
        return {"urls": urls}

    async def _crawl_sources(self, state: AgentState) -> Dict[str, Any]:
        """Node: Crawl each URL and extract text."""
        urls = state["urls"]
        keywords = state["keywords"]
        logger.info(f"Crawling sources: {urls}")
        
        new_content = []
        for url in urls:
            try:
                # We use the existing logic from CrawlingService
                results = await self.crawler_service.crawl_with_keywords(
                    start_url=url, 
                    keywords=keywords, 
                    max_depth=0, 
                    max_pages=1
                )
                
                for res in results:
                    new_content.append({
                        "url": res["url"],
                        "content": res["markdown"],
                        "score": res["score"]
                    })
            except Exception as e:
                logger.error(f"Failed to crawl {url}: {e}")
                continue
                
        return {"crawled_content": new_content}

    async def handle_question(self, question: str) -> Dict[str, Any]:
        """Main entry point: Run the LangGraph workflow and return a structured result."""
        initial_state = {
            "question": question,
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
            keywords=final_state["keywords"],
            urls=final_state["urls"],
            content=final_state["crawled_content"]
        )
        
        # Store in memory
        self.memory.add(result.dict())
        
        return result.dict()

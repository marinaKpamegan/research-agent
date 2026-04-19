import logging
import arxiv
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ArxivService:
    def __init__(self):
        self.client = arxiv.Client(page_size=10, delay_seconds=5.0, num_retries=3)

    def search_papers(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for scientific papers on arXiv based on the query.
        Returns a list of dictionaries with metadata and abstract.
        """
        logger.info(f"Searching ArXiv for: {query}")
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )

        results = []
        try:
            for result in self.client.results(search):
                results.append({
                    "id": result.entry_id,
                    "title": result.title,
                    "summary": result.summary,
                    "authors": [author.name for author in result.authors],
                    "published": result.published.isoformat() if result.published else None,
                    "pdf_url": result.pdf_url
                })
        except Exception as e:
            logger.error(f"Error fetching from ArXiv: {e}")

        logger.info(f"Found {len(results)} ArXiv papers.")
        return results

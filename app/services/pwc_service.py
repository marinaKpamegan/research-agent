import logging
import httpx
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class PwcService:
    def __init__(self):
        self.base_url = "https://paperswithcode.com/api/v1"

    async def search_papers(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Recherche des articles sur Papers With Code via l'API REST v1.
        Retourne les papiers pertinents avec leurs informations GitHub.
        """
        papers = []
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/papers/",
                    params={"q": query, "items_per_page": max_results},
                    timeout=10.0
                )
                resp.raise_for_status()
                data = resp.json()
                
                results = data.get("results", [])
                for item in results:
                    paper_id = item.get("id", "")
                    title = item.get("title", "No Title")
                    abstract = item.get("abstract", "")
                    pdf_url = item.get("pdf_url", "")
                    repository_url = ""
                    
                    # On PWC, "url_abs" or the paper "id" can be used to query its repo,
                    # but /papers/ response sometimes includes it or we can fetch repositories
                    # Pour rester simple et rapide, appelons l'endpoint de repositories
                    try:
                        repo_resp = await client.get(
                            f"{self.base_url}/papers/{paper_id}/repositories/",
                            timeout=5.0
                        )
                        if repo_resp.status_code == 200:
                            repos = repo_resp.json().get("results", [])
                            if repos:
                                # Trier par étoiles (les plus populaires d'abord)
                                repos = sorted(repos, key=lambda x: x.get("stars", 0), reverse=True)
                                best_repo = repos[0]
                                repository_url = best_repo.get("url", "")
                    except Exception as e:
                        logger.warning(f"Impossible de récupérer les repos PWC pour {paper_id}: {e}")
                        
                    content_str = f"Abstract: {abstract}"
                    if repository_url:
                        content_str += f"\nGitHub Repository: {repository_url}"
                        
                    papers.append({
                        "url": pdf_url or f"https://paperswithcode.com/paper/{paper_id}",
                        "title": f"[PapersWithCode] {title}",
                        "content": content_str,
                        "score": 1.0
                    })
        except Exception as e:
            logger.error(f"Erreur lors de la recherche Papers With Code pour '{query}': {e}")
            
        return papers

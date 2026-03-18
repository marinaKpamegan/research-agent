import asyncio
import logging
from typing import List, Optional
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DefaultMarkdownGenerator
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy

logger = logging.getLogger(__name__)

class CrawlingService:
    """Service pour effectuer des crawls profonds basés sur la pertinence des mots-clés."""

    async def crawl_with_keywords(
        self, 
        start_url: str, 
        keywords: List[str], 
        max_depth: int = 20, 
        max_pages: int = 100
    ) -> List[dict]:
        """
        Explore un site web en profondeur en priorisant les pages contenant les mots-clés spécifiés.
        
        Args:
            start_url: URL de départ.
            keywords: Liste de mots-clés pour le scoring.
            max_depth: Profondeur maximale de l'exploration.
            max_pages: Nombre maximum de pages à crawler.
            
        Returns:
            Liste de dictionnaires contenant l'URL, le titre, le score et le contenu markdown.
        """
        logger.info(f"Démarrage du deep crawl sur {start_url} avec les mots-clés: {keywords}")

        # Configurer le scorer par mots-clés
        keyword_scorer = KeywordRelevanceScorer(
            keywords=keywords,
            weight=1.0  # Importance maximale pour les mots-clés fournis
        )

        # Configurer la stratégie de crawl (Meilleur d'abord)
        strategy = BestFirstCrawlingStrategy(
            max_depth=max_depth,
            url_scorer=keyword_scorer,
            max_pages=max_pages,
            include_external=False  # Rester sur le même domaine par défaut
        )

        # Configurer l'exécution du crawler
        run_config = CrawlerRunConfig(
            deep_crawl_strategy=strategy,
            scraping_strategy=LXMLWebScrapingStrategy(),
            markdown_generator=DefaultMarkdownGenerator(options={"ignore_links": True}),
            exclude_external_links=True,
            exclude_social_media_links=True,
            stream=True,  # Utiliser le streaming pour plus de réactivité
            cache_mode="BYPASS"  # Forcer un nouveau crawl
        )

        results = []
        try:
            async with AsyncWebCrawler() as crawler:
                # arun renvoie un générateur asynchrone quand stream=True
                async for result in await crawler.arun(url=start_url, config=run_config):
                    if result.success:
                        score = result.metadata.get("score", 0)
                        logger.info(f"Page crawlée: {result.url} (Score: {score:.2f})")
                        results.append({
                            "url": result.url,
                            "title": result.metadata.get("title", ""),
                            "score": score,
                            "markdown": result.markdown
                        })
                    else:
                        logger.warning(f"Échec du crawl pour {result.url}: {result.error_message}")
        
        except Exception as e:
            logger.error(f"Erreur lors du deep crawl: {str(e)}", exc_info=True)
            raise

        logger.info(f"Deep crawl terminé. {len(results)} pages récupérées.")
        return results

    async def scrape_urls(self, urls: List[str]) -> List[dict]:
        """
        Effectue un scraping simple (non récursif) pour une liste d'URLs.
        
        Args:
            urls: Liste des URLs à scraper.
            
        Returns:
            Liste de dictionnaires contenant l'URL et le contenu markdown.
        """
        logger.info(f"Démarrage du scraping simple pour {len(urls)} URLs")
        
        results = []

        """
        3. References & Citations
        - If you enable link citations in your DefaultMarkdownGenerator (options={"citations": True}), you’ll see markdown_with_citations plus a references_markdown block. This helps large language models or academic-like referencing. 4. Links & Media
        - links["internal"] and links["external"] group discovered anchors by domain.
        - media["images"] / ["videos"] / ["audios"] store extracted media elements with optional scoring or context. 5. Error Cases
        - If success=False, check error_message (e.g., timeouts, invalid URLs).
        - status_code might be None if we failed before an HTTP response. Use CrawlResult to glean all final outputs and feed them into your data pipelines, AI models, or archives. With the synergy of a properly configured BrowserConfig and CrawlerRunConfig, the crawler can produce robust, structured results here in CrawlResult.
        
        """
        
        # Configurer l'exécution du crawler pour exclure les liens
        run_config = CrawlerRunConfig(
            markdown_generator=DefaultMarkdownGenerator(options={"citations": True}),
            exclude_external_links=True,
            exclude_social_media_links=True,
            # exclude_domains=["youtube.com", "twitter.com", "facebook.com", "instagram.com", "linkedin.com"],
            cache_mode="BYPASS"
        )

        try:
            async with AsyncWebCrawler() as crawler:
                # On utilise arun_many pour plus d'efficacité
                crawl_results = await crawler.arun_many(urls=urls, config=run_config)
                
                for result in crawl_results:
                    if result.success:
                        results.append({
                            "url": result.url,
                            "title": result.metadata.get("title", ""),
                            "markdown": result.markdown
                        })
                    else:
                        logger.warning(f"Échec du scraping pour {result.url}: {result.error_message}")
        
        except Exception as e:
            logger.error(f"Erreur lors du scraping groupé: {str(e)}", exc_info=True)
            raise

        logger.info(f"Scraping terminé. {len(results)} pages récupérées.")
        return results

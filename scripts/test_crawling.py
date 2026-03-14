import asyncio
import sys
import os

# Add project root to sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from app.services.crawling_service import CrawlingService

async def test_deep_crawl():
    print("--- Testing CrawlingService.crawl_with_keywords ---")
    service = CrawlingService()
    
    # Test on a smaller target to avoid excessive wait
    url = "https://en.wikipedia.org/wiki/Artificial_intelligence"
    keywords = ["neural", "network", "deep", "learning"]
    
    try:
        results = await service.crawl_with_keywords(
            url, 
            keywords, 
            max_depth=1, # Depth 1 for fast test
            max_pages=5
        )
        
        print(f"\nTotal pages crawled: {len(results)}")
        for r in results:
            print(f"URL: {r['url']}")
            print(f"Score: {r['score']:.2f}")
            print(f"Title: {r['title']}")
            print("-" * 20)
            
        if len(results) > 0:
            print("\nSuccess! Results obtained.")
        else:
            print("\nVerification failed: No results returned.")
            
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    # Configure logging to see what's happening
    import logging
    logging.basicConfig(level=logging.INFO)
    
    asyncio.run(test_deep_crawl())

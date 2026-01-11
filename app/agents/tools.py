from typing import List, Dict
import httpx
from bs4 import BeautifulSoup


async def search(query: str) -> List[Dict[str, str]]:
    # Stub search that performs a single HTTP GET if query looks like a URL,
    # otherwise returns a fake result list.
    if query.startswith("http://") or query.startswith("https://"):
        async with httpx.AsyncClient() as client:
            r = await client.get(query, timeout=10.0)
            return [{"url": query, "text": r.text}]
    return [{"url": "https://example.com", "text": f"Results for {query}"}]


async def scrape(url: str) -> str:
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=10.0)
        soup = BeautifulSoup(r.text, "html.parser")
        return soup.get_text(separator=" ")[:5000]


async def summarize(results: List[Dict[str, str]]) -> str:
    # Very small summarizer: take first result's text and truncate.
    if not results:
        return "No results found."
    text = results[0].get("text", "")
    return (text[:400] + "...") if len(text) > 400 else text

from typing import List, Dict
import httpx
from bs4 import BeautifulSoup
import urllib.parse
import re
import arxiv


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


async def search_arxiv(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Query arXiv using the `arxiv` package and return a list of results with title, summary and url.

    Note: `arxiv` is synchronous; run it in a thread to avoid blocking the event loop.
    """
    try:
        import asyncio
        loop = asyncio.get_running_loop()

        def _sync_search():
            search = arxiv.Search(query=query, max_results=max_results)
            res = []
            for r in search.results():
                res.append({
                    'title': r.title,
                    'summary': r.summary,
                    'url': r.entry_id,
                })
            return res

        results = await loop.run_in_executor(None, _sync_search)
        return results
    except Exception:
        return []


async def search_hackernews(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search Hacker News via the public Algolia API and return top hits."""
    url = "https://hn.algolia.com/api/v1/search"
    params = {"query": query, "tags": "story", "hitsPerPage": max_results}
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url, params=params, timeout=10.0)
            r.raise_for_status()
            payload = r.json()
            hits = payload.get('hits', [])
            results = []
            for h in hits:
                results.append({
                    'title': h.get('title') or h.get('story_title') or '',
                    'url': h.get('url') or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                    'points': h.get('points', 0),
                    'author': h.get('author'),
                })
            return results
    except Exception:
        return []


async def search_youtube_metadata(query_or_url: str, max_results: int = 5) -> List[Dict[str, str]]:
    """If `query_or_url` looks like a YouTube URL, return oEmbed metadata.
    Otherwise perform a lightweight search by scraping the YouTube search results page and returning titles + watch urls.
    Note: for robust search results prefer the official YouTube Data API.
    """
    try:
        # If looks like a youtube url, try oembed
        if re.match(r'https?://(www\.)?(youtube\.com|youtu\.be)/', query_or_url):
            oembed = f"https://www.youtube.com/oembed?url={urllib.parse.quote_plus(query_or_url)}&format=json"
            async with httpx.AsyncClient() as client:
                r = await client.get(oembed, timeout=10.0)
                r.raise_for_status()
                data = r.json()
                return [{
                    'title': data.get('title'),
                    'author_name': data.get('author_name'),
                    'thumbnail_url': data.get('thumbnail_url'),
                    'url': query_or_url,
                }]

        # Otherwise, perform a simple HTML scrape of the search results
        search_url = 'https://www.youtube.com/results'
        params = {'search_query': query_or_url}
        async with httpx.AsyncClient() as client:
            r = await client.get(search_url, params=params, timeout=15.0)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, 'html.parser')
            results = []
            seen = set()
            # Find links to watch pages
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith('/watch') and 'v=' in href:
                    vid = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get('v')
                    vid = vid[0] if vid else None
                    if not vid:
                        # sometimes href is like /watch?v=...&list=...
                        m = re.search(r'v=([\w-]+)', href)
                        vid = m.group(1) if m else None
                    if not vid:
                        continue
                    url = f'https://www.youtube.com/watch?v={vid}'
                    if url in seen:
                        continue
                    seen.add(url)
                    title = a.get('title') or a.text.strip()
                    if not title:
                        # fallback: look for nearby text
                        title = a.text.strip()
                    results.append({'title': title, 'url': url})
                    if len(results) >= max_results:
                        break
            return results
    except Exception:
        return []

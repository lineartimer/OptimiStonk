import httpx
from markdownify import markdownify
import os
import structlog


BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"


_logger = structlog.get_logger(__name__)


async def load_web_page(url: str) -> str:
    """
        Loads a web page.
    """

    client = httpx.AsyncClient(timeout=30)

    try:
        response = await client.get(url)
        response.raise_for_status()
    
    except Exception as e:
        _logger.error("Page load failed.", error=e)
    
    markdown_content = markdownify(response.text, heading_style="ATX")

    _logger.info("Web page loaded successfully.", url=url)
    return markdown_content


async def web_search(query: str) -> list:
    """
        Searches the web.
    """

    client = httpx.AsyncClient(timeout=10)

    try:
        response = await client.get(
            url=BRAVE_SEARCH_URL,
            params={
                "q": query
            },
            headers={
                "Accept": "application/json",
                "X-Subscription-Token": os.getenv("BRAVE_API_KEY")
            }
        )

        response.raise_for_status()
    
    except Exception as e:
        _logger.error("Web search failed.", error=str(e))

    payload = response.json()
    search_results = (payload.get("web") or {}).get("results", [])

    cleaned_result = []
    for search_result in search_results:
        cleaned_result.append({
            "title": search_result.get("title"),
            "description": search_result.get("description"),
            "page_age": search_result.get("page_age"),
            "language": search_result.get("language"),
            "category": "Main page",
            "url": search_result.get("url")
        })

        sub_results = search_result.get("cluster", [])
        for sub_result in sub_results:
            cleaned_result.append({
                "title": sub_result.get("title"),
                "description": sub_result.get("description"),
                "page_age": search_result.get("page_age"),
                "language": search_result.get("language"),
                "category": "Subpage",
                "url": sub_result.get("url")
            })

    _logger.info("Web search successful.", query=query)
    return cleaned_result

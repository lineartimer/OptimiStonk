import httpx
import os
import structlog

from backend.database.database import get_web_search, save_web_search


BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"


_logger = structlog.get_logger(__name__)


async def web_search(query: str) -> list:
    """
    Carries out a web search using Brave.

    Args:
        query: Search query.
    """

    stored_search = get_web_search(query)
    if stored_search:
        _logger.info(
            "Web search loaded from database.",
            query=query,
            result_count=len(stored_search.search_result)
        )

        return stored_search.search_result

    search_results = []

    try:
        async with httpx.AsyncClient(timeout=10) as client:
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

            payload = response.json()
            search_results = (payload.get("web") or {}).get("results", [])
    
    except Exception as e:
        _logger.error("Web search failed.", error=str(e))
        return []

    cleaned_result = []
    for search_result in search_results:
        cleaned_result.append({
            "title": search_result.get("title"),
            "description": search_result.get("description"),
            "publish_date": search_result.get("page_age"),
            "language": search_result.get("language"),
            "category": "Main page",
            "url": search_result.get("url")
        })

        sub_results = search_result.get("cluster", [])
        for sub_result in sub_results:
            cleaned_result.append({
                "title": sub_result.get("title"),
                "description": sub_result.get("description"),
                "publish_date": search_result.get("page_age"),
                "language": search_result.get("language"),
                "category": "Subpage",
                "url": sub_result.get("url")
            })

    save_web_search(query, cleaned_result)

    _logger.info(
        "Web search completed and saved.",
        query=query,
        result_count=len(cleaned_result)
    )

    return cleaned_result

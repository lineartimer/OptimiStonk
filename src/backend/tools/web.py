import httpx
from markdownify import markdownify
import structlog


BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"


_logger = structlog.get_logger(__name__)


async def load_web_page(url: str) -> str:
    """
        Loads a web page.

        Args:
            url: Url of the web page.
    """

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            response.raise_for_status()

            markdown_content = markdownify(response.text, heading_style="ATX")

        _logger.info("Web page loaded successfully.", url=url)
        return markdown_content
    
    except Exception as e:
        _logger.error("Page load failed.", error=e)
        return ""
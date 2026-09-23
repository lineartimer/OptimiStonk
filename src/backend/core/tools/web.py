import httpx
from markdownify import markdownify
import structlog

from backend.database.database import load_web_page, save_web_page


BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"


_logger = structlog.get_logger(__name__)


async def download_web_page(url: str) -> str:
    """
    Loads a web page.

    Args:
        url: Url of the web page.
    """

    stored_page = load_web_page(url)
    if stored_page:
        _logger.info("Web page loaded from database.", url=url)
        return stored_page.content

    response = {}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            response.raise_for_status()

            content = markdownify(response.text, heading_style="ATX")

        save_web_page(url, content)

        _logger.info("Web page downloaded and saved.", url=url)
        return content

    except httpx.ReadTimeout:
        _logger.error("Page load failed.", error="HTTP request has timed out.", url=url)

    except Exception as e:
        if response and response.status_code:
            _logger.error("Page load failed.", http_status=response.status_code, url=url)
        else:
            _logger.error("Page load failed.", error=str(e), url=url)
            
    return ""


async def download_file(url: str) -> str:
    """
    Downloads a file from the internet.

    Args:
        url: Url to the file.
    """
    
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()

    _logger.info("File downloaded.", url=url)
    return response.text

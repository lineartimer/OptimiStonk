import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from markdownify import markdownify
from playwright.async_api import BrowserContext, async_playwright
import structlog

from backend.database.database import load_web_page, save_web_page


_logger = structlog.get_logger(__name__)


_context: BrowserContext | None = None
_page_slots = asyncio.Semaphore(3)


_BLOCKED_TITLES = {
    "access denied",
    "just a moment",
    "verify you are human",
    "robot or human",
    "pardon our interruption"
}


@asynccontextmanager
async def web_session() -> AsyncIterator[None]:
    global _context, _page_slots

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()

        try:
            _context = await browser.new_context(locale="en-US")
            _context.set_default_navigation_timeout(30_000)
            _context.set_default_timeout(10_000)

            _page_slots = asyncio.Semaphore(3)

            yield
        
        finally:
            try:
                if _context is not None:
                    await _context.close()
            
            finally:
                _context = None
                await browser.close()


def _get_context() -> BrowserContext:
    if _context is None:
        raise RuntimeError("No active web_session.")
    
    return _context


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

    try:
        # Render a page in Chromium
        async with _page_slots:
            page = await _get_context().new_page()

            try:
                response = await page.goto(url, wait_until="domcontentloaded")
                if response is None or not response.ok:
                    _logger.error(
                        "Page load failed.",
                        url=url,
                        http_status=response.status if response else None
                    )

                    return ""

                # Wait for text rendered by JavaScript but not for ads and analytics
                await page.wait_for_function("""() => {
                    const content = document.querySelector('article, main, [role="main"]')
                        || document.body;
                    return content && content.innerText.trim().length > 0;
                }""")

                title = (await page.title()).lower().strip(" .!?")
                if title in _BLOCKED_TITLES:
                    _logger.error("Browser verification needed.", url=url)
                    return ""

                content = markdownify(
                    await page.locator("body").inner_html(),
                    heading_style="ATX"
                ).strip()
            
            finally:
                await page.close()

        if not content:
            _logger.error("No text on page.", url=url)
            return ""

        save_web_page(url, content)

        _logger.info("Web page downloaded and saved.", url=url)
        return content

    except Exception as e:
        _logger.error("Page load failed.", error=str(e), url=url)

    return ""


async def download_file(url: str) -> str:
    """
    Downloads a file from the internet.

    Args:
        url: Url to the file.
    """

    # No browser tab will be opened
    response = await _get_context().request.get(url, timeout=30_000)
    try:
        if not response.ok:
            raise RuntimeError(f"File download failed (HTTP {response.status}): {url}")
        
        content = await response.text()

    finally:
        await response.dispose()
    
    _logger.info("File downloaded.", url=url)
    return content

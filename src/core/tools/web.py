import httpx


async def load_web_page(url: str) -> str:
    """
        Loads and returns the textual content of a web page.
    """

    client = httpx.AsyncClient(timeout=10)
    response = await client.get(url)

    return response.content


async def web_search(query: str) -> str:
    """
        Searches the web and returns results relevant to the query.
    """

    return list()

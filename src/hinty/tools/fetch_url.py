import aiohttp
from loguru import logger


async def fetch_url_content(url: str) -> str:
    """
    Fetches the content of a web page given its URL.

    Args:
        url: The URL to fetch content from.

    Returns:
        The text content of the web page.

    Raises:
        aiohttp.ClientError: If there's an error fetching the URL.
    """
    logger.info(f"Fetching content from URL: {url}")
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            content = await response.text()
    logger.info(f"Successfully fetched content from URL: {url}")
    return content

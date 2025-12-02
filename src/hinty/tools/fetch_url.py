import asyncio
import aiohttp
import sys
from loguru import logger


async def tool_fetch_url(url: str) -> str:
    """Fetches the content of a web page given its URL."""
    logger.info(f"Fetching content from URL: {url}")
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            content = await response.text()
    logger.info(f"Successfully fetched content from URL: {url}")
    return content


async def main():
    if len(sys.argv) != 2:
        print("Usage: python fetch_url.py <url>")
        return
    url = sys.argv[1]
    content = await tool_fetch_url(url)
    print(content)


if __name__ == "__main__":
    asyncio.run(main())

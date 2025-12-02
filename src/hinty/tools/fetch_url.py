import aiohttp
from bs4 import BeautifulSoup
from loguru import logger


async def tool_fetch_url(url: str) -> str:
    """Fetches the content of a web page given its URL, extracting readable text."""
    logger.info(f"Fetching content from URL: {url}")
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            content = await response.text()
    # Parse HTML and extract readable text
    soup = BeautifulSoup(content, "html.parser")
    text = soup.get_text()
    # Normalize whitespace for better readability
    cleaned_text = " ".join(text.split())
    logger.info(f"Successfully fetched and processed content from URL: {url}")
    return cleaned_text


async def tool_fetch_github_readme(url: str) -> str:
    """Fetches the README content from a GitHub repository page."""
    if not url.startswith("https://github.com/"):
        raise ValueError("URL must be a GitHub repository URL")
    logger.info(f"Fetching README from GitHub URL: {url}")
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            content = await response.text()
    soup = BeautifulSoup(content, "html.parser")
    readme = soup.find("article", class_="markdown-body")
    if readme:
        text = readme.get_text()
        cleaned_text = " ".join(text.split())
        logger.info(f"Successfully fetched README from GitHub URL: {url}")
        return cleaned_text
    else:
        logger.warning(f"No README found in {url}")
        return ""

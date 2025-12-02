import aiohttp
from bs4 import BeautifulSoup
from loguru import logger
import re


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
    """Fetches the raw README.md content from a GitHub repository."""
    if not url.startswith("https://github.com/"):
        raise ValueError("URL must be a GitHub repository URL")
    # Extract user and repo from URL
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)", url)
    if not match:
        raise ValueError("Invalid GitHub repository URL format")
    user, repo = match.groups()
    # Try main branch first, then master
    raw_urls = [
        f"https://raw.githubusercontent.com/{user}/{repo}/main/README.md",
        f"https://raw.githubusercontent.com/{user}/{repo}/master/README.md",
    ]
    for raw_url in raw_urls:
        logger.info(f"Attempting to fetch README from: {raw_url}")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(raw_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        logger.info(
                            f"Successfully fetched README from GitHub URL: {url}"
                        )
                        return content
                    elif response.status == 404:
                        continue  # Try next URL
                    else:
                        response.raise_for_status()
            except aiohttp.ClientError as e:
                logger.warning(f"Error fetching {raw_url}: {e}")
                continue
    logger.warning(f"No README.md found for repository: {url}")
    return ""

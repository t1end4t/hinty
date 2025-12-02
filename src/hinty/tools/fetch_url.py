import aiohttp
from bs4 import BeautifulSoup
from loguru import logger
import re
import base64


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
    """Fetches the raw README.md content from a GitHub repository using the GitHub API."""
    if not url.startswith("https://github.com/"):
        raise ValueError("URL must be a GitHub repository URL")
    # Extract user and repo from URL
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)", url)
    if not match:
        raise ValueError("Invalid GitHub repository URL format")
    user, repo = match.groups()
    api_url = f"https://api.github.com/repos/{user}/{repo}/readme"
    logger.info(f"Fetching README via GitHub API: {api_url}")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    # Decode base64 content
                    content = base64.b64decode(data['content']).decode('utf-8')
                    logger.info(f"Successfully fetched README from GitHub URL: {url}")
                    return content
                elif response.status == 404:
                    logger.warning(f"No README.md found for repository: {url}")
                    return ""
                else:
                    response.raise_for_status()
        except aiohttp.ClientError as e:
            logger.error(f"Error fetching README via API: {e}")
            return ""

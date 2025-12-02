import aiohttp
from bs4 import BeautifulSoup
from loguru import logger
import re


async def tool_fetch_url(url: str) -> str:
    """Fetches the content of a web page given its URL, extracting readable text."""
    if url.startswith("https://github.com/"):
        return await _fetch_github_readme(url)
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


async def _fetch_github_readme(url: str) -> str:
    """Fetches the raw README.md content (as Markdown) from a GitHub repository."""
    if not url.startswith("https://github.com/"):
        raise ValueError("URL must be a GitHub repository URL")

    # Extract user and repo from URL (handle trailing slashes and .git)
    match = re.match(
        r"https://github\.com/([^/]+)/([^/.]+)",
        url.rstrip("/").replace(".git", ""),
    )
    if not match:
        raise ValueError("Invalid GitHub repository URL format")

    user, repo = match.groups()
    api_url = f"https://api.github.com/repos/{user}/{repo}/readme"

    logger.info(f"Fetching README via GitHub API: {api_url}")

    # Add headers for better API experience
    headers = {
        "Accept": "application/vnd.github.v3.raw",  # This gets raw Markdown directly!
        "User-Agent": "Python-README-Fetcher",
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(api_url, headers=headers) as response:
                if response.status == 200:
                    # With the .raw accept header, we get Markdown directly
                    content = await response.text()
                    logger.info(
                        f"Successfully fetched README ({len(content)} chars) from: {url}"
                    )
                    return content
                elif response.status == 404:
                    logger.warning(f"No README found for repository: {url}")
                    return ""
                else:
                    error_text = await response.text()
                    logger.error(
                        f"GitHub API error {response.status}: {error_text}"
                    )
                    return ""
        except aiohttp.ClientError as e:
            logger.error(f"Error fetching README via API: {e}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error fetching README: {e}")
            return ""

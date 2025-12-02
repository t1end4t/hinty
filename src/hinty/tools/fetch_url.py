import aiohttp
from bs4 import BeautifulSoup
from loguru import logger
import re


def _is_github_url(url: str) -> bool:
    return url.startswith("https://github.com/")


def _parse_github_repo(url: str) -> tuple[str, str]:
    match = re.match(
        r"https://github\.com/([^/]+)/([^/.]+)",
        url.rstrip("/").replace(".git", ""),
    )
    if not match:
        raise ValueError("Invalid GitHub repository URL format")
    return match.groups()


def _build_github_api_url(user: str, repo: str) -> str:
    return f"https://api.github.com/repos/{user}/{repo}/readme"


async def _fetch_general_url(url: str) -> str:
    logger.info(f"Fetching content from URL: {url}")
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            content = await response.text()
    soup = BeautifulSoup(content, "html.parser")
    text = soup.get_text()
    cleaned_text = " ".join(text.split())
    logger.info(f"Successfully fetched and processed content from URL: {url}")
    return cleaned_text


async def _fetch_github_readme(url: str) -> str:
    user, repo = _parse_github_repo(url)
    api_url = _build_github_api_url(user, repo)
    logger.info(f"Fetching README via GitHub API: {api_url}")
    headers = {
        "Accept": "application/vnd.github.v3.raw",
        "User-Agent": "Python-README-Fetcher",
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(api_url, headers=headers) as response:
                if response.status == 200:
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


async def tool_fetch_url(url: str) -> str:
    if _is_github_url(url):
        return await _fetch_github_readme(url)
    return await _fetch_general_url(url)

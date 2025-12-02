import aiohttp
from bs4 import BeautifulSoup
from loguru import logger
import re


def _is_github_url(url: str) -> bool:
    return url.startswith("https://github.com/")


def _is_stackoverflow_url(url: str) -> bool:
    return url.startswith("https://stackoverflow.com/questions/")


def _is_reddit_url(url: str) -> bool:
    return url.startswith("https://www.reddit.com/r/") and "/comments/" in url


def _parse_reddit_ids(url: str) -> tuple[str, str]:
    match = re.match(
        r"https://www\.reddit\.com/r/([^/]+)/comments/([^/]+)/",
        url,
    )
    if not match:
        raise ValueError("Invalid Reddit post URL format")
    return match.group(1), match.group(2)


def _parse_stackoverflow_question_id(url: str) -> str:
    match = re.match(
        r"https://stackoverflow\.com/questions/(\d+)/",
        url,
    )
    if not match:
        raise ValueError("Invalid StackOverflow question URL format")
    return match.group(1)


def _parse_github_repo(url: str) -> tuple[str, str]:
    match = re.match(
        r"https://github\.com/([^/]+)/([^/.]+)",
        url.rstrip("/").replace(".git", ""),
    )
    if not match:
        raise ValueError("Invalid GitHub repository URL format")
    return (match.group(1), match.group(2))


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


async def _fetch_stackoverflow_question(url: str) -> str:
    question_id = _parse_stackoverflow_question_id(url)
    api_url = f"https://api.stackexchange.com/2.3/questions/{question_id}?site=stackoverflow&filter=withbody"
    logger.info(f"Fetching StackOverflow question via API: {api_url}")
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url) as response:
            response.raise_for_status()
            data = await response.json()
    if not data.get("items"):
        logger.warning(f"No question found for ID: {question_id}")
        return ""
    question = data["items"][0]
    title = question.get("title", "")
    body_html = question.get("body", "")
    body_text = BeautifulSoup(body_html, "html.parser").get_text()
    body_cleaned = " ".join(body_text.split())
    accepted_answer_id = question.get("accepted_answer_id")
    result = f"Title: {title}\n\nBody: {body_cleaned}"
    if accepted_answer_id:
        answer_api_url = f"https://api.stackexchange.com/2.3/answers/{accepted_answer_id}?site=stackoverflow&filter=withbody"
        logger.info(f"Fetching accepted answer via API: {answer_api_url}")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(answer_api_url) as response:
                    if response.status == 200:
                        answer_data = await response.json()
                        if answer_data.get("items"):
                            accepted_body_html = answer_data["items"][0].get(
                                "body", ""
                            )
                            accepted_body_text = BeautifulSoup(
                                accepted_body_html, "html.parser"
                            ).get_text()
                            accepted_cleaned = " ".join(
                                accepted_body_text.split()
                            )
                            result += f"\n\nAccepted Answer: {accepted_cleaned}"
                        else:
                            logger.warning(
                                f"No accepted answer found for ID: {accepted_answer_id}"
                            )
                    else:
                        logger.error(
                            f"Failed to fetch accepted answer: {response.status}"
                        )
            except aiohttp.ClientError as e:
                logger.error(f"Error fetching accepted answer: {e}")
            except Exception as e:
                logger.error(f"Unexpected error fetching accepted answer: {e}")
    logger.info(f"Successfully fetched StackOverflow question: {url}")
    return result


async def _fetch_reddit_post(url: str) -> str:
    subreddit, post_id = _parse_reddit_ids(url)
    api_url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}/.json"
    logger.info(f"Fetching Reddit post via API: {api_url}")
    headers = {"User-Agent": "Python-Reddit-Fetcher"}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(api_url) as response:
            response.raise_for_status()
            data = await response.json()
    if not data or len(data) < 2:
        logger.warning(f"No post or comments found for: {url}")
        return ""
    post_data = data[0]["data"]["children"][0]["data"]
    title = post_data.get("title", "")
    selftext = post_data.get("selftext", "")
    result = f"Title: {title}\n\nPost: {selftext}"
    comments_data = data[1]["data"]["children"]
    if comments_data:
        result += "\n\nComments:\n"

        def collect_comments(comments):
            bodies = []
            for comment in comments:
                if comment["kind"] == "t1":
                    body = comment["data"].get("body", "")
                    bodies.append(body)
                    replies = comment["data"].get("replies")
                    if replies and replies != "":
                        bodies.extend(
                            collect_comments(replies["data"]["children"])
                        )
            return bodies

        all_comments = collect_comments(comments_data)
        for i, comment in enumerate(all_comments, 1):
            result += f"\n{i}. {comment}\n"
    logger.info(f"Successfully fetched Reddit post: {url}")
    return result


async def tool_fetch_url(url: str) -> str:
    if _is_github_url(url):
        return await _fetch_github_readme(url)
    elif _is_stackoverflow_url(url):
        return await _fetch_stackoverflow_question(url)
    elif _is_reddit_url(url):
        return await _fetch_reddit_post(url)
    return await _fetch_general_url(url)

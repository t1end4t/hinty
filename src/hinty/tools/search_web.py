import asyncio
import os

from google import genai
from google.genai import types
from loguru import logger
from tavily import TavilyClient

from hinty.core.models import ToolResult


async def _search_with_google(query: str) -> ToolResult:
    """Perform web search using Google Gemini API."""
    logger.info(f"Starting Google Gemini web search for query: {query}")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error("GOOGLE_API_KEY environment variable not set")
        return ToolResult(
            success=False,
            error="GOOGLE_API_KEY environment variable is required for Gemini provider",
        )

    try:
        client = genai.Client(api_key=api_key)
        model = "gemini-flash-lite-latest"
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=query)],
            )
        ]
        tools = [
            types.Tool(google_search=types.GoogleSearch()),
        ]
        config = types.GenerateContentConfig(tools=tools)  # type: ignore
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=model,
            contents=contents,  # type: ignore
            config=config,
        )
        logger.info(
            f"Google Gemini web search completed successfully for query: {query}"
        )
        return ToolResult(success=True, output=response.text)
    except Exception as e:
        logger.error(
            f"Error during Google Gemini web search for query '{query}': {e}"
        )
        return ToolResult(success=False, error=str(e))


async def _search_with_tavily(query: str) -> ToolResult:
    """Perform web search using Tavily API."""
    logger.info(f"Starting Tavily web search for query: {query}")
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        logger.error("TAVILY_API_KEY environment variable not set")
        return ToolResult(
            success=False,
            error="TAVILY_API_KEY environment variable is required",
        )

    try:
        client = TavilyClient(api_key=api_key)
        response = await asyncio.to_thread(client.search, query=query)
        logger.info(
            f"Tavily web search completed successfully for query: {query}"
        )
        return ToolResult(success=True, output=response)
    except Exception as e:
        logger.error(f"Error during Tavily web search for query '{query}': {e}")
        return ToolResult(success=False, error=str(e))


async def tool_search_web(query: str) -> ToolResult:
    """Perform a web search using the configured provider."""
    provider = os.getenv("WEB_SEARCH_PROVIDER", "tavily").lower()
    logger.info(f"Dispatching web search for query: {query} using {provider}")

    if provider == "google":
        return await _search_with_google(query)
    else:
        return await _search_with_tavily(query)

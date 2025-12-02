import os
from typing import Dict, Any

from loguru import logger
from tavily import TavilyClient

from hinty.core.models import ToolResult


def tool_search_web(query: str) -> ToolResult:
    """Perform a web search using Tavily API."""
    logger.info(f"Starting web search for query: {query}")

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        logger.error("TAVILY_API_KEY environment variable not set")
        return ToolResult(
            success=False,
            error="TAVILY_API_KEY environment variable is required",
        )

    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(query=query)
        logger.info(f"Web search completed successfully for query: {query}")
        return ToolResult(success=True, output=response)
    except Exception as e:
        logger.error(f"Error during web search for query '{query}': {e}")
        return ToolResult(success=False, error=str(e))

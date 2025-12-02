import os
from typing import Dict, Any

from loguru import logger
from tavily import TavilyClient


def search_web_tool(query: str) -> Dict[str, Any]:
    """
    Perform a web search using Tavily API.

    Args:
        query: The search query string.

    Returns:
        A dictionary containing the search response.
    """
    logger.info(f"Starting web search for query: {query}")
    
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        logger.error("TAVILY_API_KEY environment variable not set")
        raise ValueError("TAVILY_API_KEY environment variable is required")
    
    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(query=query)
        logger.info(f"Web search completed successfully for query: {query}")
        return response
    except Exception as e:
        logger.error(f"Error during web search for query '{query}': {e}")
        raise

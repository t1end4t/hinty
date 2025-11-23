import re
from pathlib import Path

from loguru import logger


def tool_apply_search_replace(diff_content: str) -> None:
    """
    Apply a search/replace edit to a file based on the provided diff content.

    The diff_content should be in the format:
    file_path
    ```language
    <<<<<<< SEARCH
    [exact code to find]

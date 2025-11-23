import base64
import mimetypes
import re
from pathlib import Path
from typing import List, Tuple

from loguru import logger
from pypdf import PdfReader


def parse_search_replace_blocks(content: str) -> List[Tuple[str, str, str]]:
    """Parse search/replace blocks from content.

    Expects format: file_path\n```language\n<<<<<<< SEARCH\nold\n=======\nnew\n>>>>>>> REPLACE\n```

    Returns list of (filepath, search, replace) tuples.
    """
    logger.debug("Parsing search/replace blocks")
    blocks = []
    # Regex to match the block structure
    pattern = r"^([^\n]+)\n```[^\n]*\n<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE\n```"
    matches = re.findall(pattern, content, re.DOTALL | re.MULTILINE)
    for filepath, search, replace in matches:
        blocks.append((filepath.strip(), search.strip(), replace.strip()))
    logger.info(f"Parsed {len(blocks)} search/replace block(s)")
    return blocks


def apply_search_replace_to_file(
    filepath: Path, search: str, replace: str
) -> bool:
    """Apply a single search/replace to a file.

    Returns True if successful, False otherwise.
    """
    logger.info(f"Applying search/replace to {filepath}")
    try:
        if filepath.exists():
            content = filepath.read_text()
        else:
            logger.warning(f"File {filepath} does not exist, creating new")
            content = ""
        # Perform the replacement (only first match)
        new_content = content.replace(search, replace, 1)
        if new_content == content:
            logger.warning(f"No match found for search in {filepath}")
            return False
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(new_content)
        logger.info(f"Successfully applied search/replace to {filepath}")
        return True
    except Exception as e:
        logger.error(f"Failed to apply search/replace to {filepath}: {e}")
        return False


def tool_apply_search_replace(
    blocks_content: str, base_path: Path = Path.cwd()
) -> bool:
    """Apply search/replace blocks to files.

    Args:
        blocks_content: String containing search/replace blocks
        base_path: Base directory for resolving file paths

    Returns:
        True if all replacements applied successfully
    """
    logger.info("Starting search/replace application")
    file_changes = parse_search_replace_blocks(blocks_content)
    if not file_changes:
        logger.warning("No search/replace blocks found")
        return False
    success = True
    for filepath_str, search, replace in file_changes:
        filepath = base_path / filepath_str
        if not apply_search_replace_to_file(filepath, search, replace):
            success = False
    logger.info(
        f"Search/replace application {'successful' if success else 'failed'}"
    )
    return success


def tool_read_file(filepath: Path) -> str:
    """Read content from a file, handling different types like code, PDF, images, etc.

    For text-based files (e.g., code), returns the text content.
    For PDFs, extracts and returns text content.
    For images, returns base64-encoded data URI.
    For other files, attempts to read as text; falls back to a string representation of bytes if unsuccessful.

    Args:
        filepath: Path to the file to read.

    Returns:
        String representation of the file content.
    """
    if not filepath.exists():
        logger.error(f"File {filepath} does not exist")
        return ""

    mime_type, _ = mimetypes.guess_type(str(filepath))

    try:
        if mime_type and mime_type.startswith("text"):
            # Handle text files like code
            return filepath.read_text()
        elif mime_type == "application/pdf":
            # Handle PDF files by extracting text
            try:
                reader = PdfReader(filepath)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
            except ImportError:
                logger.error("pypdf library not available for PDF reading")
                return ""
        elif mime_type and mime_type.startswith("image"):
            # Handle images by base64 encoding
            with open(filepath, "rb") as f:
                data = f.read()
            encoded = base64.b64encode(data).decode("utf-8")
            return f"data:{mime_type};base64,{encoded}"
        else:
            # Attempt to read as text for other types
            try:
                return filepath.read_text()
            except UnicodeDecodeError:
                # Fall back to reading as bytes and representing as string
                with open(filepath, "rb") as f:
                    data = f.read()
                return f"<binary data: {len(data)} bytes>"
    except Exception as e:
        logger.error(f"Error reading file {filepath}: {e}")
        return ""

import base64
import mimetypes
from pathlib import Path

from loguru import logger


def read_content_file(filepath: Path) -> str:
    """Read content from a file, handling different types like code, PDF, images, etc.

    For text-based files (e.g., code), returns the text content.
    For PDFs, returns base64-encoded data URI.
    For images, returns base64-encoded data URI.
    For other files, attempts to read as text; falls back to a string representation of bytes if unsuccessful.

    Args:
        filepath: Path to the file to read.

    Returns:
        The content as a string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If there is an error reading the file or unsupported format.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File {filepath} does not exist")

    mime_type, _ = mimetypes.guess_type(str(filepath))

    try:
        if mime_type and mime_type.startswith("text"):
            # Handle text files like code
            content = filepath.read_text()
            return content
        elif mime_type == "application/pdf":
            # Handle PDF files by base64 encoding
            with open(filepath, "rb") as f:
                data = f.read()
            encoded = base64.b64encode(data).decode("utf-8")
            return f"data:{mime_type};base64,{encoded}"
        elif mime_type and mime_type.startswith("image"):
            # Handle images by base64 encoding
            with open(filepath, "rb") as f:
                data = f.read()
            encoded = base64.b64encode(data).decode("utf-8")
            return f"data:{mime_type};base64,{encoded}"
        else:
            # Attempt to read as text for other types
            try:
                content = filepath.read_text()
                return content
            except UnicodeDecodeError:
                # Fall back to reading as bytes and representing as string
                with open(filepath, "rb") as f:
                    data = f.read()
                return f"<binary data: {len(data)} bytes>"
    except Exception as e:
        logger.error(f"Error reading file {filepath}: {e}")
        raise ValueError(f"Error reading file {filepath}: {e}")

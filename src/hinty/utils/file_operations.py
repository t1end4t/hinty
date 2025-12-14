import base64
import mimetypes
from pathlib import Path
from typing import Tuple

from loguru import logger


def read_content_file(filepath: Path) -> Tuple[str, str]:
    """Read content from a file, handling different types like code, PDF, images, etc.

    For text-based files (e.g., code), returns the text content and type "text".
    For PDFs, returns base64-encoded data URI and type "pdf".
    For images, returns base64-encoded data URI and type "image".
    For other files, attempts to read as text and type "text"; falls back to a string representation of bytes and type "binary" if unsuccessful.

    Args:
        filepath: Path to the file to read.

    Returns:
        A tuple of (content as string, file_type as string).

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
            return content, "text"
        elif mime_type == "application/pdf":
            # Handle PDF files by base64 encoding
            with open(filepath, "rb") as f:
                data = f.read()
            encoded = base64.b64encode(data).decode("utf-8")
            return f"data:{mime_type};base64,{encoded}", "pdf"
        elif mime_type and mime_type.startswith("image"):
            # Handle images by base64 encoding
            with open(filepath, "rb") as f:
                data = f.read()
            encoded = base64.b64encode(data).decode("utf-8")
            return f"data:{mime_type};base64,{encoded}", "image"
        else:
            # Attempt to read as text for other types
            try:
                content = filepath.read_text()
                return content, "text"
            except UnicodeDecodeError:
                # Fall back to reading as bytes and representing as string
                with open(filepath, "rb") as f:
                    data = f.read()
                return f"<binary data: {len(data)} bytes>", "binary"
    except Exception as e:
        logger.error(f"Error reading file {filepath}: {e}")
        raise ValueError(f"Error reading file {filepath}: {e}")

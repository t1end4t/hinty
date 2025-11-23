import base64
import mimetypes
from pathlib import Path

from loguru import logger
from pypdf import PdfReader


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

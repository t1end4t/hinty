import base64
import mimetypes
from pathlib import Path
from typing import List, Tuple

from loguru import logger
from pypdf import PdfReader
from unidiff import Hunk, PatchSet


def parse_unified_diff(diff_content: str) -> List[Tuple[str, List[Hunk]]]:
    """Parse unified diff format into file changes using unidiff.

    Returns list of (filepath, hunks) tuples, where hunks are unidiff.Hunk objects.
    """
    logger.debug("Parsing unified diff content with unidiff")

    patch_set = PatchSet.from_string(diff_content)
    files = []

    for patch in patch_set:
        filepath = patch.target_file
        if filepath.startswith("b/"):
            filepath = filepath[2:]
        hunks = list(patch)
        files.append((filepath, hunks))

    logger.info(f"Parsed {len(files)} file(s) from diff")
    return files


def apply_hunk(original_lines: List[str], hunk: Hunk) -> List[str]:
    """Apply a single diff hunk to original content using unidiff.Hunk."""
    result = []
    orig_idx = 0

    # Add lines before this hunk
    while orig_idx < hunk.source_start:
        result.append(original_lines[orig_idx])
        orig_idx += 1

    for line in hunk:
        if line.is_removed:
            # Line removed - skip in original
            orig_idx += 1
        elif line.is_added:
            # Line added - add to result
            result.append(line.value)
        elif line.is_context:
            # Context line - verify and add
            if orig_idx < len(original_lines):
                result.append(original_lines[orig_idx])
                orig_idx += 1

    # Add remaining lines
    while orig_idx < len(original_lines):
        result.append(original_lines[orig_idx])
        orig_idx += 1

    return result


def apply_diff_to_file(filepath: Path, hunks: List[Hunk]) -> bool:
    """Apply diff to a single file.

    Returns True if successful, False otherwise.
    """
    logger.info(f"Applying diff to {filepath}")

    try:
        if filepath.exists():
            original_content = filepath.read_text()
            original_lines = original_content.split("\n")
        else:
            logger.warning(f"File {filepath} does not exist, creating new")
            original_lines = []

        # Apply all hunks sequentially
        for hunk in hunks:
            original_lines = apply_hunk(original_lines, hunk)

        modified_content = "\n".join(original_lines)

        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(modified_content)

        logger.info(f"Successfully applied diff to {filepath}")
        return True

    except Exception as e:
        logger.error(f"Failed to apply diff to {filepath}: {e}")
        return False


def tool_apply_diff(diff_content: str, base_path: Path = Path.cwd()) -> bool:
    """Apply unified diff to files.

    Args:
        diff_content: Unified diff format string
        base_path: Base directory for resolving file paths

    Returns:
        True if all diffs applied successfully
    """
    logger.info("Starting diff application")

    file_changes = parse_unified_diff(diff_content)

    if not file_changes:
        logger.warning("No file changes found in diff")
        return False

    success = True
    for filepath_str, hunks in file_changes:
        filepath = base_path / filepath_str
        if not apply_diff_to_file(filepath, hunks):
            success = False

    logger.info(f"Diff application {'successful' if success else 'failed'}")
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

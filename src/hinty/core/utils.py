import asyncio
import base64
import mimetypes
from collections import defaultdict
from pathlib import Path

import pathspec
from loguru import logger
from pypdf import PdfReader

from ..baml_client.types import CoderOutput
from ..core.models import ToolResult


def read_content_file(filepath: Path) -> ToolResult:
    """Read content from a file, handling different types like code, PDF, images, etc.

    For text-based files (e.g., code), returns the text content.
    For PDFs, extracts and returns text content.
    For images, returns base64-encoded data URI.
    For other files, attempts to read as text; falls back to a string representation of bytes if unsuccessful.

    Args:
        filepath: Path to the file to read.

    Returns:
        ToolResult with success status, output content, and error message if applicable.
    """
    if not filepath.exists():
        logger.error(f"File {filepath} does not exist")
        return ToolResult(
            success=False, error=f"File {filepath} does not exist"
        )

    mime_type, _ = mimetypes.guess_type(str(filepath))

    try:
        if mime_type and mime_type.startswith("text"):
            # Handle text files like code
            content = filepath.read_text()
            return ToolResult(success=True, output=content)
        elif mime_type == "application/pdf":
            # Handle PDF files by extracting text
            try:
                reader = PdfReader(filepath)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return ToolResult(success=True, output=text.strip())
            except ImportError:
                logger.error("pypdf library not available for PDF reading")
                return ToolResult(
                    success=False,
                    error="pypdf library not available for PDF reading",
                )
        elif mime_type and mime_type.startswith("image"):
            # Handle images by base64 encoding
            with open(filepath, "rb") as f:
                data = f.read()
            encoded = base64.b64encode(data).decode("utf-8")
            return ToolResult(
                success=True, output=f"data:{mime_type};base64,{encoded}"
            )
        else:
            # Attempt to read as text for other types
            try:
                content = filepath.read_text()
                return ToolResult(success=True, output=content)
            except UnicodeDecodeError:
                # Fall back to reading as bytes and representing as string
                with open(filepath, "rb") as f:
                    data = f.read()
                return ToolResult(
                    success=True, output=f"<binary data: {len(data)} bytes>"
                )
    except Exception as e:
        logger.error(f"Error reading file {filepath}: {e}")
        return ToolResult(
            success=False, error=f"Error reading file {filepath}: {e}"
        )


def apply_search_replace(
    coder_output: CoderOutput, base_path: Path
) -> ToolResult:
    """
    Applies search and replace operations based on structured coder output.

    Args:
        coder_output: Structured output containing files to change and their blocks.
        base_path: The base path for relative file paths.

    Returns:
        ToolResult: Result containing success status, applied changes, and any errors.
    """
    changes_by_file = defaultdict(list)
    for file_change in coder_output.files_to_change:
        file_path = file_change.file_path
        for block in file_change.blocks:
            changes_by_file[file_path].append((block.search, block.replace))

    if not changes_by_file:
        logger.warning("No search/replace blocks found in the coder output.")
        return ToolResult(
            success=False,
            error="No search/replace blocks found in the coder output.",
        )

    results = []
    total_changes_applied = 0
    errors = []

    for file_path_str, changes in changes_by_file.items():
        file_path = Path(file_path_str)
        if not file_path.is_absolute():
            file_path = base_path / file_path

        if not file_path.exists():
            error_msg = (
                f"File not found: {file_path_str}. Cannot apply changes."
            )
            logger.error(error_msg)
            errors.append(error_msg)
            continue

        try:
            original_content = file_path.read_text()
            content = original_content
        except Exception as e:
            error_msg = f"Error reading file {file_path}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
            continue

        num_changes_applied = 0
        file_errors = []
        for search_block, replace_block in changes:
            if search_block in content:
                content = content.replace(search_block, replace_block, 1)
                num_changes_applied += 1
            else:
                error_msg = f"Search block not found in {file_path}. Skipping this change."
                logger.error(error_msg)
                logger.debug(f"--- Search Block ---\n{search_block}\n---")
                file_errors.append(error_msg)

        if content != original_content:
            try:
                file_path.write_text(content)
                total_changes_applied += num_changes_applied
                results.append(
                    f"Successfully applied {num_changes_applied} change(s) to {file_path}"
                )
                logger.info(
                    f"Successfully applied {num_changes_applied} change(s) to {file_path}"
                )
            except Exception as e:
                error_msg = f"Error writing to file {file_path}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        else:
            # Check if any change was attempted with non-identical search/replace blocks
            if any(s != r for s, r in changes if s in original_content):
                warning_msg = f"Content of {file_path} is unchanged after applying modifications."
                logger.warning(warning_msg)
                results.append(warning_msg)
            else:
                info_msg = f"No changes applied to {file_path} as content was already compliant or no valid search blocks found."
                logger.info(info_msg)
                results.append(info_msg)

        if file_errors:
            errors.extend(file_errors)

    success = len(errors) == 0 and total_changes_applied > 0
    output = {
        "total_changes_applied": total_changes_applied,
        "results": results,
        "files_processed": len(changes_by_file),
        "successful_files": len(
            [r for r in results if "Successfully applied" in r]
        ),
        "summary": coder_output.summary,
    }

    if errors:
        return ToolResult(
            success=success, output=output, error="; ".join(errors)
        )

    return ToolResult(success=success, output=output)


async def cache_available_files(
    project_root: Path, available_files_cache: Path
):
    """Load all files in project root recursively and save to cache, respecting .gitignore."""

    def _load():
        files = list(project_root.rglob("*"))
        files = [f for f in files if f.is_file()]
        # Exclude .git directory to avoid loading large or unwanted files
        files = [f for f in files if ".git" not in f.parts]

        # Respect .gitignore to avoid loading large or unwanted files
        gitignore_path = project_root / ".gitignore"
        if gitignore_path.exists():
            with open(gitignore_path, "r") as f:
                spec = pathspec.PathSpec.from_lines("gitwildmatch", f)
            files = [
                f
                for f in files
                if not spec.match_file(str(f.relative_to(project_root)))
            ]

        available_files_cache.parent.mkdir(parents=True, exist_ok=True)
        file_names = [str(f.relative_to(project_root)) for f in files]
        with open(available_files_cache, "w") as f:
            for file_name in file_names:
                f.write(file_name + "\n")

    await asyncio.to_thread(_load)

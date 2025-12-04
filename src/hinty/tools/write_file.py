from pathlib import Path

from loguru import logger

from hinty.core.models import ToolResult


async def tool_write_file(file_path: str, content: str) -> ToolResult:
    """
    Write content to a file at the specified path.

    Args:
        file_path: The path to the file to write to.
        content: The content to write into the file.

    Returns:
        ToolResult indicating success or failure.
    """
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        logger.info(f"Successfully wrote to file: {file_path}")
        return ToolResult(
            success=True, output="File written successfully.", error=None
        )
    except Exception as e:
        error_msg = f"Failed to write to file {file_path}: {str(e)}"
        logger.error(error_msg)
        return ToolResult(success=False, output=None, error=error_msg)

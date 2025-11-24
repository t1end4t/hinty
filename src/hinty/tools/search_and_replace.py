import re
from collections import defaultdict
from pathlib import Path

from loguru import logger

from ..core.models import ToolResult


def tool_apply_search_replace(diff_content: str, base_path: Path) -> ToolResult:
    """
    Applies search and replace operations based on a diff content format.

    The diff content should be structured as follows for each change:
    file_path
    ```language
    <<<<<<< SEARCH
    [code to be replaced]
    =======
    [new code]
    >>>>>>> REPLACE
    ```

    Args:
        diff_content: A string containing one or more search/replace blocks.
        base_path: The base path for relative file paths.

    Returns:
        ToolResult: Result containing success status, applied changes, and any errors.
    """
    changes_by_file = defaultdict(list)
    for match in BLOCK_REGEX.finditer(diff_content):
        file_path = match.group("file_path").strip()
        search_block = match.group("search")
        replace_block = match.group("replace")
        changes_by_file[file_path].append((search_block, replace_block))

    if not changes_by_file:
        logger.warning("No search/replace blocks found in the diff content.")
        return ToolResult(
            success=False,
            error="No search/replace blocks found in the diff content.",
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
    }

    if errors:
        return ToolResult(
            success=success, output=output, error="; ".join(errors)
        )

    return ToolResult(success=success, output=output)

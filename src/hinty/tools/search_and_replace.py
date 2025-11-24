import re
from collections import defaultdict
from pathlib import Path

from loguru import logger

BLOCK_REGEX = re.compile(
    r"^\s*(?P<file_path>[^\n]+)\s*\n"
    r"```[a-zA-Z0-9]*\n"
    r"<<<<<<< SEARCH\n"
    r"(?P<search>.*?)"
    r"\n=======\n"
    r"(?P<replace>.*?)"
    r"\n>>>>>>> REPLACE\n"
    r"```",
    re.DOTALL | re.MULTILINE,
)


def tool_apply_search_replace(diff_content: str, base_path: Path) -> None:
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
    """
    changes_by_file = defaultdict(list)
    for match in BLOCK_REGEX.finditer(diff_content):
        file_path = match.group("file_path").strip()
        search_block = match.group("search")
        replace_block = match.group("replace")
        changes_by_file[file_path].append((search_block, replace_block))

    if not changes_by_file:
        logger.warning("No search/replace blocks found in the diff content.")
        return

    for file_path_str, changes in changes_by_file.items():
        file_path = Path(file_path_str)
        if not file_path.is_absolute():
            file_path = base_path / file_path

        if not file_path.exists():
            logger.error(f"File not found: {file_path_str}. Cannot apply changes.")
            continue

        try:
            original_content = file_path.read_text()
            content = original_content
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            continue

        num_changes_applied = 0
        for search_block, replace_block in changes:
            if search_block in content:
                content = content.replace(search_block, replace_block, 1)
                num_changes_applied += 1
            else:
                logger.error(
                    f"Search block not found in {file_path}. Skipping this change."
                )
                logger.debug(f"--- Search Block ---\n{search_block}\n---")

        if content != original_content:
            try:
                file_path.write_text(content)
                logger.info(
                    f"Successfully applied {num_changes_applied} change(s) to {file_path}"
                )
            except Exception as e:
                logger.error(f"Error writing to file {file_path}: {e}")
        else:
            # Check if any change was attempted with non-identical search/replace blocks
            if any(s != r for s, r in changes if s in original_content):
                logger.warning(
                    f"Content of {file_path} is unchanged after applying modifications."
                )
            else:
                logger.info(
                    f"No changes applied to {file_path} as content was already compliant or no valid search blocks found."
                )

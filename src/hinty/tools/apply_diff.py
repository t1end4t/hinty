from pathlib import Path
from typing import List, Tuple
from loguru import logger


def parse_unified_diff(diff_content: str) -> List[Tuple[str, List[str]]]:
    """Parse unified diff format into file changes.

    Returns list of (filepath, diff_lines) tuples.
    """
    logger.debug("Parsing unified diff content")

    files = []
    current_file = None
    current_lines = []

    for line in diff_content.split("\n"):
        if line.startswith("--- "):
            if current_file and current_lines:
                files.append((current_file, current_lines))
            current_file = None
            current_lines = []
        elif line.startswith("+++ "):
            filepath = line[4:].split("\t")[0].strip()
            if filepath.startswith("b/"):
                filepath = filepath[2:]
            current_file = filepath
        elif current_file:
            current_lines.append(line)

    if current_file and current_lines:
        files.append((current_file, current_lines))

    logger.info(f"Parsed {len(files)} file(s) from diff")
    return files


def apply_hunk(original_lines: List[str], hunk_lines: List[str]) -> List[str]:
    """Apply a single diff hunk to original content."""
    result = []
    orig_idx = 0
    i = 0

    while i < len(hunk_lines):
        line = hunk_lines[i]

        if line.startswith("@@"):
            # Parse hunk header: @@ -start,count +start,count @@
            parts = line.split("@@")[1].strip().split()
            orig_start = int(parts[0].split(",")[0][1:]) - 1

            # Add lines before this hunk
            while orig_idx < orig_start:
                result.append(original_lines[orig_idx])
                orig_idx += 1

        elif line.startswith("-"):
            # Line removed - skip in original
            orig_idx += 1

        elif line.startswith("+"):
            # Line added - add to result
            result.append(line[1:])

        elif line.startswith(" "):
            # Context line - verify and add
            if orig_idx < len(original_lines):
                result.append(original_lines[orig_idx])
                orig_idx += 1

        i += 1

    # Add remaining lines
    while orig_idx < len(original_lines):
        result.append(original_lines[orig_idx])
        orig_idx += 1

    return result


def apply_diff_to_file(filepath: Path, diff_lines: List[str]) -> bool:
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

        modified_lines = apply_hunk(original_lines, diff_lines)
        modified_content = "\n".join(modified_lines)

        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(modified_content)

        logger.info(f"Successfully applied diff to {filepath}")
        return True

    except Exception as e:
        logger.error(f"Failed to apply diff to {filepath}: {e}")
        return False


def apply_diff(diff_content: str, base_path: Path = Path.cwd()) -> bool:
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
    for filepath_str, diff_lines in file_changes:
        filepath = base_path / filepath_str
        if not apply_diff_to_file(filepath, diff_lines):
            success = False

    logger.info(f"Diff application {'successful' if success else 'failed'}")
    return success

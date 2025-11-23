from pathlib import Path
from typing import List, Tuple
from loguru import logger
from unidiff import PatchSet


def parse_unified_diff(diff_content: str) -> List[Tuple[str, List]]:
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
        files.append((filepath, patch.hunks))

    logger.info(f"Parsed {len(files)} file(s) from diff")
    return files


def apply_hunk(original_lines: List[str], hunk) -> List[str]:
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


def apply_diff_to_file(filepath: Path, hunks: List) -> bool:
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

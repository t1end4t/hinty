import re
from pathlib import Path
from typing import List, Tuple, Optional
from loguru import logger


def parse_search_replace_blocks(content: str) -> List[Tuple[str, str, str]]:
    """Parse search/replace blocks from content.

    Expects format:
        file_path
        ```language
        <<<<<<< SEARCH
        old_content
        =======
        new_content
        >>>>>>> REPLACE
        ```

    Returns:
        List of (filepath, search, replace) tuples.
    """
    logger.debug("Parsing search/replace blocks")
    blocks = []

    # Pattern to match the block structure
    # Made more flexible: optional language specifier, works anywhere in content
    pattern = r"([^\n]+)\n```[^\n]*\n<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE\n```"

    matches = re.findall(pattern, content, re.DOTALL | re.MULTILINE)

    for filepath, search, replace in matches:
        # Only strip filepath, preserve exact whitespace in search/replace
        blocks.append((filepath.strip(), search, replace))
        logger.debug(f"Found block for: {filepath.strip()}")

    logger.info(f"Parsed {len(blocks)} search/replace block(s)")

    if not blocks:
        logger.debug(f"No blocks found. Content preview:\n{content[:300]}")

    return blocks


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace for comparison (collapse multiple spaces/tabs)."""
    return " ".join(text.split())


def find_best_match_location(content: str, search: str) -> Optional[int]:
    """Try to find where the search block should match, even with whitespace issues.

    Returns:
        Line number (1-indexed) if approximate match found, None otherwise.
    """
    normalized_search = normalize_whitespace(search)

    # Try to find in content line by line
    lines = content.splitlines()

    for i, line in enumerate(lines, 1):
        normalized_line = normalize_whitespace(line)
        if normalized_search in normalized_line:
            return i

    # Try multi-line match
    search_lines = [normalize_whitespace(line) for line in search.splitlines()]
    if not search_lines:
        return None

    first_search_line = search_lines[0]

    for i, line in enumerate(lines, 1):
        if normalize_whitespace(line) == first_search_line:
            # Check if subsequent lines also match
            if i + len(search_lines) - 1 <= len(lines):
                match = True
                for j, search_line in enumerate(search_lines):
                    if normalize_whitespace(lines[i - 1 + j]) != search_line:
                        match = False
                        break
                if match:
                    return i

    return None


def apply_search_replace_to_file(
    filepath: Path, search: str, replace: str, strict: bool = True
) -> bool:
    """Apply a single search/replace to a file.

    Args:
        filepath: Path to the file
        search: Text to search for (must match exactly)
        replace: Text to replace with
        strict: If True, require exact match. If False, try normalized whitespace.

    Returns:
        True if successful, False otherwise.
    """
    logger.info(f"Applying search/replace to {filepath}")

    try:
        # Read existing file or start with empty content
        if filepath.exists():
            content = filepath.read_text(encoding="utf-8")
            logger.debug(f"File exists, size: {len(content)} chars")
        else:
            logger.warning(f"File {filepath} does not exist, creating new")
            content = ""

        # Try exact match first
        if search in content:
            logger.debug("Exact match found")
            new_content = content.replace(search, replace, 1)

            # Write the result
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(new_content, encoding="utf-8")

            logger.info(f"✓ Successfully applied search/replace to {filepath}")
            return True

        # Exact match failed
        logger.warning(f"Exact match not found in {filepath}")

        # Try to diagnose the issue
        match_line = find_best_match_location(content, search)
        if match_line:
            logger.warning(
                f"Found approximate match near line {match_line}, but whitespace differs."
            )
            logger.warning(
                "Check that your SEARCH block has the exact same indentation/spacing as the original file."
            )
        else:
            logger.warning("Could not find even an approximate match.")

        # Debug output
        logger.debug("=" * 60)
        logger.debug("SEARCH BLOCK (first 300 chars):")
        logger.debug(repr(search[:300]))
        logger.debug("=" * 60)
        logger.debug("FILE CONTENT (first 300 chars):")
        logger.debug(repr(content[:300]))
        logger.debug("=" * 60)

        # If not strict mode, try normalized whitespace replacement (DANGEROUS)
        if not strict:
            logger.warning("Attempting non-strict mode (normalized whitespace)")
            # This is risky and generally not recommended
            # Only use for debugging purposes
            normalized_search = normalize_whitespace(search)
            normalized_content = normalize_whitespace(content)

            if normalized_search in normalized_content:
                logger.error(
                    "Found match with normalized whitespace, but this mode is not safe for replacement. "
                    "Fix your SEARCH block to match exact whitespace."
                )

        return False

    except UnicodeDecodeError as e:
        logger.error(f"Encoding error reading {filepath}: {e}")
        logger.error(
            "Try specifying a different encoding or check if file is binary"
        )
        return False
    except Exception as e:
        logger.error(f"Failed to apply search/replace to {filepath}: {e}")
        logger.exception("Full traceback:")
        return False


def tool_apply_search_replace(
    blocks_content: str,
    base_path: Path = Path.cwd(),
    strict: bool = True,
    dry_run: bool = False,
) -> bool:
    """Apply search/replace blocks to files.

    Args:
        blocks_content: String containing search/replace blocks
        base_path: Base directory for resolving file paths
        strict: If True, require exact whitespace match
        dry_run: If True, only parse and validate without writing

    Returns:
        True if all replacements applied successfully (or validated in dry_run)
    """
    logger.info("=" * 70)
    logger.info(f"Starting search/replace application (dry_run={dry_run})")
    logger.info(f"Base path: {base_path}")
    logger.info("=" * 70)

    # Parse the blocks
    file_changes = parse_search_replace_blocks(blocks_content)

    if not file_changes:
        logger.warning("No search/replace blocks found in content")
        logger.debug("Content preview (first 500 chars):")
        logger.debug(blocks_content[:500])
        return False

    logger.info(f"Found {len(file_changes)} block(s) to apply")

    # Apply each block
    success = True
    results = []

    for i, (filepath_str, search, replace) in enumerate(file_changes, 1):
        logger.info(f"\n[{i}/{len(file_changes)}] Processing: {filepath_str}")

        filepath = base_path / filepath_str

        if dry_run:
            logger.info(f"DRY RUN: Would modify {filepath}")
            logger.debug(f"Search length: {len(search)} chars")
            logger.debug(f"Replace length: {len(replace)} chars")

            # Check if file exists and search text is present
            if filepath.exists():
                content = filepath.read_text(encoding="utf-8")
                if search in content:
                    logger.info("✓ Validation passed: exact match found")
                    results.append((filepath_str, True))
                else:
                    logger.warning("✗ Validation failed: no exact match")
                    results.append((filepath_str, False))
                    success = False
            else:
                logger.info("File doesn't exist, would create new file")
                results.append((filepath_str, True))
        else:
            # Actually apply the change
            if not apply_search_replace_to_file(
                filepath, search, replace, strict
            ):
                success = False
                results.append((filepath_str, False))
            else:
                results.append((filepath_str, True))

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY:")
    logger.info("=" * 70)

    for filepath_str, result in results:
        status = "✓ SUCCESS" if result else "✗ FAILED"
        logger.info(f"{status}: {filepath_str}")

    success_count = sum(1 for _, result in results if result)
    logger.info(f"\nTotal: {success_count}/{len(results)} successful")

    if success:
        logger.info("✓ All operations completed successfully")
    else:
        logger.error("✗ Some operations failed")

    logger.info("=" * 70)

    return success


def validate_search_replace_blocks(blocks_content: str) -> bool:
    """Validate search/replace blocks without applying them.

    Args:
        blocks_content: String containing search/replace blocks

    Returns:
        True if blocks are valid and can be parsed
    """
    try:
        blocks = parse_search_replace_blocks(blocks_content)

        if not blocks:
            logger.error("No valid blocks found")
            return False

        logger.info(f"Validation successful: {len(blocks)} valid block(s)")

        for i, (filepath, search, replace) in enumerate(blocks, 1):
            logger.info(f"Block {i}:")
            logger.info(f"  File: {filepath}")
            logger.info(f"  Search: {len(search)} chars")
            logger.info(f"  Replace: {len(replace)} chars")

        return True

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return False

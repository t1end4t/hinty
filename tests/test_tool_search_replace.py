from pathlib import Path

from hinty.tools.file_operations import tool_apply_search_replace


def test_tool_apply_search_replace():
    # Read the sample.txt file containing search/replace blocks
    sample_path = Path(__file__).parent / "sample.txt"
    assert sample_path.exists(), f"sample.txt not found at {sample_path}"

    with open(sample_path, "r") as f:
        blocks_content = f.read()

    # Apply the search/replace blocks
    success = tool_apply_search_replace(blocks_content, base_path=Path.cwd())
    assert success, "Search/replace application failed"

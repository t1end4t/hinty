from pathlib import Path

from hinty.tools.file_operations import tool_apply_search_replace


def main():
    # Read the sample.txt file containing search/replace blocks
    sample_path = Path(__file__).parent / "sample.txt"
    if not sample_path.exists():
        print(f"sample.txt not found at {sample_path}")
        return

    with open(sample_path, "r") as f:
        blocks_content = f.read()

    # Apply the search/replace blocks
    success = tool_apply_search_replace(blocks_content, base_path=Path.cwd())
    print(f"Search/replace application {'succeeded' if success else 'failed'}")


if __name__ == "__main__":
    main()

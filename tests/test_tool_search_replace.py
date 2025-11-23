from pathlib import Path

from hinty.tools.file_operations import tool_apply_search_replace


def main():
    # Define search/replace blocks content
    blocks_content = """tests/sample.txt
```python
<<<<<<< SEARCH
line 1
line 2
line 3
new line
=======
line 1
line 2 edited
line 3
new line
>>>>>>> REPLACE
```"""

    sample_path = Path(__file__).parent / "sample.txt"
    if not sample_path.exists():
        print(f"sample.txt not found at {sample_path}")
        return

    # Read and print old content
    with open(sample_path, "r") as f:
        old_content = f.read()
    print("Old content:")
    print(old_content)

    # Apply the search/replace blocks
    success = tool_apply_search_replace(blocks_content, base_path=Path.cwd())
    print(f"Search/replace application {'succeeded' if success else 'failed'}")

    # Read and print new content
    with open(sample_path, "r") as f:
        new_content = f.read()
    print("New content:")
    print(new_content)


if __name__ == "__main__":
    main()

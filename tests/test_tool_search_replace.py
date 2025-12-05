from pathlib import Path

from hinty.baml_client.types import CoderOutput, FileChange, SearchReplaceBlock
from hinty.tools.search_and_replace import tool_search_and_replace


def main():
    # Create sample.txt if it doesn't exist
    sample_path = Path(__file__).parent / "sample.txt"
    if not sample_path.exists():
        sample_path.write_text("line 1\nline 2\nline 3\n")
        print(f"Created sample.txt at {sample_path}")

    # Read and print old content
    with open(sample_path, "r") as f:
        old_content = f.read()
    print("Old content:")
    print(old_content)

    # Create CoderOutput with search/replace blocks
    search_block = "line 1\nline 2\nline 3\n"
    replace_block = "line 1\nline 2 edited\nline 3\nnew line\n"
    coder_output = CoderOutput(
        thinking="Applying a simple edit to sample.txt for testing.",
        files_to_change=[
            FileChange(
                file_path="tests/sample.txt",
                blocks=[
                    SearchReplaceBlock(
                        search=search_block,
                        replace=replace_block,
                        language="python",
                    )
                ],
                explanation="Editing line 2 and adding a new line.",
            )
        ],
        additional_files_to_check=[],
        summary="Test search and replace operation.",
    )

    # Apply the search/replace blocks
    result = tool_search_and_replace(coder_output, base_path=Path.cwd())
    print(
        f"Search/replace application {'succeeded' if result.success else 'failed'}"
    )
    if not result.success:
        print(f"Error: {result.error}")

    # Read and print new content
    with open(sample_path, "r") as f:
        new_content = f.read()
    print("New content:")
    print(new_content)


if __name__ == "__main__":
    main()

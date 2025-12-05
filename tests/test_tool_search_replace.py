line 1
line 2 edited
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
    result = tool_search_and_replace(blocks_content, base_path=Path.cwd())
    print(
        f"Search/replace application {'succeeded' if result.success else 'failed'}"
    )

    # Read and print new content
    with open(sample_path, "r") as f:
        new_content = f.read()
    print("New content:")
    print(new_content)


if __name__ == "__main__":
    main()

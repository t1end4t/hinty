from pathlib import Path

from hinty.tools.file_operations import tool_apply_search_replace


def main():
    # Specify the search/replace blocks content directly
    blocks_content = """tests/dummy.txt
```python
<<<<<<< SEARCH
old content

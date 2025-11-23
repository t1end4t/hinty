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

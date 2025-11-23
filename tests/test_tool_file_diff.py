#!/usr/bin/env python3
"""Simple test script to demonstrate applying a diff using file_diff tool."""

from pathlib import Path
from src.hinty.tools.file_diff import tool_apply_diff


def main():
    temp_path = Path(".")
    
    # Create a sample file to edit
    sample_file = temp_path / "sample.txt"
    sample_file.write_text("line 1\nline 2\nline 3\n")
    
    print("Original file content:")
    print(sample_file.read_text())
    
    # Sample unified diff that adds a line after line 2
    diff_content = """--- a/sample.txt
+++ b/sample.txt
@@ -1,3 +1,4 @@
 line 1
 line 2
+new line
 line 3
"""
    
    # Apply the diff
    success = tool_apply_diff(diff_content, base_path=temp_path)
    
    print(f"Diff application success: {success}")
    print("Modified file content:")
    print(sample_file.read_text())


if __name__ == "__main__":
    main()

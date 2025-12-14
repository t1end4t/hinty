import json
import sys
from pathlib import Path

from hinty.context.analyze_related_files import (
    analyze_related_files,
)


def main():
    if len(sys.argv) > 2:
        project_root = Path(sys.argv[1])
        target_file = Path(sys.argv[2])
    else:
        project_root = Path.cwd()
        target_file = Path("src/hinty/cli/commands.py")

    result, excerpts = analyze_related_files(project_root, target_file)

    related_files = []
    for f in result.imported_from:
        excerpt = excerpts.get(f, "")
        related_files.append(
            {
                "file_path": str(f),
                "relationship": "imports_from",
                "relevant_excerpt": excerpt,
            }
        )

    print(f"Analyzing file: {target_file}")
    print(json.dumps(related_files, indent=2))


if __name__ == "__main__":
    main()

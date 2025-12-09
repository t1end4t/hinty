import ast
from pathlib import Path
from typing import Dict, List


def get_related_filepaths(
    target_file: Path, project_root: Path
) -> Dict[str, List[Path]]:
    """
    Extract filepaths related to the target file, including imports_from, imported_by, uses, used_by, tests, etc.

    - imports_from: Files that the target file imports.
    - imported_by: Files that import the target file.
    - uses: Same as imports_from (files used by the target).
    - used_by: Same as imported_by (files that use the target).
    - tests: Test files related to the target file (based on name matching).
    """
    result = {
        "imports_from": [],
        "imported_by": [],
        "uses": [],
        "used_by": [],
        "tests": [],
    }

    # Get module name from target_file relative to project_root
    rel_path = target_file.relative_to(project_root)
    module_name = (
        str(rel_path).replace("/", ".").replace("\\", ".").replace(".py", "")
    )

    # Helper to convert module name to path (assuming src/hinty/... structure)
    def module_to_path(module: str) -> Path | None:
        parts = module.split(".")
        if parts[0] == "hinty":
            path = project_root / "src" / "hinty" / "/".join(parts[1:]) + ".py"
            if path.exists():
                return path
        return None

    # Parse target file for imports
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except Exception:
        return result  # If can't parse, return empty

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)

    # Resolve imports to filepaths
    for imp in imports:
        path = module_to_path(imp)
        if path:
            result["imports_from"].append(path)

    result["uses"] = result["imports_from"]  # Uses is same as imports_from

    # Find files that import this module
    for file in project_root.rglob("*.py"):
        if file == target_file:
            continue
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
            if (
                f"import {module_name}" in content
                or f"from {module_name}" in content
            ):
                result["imported_by"].append(file)
        except Exception:
            pass

    result["used_by"] = result["imported_by"]  # Used_by is same as imported_by

    # Find related test files
    test_dir = project_root / "tests"
    if test_dir.exists():
        target_stem = target_file.stem
        for file in test_dir.rglob("*.py"):
            if (
                target_stem in file.stem
                or file.stem.replace("test_", "") == target_stem
            ):
                result["tests"].append(file)

    return result

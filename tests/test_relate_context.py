import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Set


def extract_related_filepaths(
    target_file: Path, project_root: Path
) -> Dict[str, List[Path]]:
    """
    Extract filepaths related to the target file, including imports_from, imported_by, uses, used_by, tests, etc.
    Uses AST parsing to analyze code structure.
    """
    related = {
        "imports_from": [],
        "imported_by": [],
        "uses": [],
        "used_by": [],
        "tests": [],
    }

    # Normalize paths
    target_file = target_file.resolve()
    project_root = project_root.resolve()

    # Get target module name
    target_module = _path_to_module(target_file, project_root)

    # Find all Python files in project
    all_py_files = list(project_root.rglob("*.py"))

    # Parse target file for imports_from and uses
    if target_file.exists():
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content, filename=str(target_file))
            _analyze_file(
                tree, target_file, project_root, related, "imports_from", "uses"
            )
        except SyntaxError:
            pass  # Skip files with syntax errors

    # Scan all files for imported_by and used_by
    for file_path in all_py_files:
        if file_path == target_file:
            continue
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content, filename=str(file_path))
            _check_imports_and_uses(
                tree, file_path, project_root, target_module, related
            )
        except SyntaxError:
            pass

    # Find test files
    test_dirs = ["tests", "test"]
    for test_dir in test_dirs:
        test_path = project_root / test_dir
        if test_path.exists():
            for test_file in test_path.rglob("*.py"):
                if (
                    target_file.stem in test_file.stem
                    or test_file.stem in target_file.stem
                ):
                    related["tests"].append(test_file)

    # Remove duplicates and sort
    for key in related:
        related[key] = sorted(set(related[key]))

    return related


def _path_to_module(file_path: Path, project_root: Path) -> str:
    """Convert file path to module name."""
    rel_path = file_path.relative_to(project_root)
    return str(rel_path.with_suffix("")).replace(os.sep, ".")


def _analyze_file(
    tree: ast.AST,
    file_path: Path,
    project_root: Path,
    related: Dict,
    imports_key: str,
    uses_key: str,
):
    """Analyze a single file for imports and uses."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name.split(".")[0]
                imported_file = _module_to_path(module, project_root)
                if imported_file:
                    related[imports_key].append(imported_file)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module = node.module.split(".")[0]
                imported_file = _module_to_path(module, project_root)
                if imported_file:
                    related[imports_key].append(imported_file)
        elif isinstance(node, ast.Call):
            # Simple heuristic for uses: if calling a function that might be from another file
            if isinstance(node.func, ast.Name):
                # This is simplistic; in reality, you'd need symbol resolution
                pass  # Placeholder for more complex analysis


def _check_imports_and_uses(
    tree: ast.AST,
    file_path: Path,
    project_root: Path,
    target_module: str,
    related: Dict,
):
    """Check if file imports or uses the target module."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == target_module or alias.name.startswith(
                    target_module + "."
                ):
                    related["imported_by"].append(file_path)
        elif isinstance(node, ast.ImportFrom):
            if node.module == target_module or node.module.startswith(
                target_module + "."
            ):
                related["imported_by"].append(file_path)
        # For used_by, similar simplistic check
        # In practice, this would require more advanced static analysis


def _module_to_path(module: str, project_root: Path) -> Path | None:
    """Attempt to convert module name to file path."""
    # Simple heuristic: assume module corresponds to file or package
    possible_paths = [
        project_root / f"{module}.py",
        project_root / module / "__init__.py",
    ]
    for path in possible_paths:
        if path.exists():
            return path
    return None


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(
            "Usage: python test_relate_context.py <target_file> <project_root>"
        )
        sys.exit(1)

    target_file = Path(sys.argv[1])
    project_root = Path(sys.argv[2])

    related = extract_related_filepaths(target_file, project_root)

    for key, paths in related.items():
        print(f"{key}:")
        for path in paths:
            print(f"  {path}")
        print()

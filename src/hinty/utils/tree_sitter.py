import ast
from pathlib import Path
from typing import List


def get_all_objects(file_path: Path) -> List[str]:
    """
    Extract all object names (functions, classes, variables, including inner ones) from a Python file using AST.
    For non-Python files, return an empty list.
    """
    if file_path.suffix != ".py":
        return []

    def collect_names(node: ast.AST) -> List[str]:
        names = []
        if isinstance(node, ast.FunctionDef):
            names.append(node.name)
        elif isinstance(node, ast.ClassDef):
            names.append(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.append(target.id)
        for child in ast.iter_child_nodes(node):
            names.extend(collect_names(child))
        return names

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        tree = ast.parse(content, filename=str(file_path))
        return collect_names(tree)
    except (SyntaxError, FileNotFoundError, UnicodeDecodeError):
        return []

import ast
from pathlib import Path
from typing import List


def get_top_level_objects(file_path: Path) -> List[str]:
    """
    Extract top-level object names (functions, classes, variables) from a Python file using AST.
    For non-Python files, return an empty list.
    """
    if file_path.suffix != '.py':
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content, filename=str(file_path))
        objects = []
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                objects.append(node.name)
            elif isinstance(node, ast.ClassDef):
                objects.append(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        objects.append(target.id)
        return objects
    except (SyntaxError, FileNotFoundError, UnicodeDecodeError):
        return []

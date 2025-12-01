from pathlib import Path
from typing import List
from tree_sitter import Parser
import tree_sitter_python as tspython


def get_all_objects(file_path: Path) -> List[str]:
    """
    Extract all object names (functions, classes, variables, parameters, including inner ones) from a Python file using tree-sitter.
    For non-Python files, return an empty list.
    """
    if file_path.suffix != ".py":
        return []
    
    parser = Parser()
    parser.set_language(tspython.language())
    
    try:
        with open(file_path, "rb") as f:
            content = f.read()
        tree = parser.parse(content)
        return collect_names(tree.root_node)
    except (FileNotFoundError, UnicodeDecodeError):
        return []


def collect_names(node) -> List[str]:
    names = []
    if node.type == "function_definition":
        # Function name
        name_node = node.child_by_field_name("name")
        if name_node:
            names.append(name_node.text.decode("utf-8"))
        # Parameters
        params_node = node.child_by_field_name("parameters")
        if params_node:
            names.extend(collect_identifiers(params_node))
    elif node.type == "class_definition":
        # Class name
        name_node = node.child_by_field_name("name")
        if name_node:
            names.append(name_node.text.decode("utf-8"))
    elif node.type == "assignment":
        # Left side of assignment
        left_node = node.child_by_field_name("left")
        if left_node:
            names.extend(collect_identifiers(left_node))
    
    # Recurse on children
    for child in node.children:
        names.extend(collect_names(child))
    
    return names


def collect_identifiers(node) -> List[str]:
    names = []
    if node.type == "identifier":
        names.append(node.text.decode("utf-8"))
    for child in node.children:
        names.extend(collect_identifiers(child))
    return names

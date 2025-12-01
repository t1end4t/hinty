from pathlib import Path
from typing import List
from tree_sitter import Parser, Node, Language
import tree_sitter_python as tspython

PY = Language(tspython.language())


def get_all_objects(file_path: Path) -> List[str]:
    """
    Extract all object names (functions, classes, variables, parameters, including inner ones)
    from a Python file using tree-sitter.
    For non-Python files, return an empty list.
    """
    if file_path.suffix != ".py":
        return []

    try:
        content = file_path.read_bytes()
    except (FileNotFoundError, UnicodeDecodeError):
        return []

    parser = Parser(language=PY)
    tree = parser.parse(content)

    return collect_names(tree.root_node)


def collect_names(node: Node) -> List[str]:
    names: List[str] = []

    match node.type:
        case "function_definition":
            if name := _get_field_text(node, "name"):
                names.append(name)
            params = node.child_by_field_name("parameters")
            if params:
                names.extend(collect_identifiers(params))

        case "class_definition":
            if name := _get_field_text(node, "name"):
                names.append(name)

        case "assignment":
            left = node.child_by_field_name("left")
            if left:
                names.extend(collect_identifiers(left))

    for child in node.children:
        names.extend(collect_names(child))

    return names


def collect_identifiers(node: Node) -> List[str]:
    names: List[str] = []

    if node.type == "identifier" and node.text:
        names.append(node.text.decode("utf-8"))

    for child in node.children:
        names.extend(collect_identifiers(child))

    return names


def _get_field_text(node: Node, field: str) -> str | None:
    child = node.child_by_field_name(field)

    if child and child.text:
        return child.text.decode("utf-8") if child else None

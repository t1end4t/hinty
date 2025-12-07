from pathlib import Path
from typing import List, Dict
from tree_sitter import Parser, Node, Language
from loguru import logger
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
import tree_sitter_typescript as tstypescript
import tree_sitter_rust as tsrust
import tree_sitter_go as tsgo
import tree_sitter_java as tsjava
import tree_sitter_cpp as tscpp

LANGUAGES: Dict[str, Language] = {
    ".py": Language(tspython.language()),
    ".js": Language(tsjavascript.language()),
    ".jsx": Language(tsjavascript.language()),
    ".ts": Language(tstypescript.language_typescript()),
    ".tsx": Language(tstypescript.language_tsx()),
    ".rs": Language(tsrust.language()),
    ".go": Language(tsgo.language()),
    ".java": Language(tsjava.language()),
    ".c": Language(tscpp.language()),
    ".cpp": Language(tscpp.language()),
    ".cc": Language(tscpp.language()),
    ".cxx": Language(tscpp.language()),
    ".h": Language(tscpp.language()),
    ".hpp": Language(tscpp.language()),
}


def _collect_names(node: Node) -> List[str]:
    names: List[str] = []

    match node.type:
        # Python
        case "function_definition" | "class_definition":
            if name := _get_field_text(node, "name"):
                names.append(name)
            if node.type == "function_definition":
                params = node.child_by_field_name("parameters")
                if params:
                    names.extend(_collect_identifiers(params))

        case "assignment":
            left = node.child_by_field_name("left")
            if left:
                names.extend(_collect_identifiers(left))

        # JavaScript/TypeScript
        case "function_declaration" | "class_declaration" | "method_definition":
            if name := _get_field_text(node, "name"):
                names.append(name)
            if node.type in ("function_declaration", "method_definition"):
                params = node.child_by_field_name("parameters")
                if params:
                    names.extend(_collect_identifiers(params))

        case "variable_declarator":
            if name := _get_field_text(node, "name"):
                names.append(name)

        # Rust
        case (
            "function_item"
            | "struct_item"
            | "enum_item"
            | "trait_item"
            | "impl_item"
        ):
            if name := _get_field_text(node, "name"):
                names.append(name)
            if node.type == "function_item":
                params = node.child_by_field_name("parameters")
                if params:
                    names.extend(_collect_identifiers(params))

        case "let_declaration":
            pattern = node.child_by_field_name("pattern")
            if pattern:
                names.extend(_collect_identifiers(pattern))

        # Go
        case "function_declaration" | "method_declaration" | "type_declaration":
            if name := _get_field_text(node, "name"):
                names.append(name)
            if node.type in ("function_declaration", "method_declaration"):
                params = node.child_by_field_name("parameters")
                if params:
                    names.extend(_collect_identifiers(params))

        case "var_declaration" | "short_var_declaration":
            names.extend(_collect_identifiers(node))

        # Java
        case "class_declaration" | "interface_declaration" | "enum_declaration":
            if name := _get_field_text(node, "name"):
                names.append(name)

        case "method_declaration" | "constructor_declaration":
            if name := _get_field_text(node, "name"):
                names.append(name)
            params = node.child_by_field_name("parameters")
            if params:
                names.extend(_collect_identifiers(params))

        case "variable_declarator":
            if name := _get_field_text(node, "name"):
                names.append(name)

        # C/C++
        case "function_definition" | "function_declarator":
            declarator = node.child_by_field_name("declarator")
            if declarator and declarator.type == "function_declarator":
                if name := _get_field_text(declarator, "declarator"):
                    names.append(name)
                params = declarator.child_by_field_name("parameters")
                if params:
                    names.extend(_collect_identifiers(params))
            elif name := _get_field_text(node, "declarator"):
                names.append(name)

        case "struct_specifier" | "class_specifier" | "enum_specifier":
            if name := _get_field_text(node, "name"):
                names.append(name)

        case "declaration":
            declarator = node.child_by_field_name("declarator")
            if declarator:
                names.extend(_collect_identifiers(declarator))

    for child in node.children:
        names.extend(_collect_names(child))

    return names


def _collect_identifiers(node: Node) -> List[str]:
    names: List[str] = []

    if node.type == "identifier" and node.text:
        names.append(node.text.decode("utf-8"))

    for child in node.children:
        names.extend(_collect_identifiers(child))

    return names


def _get_field_text(node: Node, field: str) -> str | None:
    child = node.child_by_field_name(field)

    if child and child.text:
        return child.text.decode("utf-8") if child else None


def get_all_objects(file_path: Path) -> List[str]:
    """
    Extract all object names (functions, classes, variables, parameters, including inner ones)
    from a source file using tree-sitter.
    Supports Python, JavaScript, TypeScript, Rust, Go, Java, and C/C++.
    For unsupported files, return an empty list.
    """
    language = LANGUAGES.get(file_path.suffix)
    if not language:
        return []

    try:
        content = file_path.read_bytes()
    except FileNotFoundError:
        logger.error(f"File {file_path} not found")
        return []
    except UnicodeDecodeError:
        logger.error(f"Failed to decode file {file_path}")
        return []

    parser = Parser(language=language)
    tree = parser.parse(content)

    return _collect_names(tree.root_node)

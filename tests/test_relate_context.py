from pathlib import Path
from typing import List, Dict
from tree_sitter import Language, Parser
from tree_sitter_python import language

PY_LANGUAGE = Language(language())
parser = Parser(PY_LANGUAGE)


def get_module_name(file_path: Path, project_root: Path) -> str:
    """Get the module name from a file path relative to project root."""
    relative = file_path.relative_to(project_root)
    parts = relative.parts
    if parts and parts[0] == 'src':
        return '.'.join(parts[1:]).replace('.py', '')
    return '.'.join(parts).replace('.py', '')


def extract_imports_from_file(file_path: Path) -> List[str]:
    """Extract imported module names from a Python file using tree-sitter."""
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()
    tree = parser.parse(bytes(code, 'utf-8'))
    imports = []

    def traverse(node):
        if node.type == 'import_statement':
            for child in node.children:
                if child.type == 'dotted_name':
                    imports.append(child.text.decode('utf-8'))
        elif node.type == 'import_from_statement':
            for child in node.children:
                if child.type == 'dotted_name':
                    imports.append(child.text.decode('utf-8'))
                    break
        for child in node.children:
            traverse(child)

    traverse(tree.root_node)
    return imports


def resolve_module_to_file(module: str, project_root: Path) -> Path | None:
    """Resolve a module name to a file path, assuming src/ structure."""
    file_path = project_root / 'src' / (module.replace('.', '/') + '.py')
    if file_path.exists():
        return file_path
    return None


def get_related_files(target_file: Path, project_root: Path, all_files: List[Path]) -> Dict[str, List[Path]]:
    """Extract filepaths related to the target file: imports_from, imported_by, uses, used_by, tests."""
    module_name = get_module_name(target_file, project_root)
    imports_from_modules = extract_imports_from_file(target_file)
    imports_from = [f for mod in imports_from_modules if (f := resolve_module_to_file(mod, project_root))]

    imported_by = []
    for file in all_files:
        if file == target_file or file.suffix != '.py':
            continue
        if module_name in extract_imports_from_file(file):
            imported_by.append(file)

    # 'uses' and 'used_by' are treated as synonyms for imports_from and imported_by
    uses = imports_from
    used_by = imported_by

    # 'tests': simplistic matching for test files in tests/ directory
    tests = []
    base_name = target_file.stem
    for file in all_files:
        if file.parent.name == 'tests' and base_name in file.stem and file.suffix == '.py':
            tests.append(file)

    return {
        'imports_from': imports_from,
        'imported_by': imported_by,
        'uses': uses,
        'used_by': used_by,
        'tests': tests
    }

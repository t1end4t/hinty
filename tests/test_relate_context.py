from pathlib import Path
from typing import Dict, List, Set
from tree_sitter import Language, Parser
import tree_sitter_python
from loguru import logger


def extract_imports(file_path: Path) -> Set[str]:
    """Extract all import statements from a Python file using tree-sitter."""
    try:
        content = file_path.read_text()
        parser = Parser()
        parser.set_language(Language(tree_sitter_python.language()))
        tree = parser.parse(bytes(content, "utf8"))
        
        imports = set()
        
        def traverse(node):
            if node.type == "import_statement":
                for child in node.children:
                    if child.type == "dotted_name":
                        imports.add(child.text.decode("utf8"))
            elif node.type == "import_from_statement":
                module_name = None
                for child in node.children:
                    if child.type == "dotted_name":
                        module_name = child.text.decode("utf8")
                        break
                if module_name:
                    imports.add(module_name)
            
            for child in node.children:
                traverse(child)
        
        traverse(tree.root_node)
        return imports
    except Exception as e:
        logger.error(f"Failed to extract imports from {file_path}: {e}")
        return set()


def extract_function_calls(file_path: Path) -> Set[str]:
    """Extract all function calls from a Python file using tree-sitter."""
    try:
        content = file_path.read_text()
        parser = Parser()
        parser.set_language(Language(tree_sitter_python.language()))
        tree = parser.parse(bytes(content, "utf8"))
        
        calls = set()
        
        def traverse(node):
            if node.type == "call":
                func_node = node.child_by_field_name("function")
                if func_node:
                    if func_node.type == "identifier":
                        calls.add(func_node.text.decode("utf8"))
                    elif func_node.type == "attribute":
                        calls.add(func_node.text.decode("utf8"))
            
            for child in node.children:
                traverse(child)
        
        traverse(tree.root_node)
        return calls
    except Exception as e:
        logger.error(f"Failed to extract function calls from {file_path}: {e}")
        return set()


def module_to_file_path(
    module_name: str, project_root: Path
) -> Path | None:
    """Convert a module name to a file path."""
    parts = module_name.split(".")
    
    # Try as a package
    package_path = project_root / "src" / "/".join(parts) / "__init__.py"
    if package_path.exists():
        return package_path
    
    # Try as a module
    module_path = project_root / "src" / "/".join(parts[:-1]) / f"{parts[-1]}.py"
    if module_path.exists():
        return module_path
    
    # Try without src directory
    package_path = project_root / "/".join(parts) / "__init__.py"
    if package_path.exists():
        return package_path
    
    module_path = project_root / "/".join(parts[:-1]) / f"{parts[-1]}.py"
    if module_path.exists():
        return module_path
    
    return None


def is_test_file(file_path: Path, target_path: Path) -> bool:
    """Check if a file is a test file for the target."""
    target_name = target_path.stem
    file_name = file_path.stem
    
    # Check if it's in a tests directory
    if "test" not in str(file_path).lower():
        return False
    
    # Check naming patterns
    return (
        file_name == f"test_{target_name}"
        or file_name == f"{target_name}_test"
        or target_name in file_name
    )


def get_related_files(
    target_file: Path, project_root: Path
) -> Dict[str, List[Path]]:
    """
    Extract files related to the target file.
    
    Returns a dictionary with:
    - imports_from: Files that the target imports from
    - imported_by: Files that import the target
    - uses: Files that use functions/classes from the target
    - used_by: Files whose functions/classes are used by the target
    - tests: Test files for the target
    """
    logger.info(f"Analyzing relationships for {target_file}")
    
    result = {
        "imports_from": [],
        "imported_by": [],
        "uses": [],
        "used_by": [],
        "tests": [],
    }
    
    # Get imports from target file
    target_imports = extract_imports(target_file)
    target_calls = extract_function_calls(target_file)
    
    # Convert target file to module name
    try:
        target_relative = target_file.relative_to(project_root / "src")
        target_module = str(target_relative.with_suffix("")).replace("/", ".")
    except ValueError:
        try:
            target_relative = target_file.relative_to(project_root)
            target_module = str(target_relative.with_suffix("")).replace("/", ".")
        except ValueError:
            logger.warning(f"Could not determine module name for {target_file}")
            target_module = None
    
    # Find all Python files in project
    python_files = list(project_root.rglob("*.py"))
    
    for py_file in python_files:
        if py_file == target_file:
            continue
        
        # Check if it's a test file
        if is_test_file(py_file, target_file):
            result["tests"].append(py_file)
        
        # Get imports and calls from this file
        file_imports = extract_imports(py_file)
        file_calls = extract_function_calls(py_file)
        
        # Check if target imports from this file
        try:
            file_relative = py_file.relative_to(project_root / "src")
            file_module = str(file_relative.with_suffix("")).replace("/", ".")
        except ValueError:
            try:
                file_relative = py_file.relative_to(project_root)
                file_module = str(file_relative.with_suffix("")).replace("/", ".")
            except ValueError:
                continue
        
        if file_module in target_imports:
            result["imports_from"].append(py_file)
        
        # Check if this file imports target
        if target_module and target_module in file_imports:
            result["imported_by"].append(py_file)
    
    logger.info(
        f"Found {len(result['imports_from'])} imports_from, "
        f"{len(result['imported_by'])} imported_by, "
        f"{len(result['tests'])} tests"
    )
    
    return result


def main():
    """Test the related files extraction."""
    project_root = Path.cwd()
    target_file = project_root / "src/hinty/core/project_manager.py"
    
    if not target_file.exists():
        logger.error(f"Target file does not exist: {target_file}")
        return
    
    related = get_related_files(target_file, project_root)
    
    print(f"\nRelated files for {target_file.name}:\n")
    
    for category, files in related.items():
        print(f"{category}:")
        if files:
            for f in files:
                print(f"  - {f.relative_to(project_root)}")
        else:
            print("  (none)")
        print()


if __name__ == "__main__":
    main()

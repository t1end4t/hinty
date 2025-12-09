import json
import os
from collections import Counter
from pathlib import Path
from tree_format import format_tree
import pathspec


def get_tree_with_library(directory="."):
    """Generate tree using tree-format library, respecting .gitignore"""
    path = Path(directory).resolve()

    # Load .gitignore patterns
    gitignore_spec = None
    gitignore_path = Path(directory) / ".gitignore"
    if gitignore_path.exists():
        with open(gitignore_path, "r") as f:
            patterns = f.read().splitlines()
            gitignore_spec = pathspec.PathSpec.from_lines(
                "gitwildmatch", patterns
            )

    def is_ignored(p):
        """Check if path should be ignored"""
        if gitignore_spec is None:
            return False

        # Get relative path from root directory
        try:
            rel_path = p.relative_to(path)
            # Check both the path and path with trailing slash for directories
            if gitignore_spec.match_file(str(rel_path)):
                return True
            if p.is_dir() and gitignore_spec.match_file(str(rel_path) + "/"):
                return True
        except ValueError:
            pass
        return False

    def build_tree(p):
        """Recursively build tree structure"""
        if p.is_file():
            return (p.name, [])

        children = []
        try:
            for child in sorted(p.iterdir()):
                # Skip hidden files/folders starting with .
                if child.name.startswith("."):
                    continue

                # Skip if ignored by .gitignore
                if is_ignored(child):
                    continue

                subtree = build_tree(child)
                if subtree:
                    children.append(subtree)
        except PermissionError:
            pass

        return (p.name, children)

    tree = build_tree(path)
    return format_tree(
        tree,
        format_node=lambda node: node[0],
        get_children=lambda node: node[1],
    )


def get_primary_language(directory="."):
    """Determine the primary programming language of the project in the given directory."""
    path = Path(directory).resolve()

    # Load .gitignore patterns
    gitignore_spec = None
    gitignore_path = Path(directory) / ".gitignore"
    if gitignore_path.exists():
        with open(gitignore_path, "r") as f:
            patterns = f.read().splitlines()
            gitignore_spec = pathspec.PathSpec.from_lines(
                "gitwildmatch", patterns
            )

    def is_ignored(p):
        """Check if path should be ignored"""
        if gitignore_spec is None:
            return False

        # Get relative path from root directory
        try:
            rel_path = p.relative_to(path)
            # Check both the path and path with trailing slash for directories
            if gitignore_spec.match_file(str(rel_path)):
                return True
            if p.is_dir() and gitignore_spec.match_file(str(rel_path) + "/"):
                return True
        except ValueError:
            pass
        return False

    ext_counter = Counter()
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = Path(root) / file
            if is_ignored(file_path):
                continue
            ext = file_path.suffix.lower()
            if ext:
                ext_counter[ext] += 1

    if not ext_counter:
        return "Unknown"

    most_common_ext = ext_counter.most_common(1)[0][0]

    lang_map = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".java": "Java",
        ".cpp": "C++",
        ".cc": "C++",
        ".cxx": "C++",
        ".c": "C",
        ".h": "C",
        ".rb": "Ruby",
        ".php": "PHP",
        ".go": "Go",
        ".rs": "Rust",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".scala": "Scala",
    }

    return lang_map.get(most_common_ext, f"Unknown ({most_common_ext})")


def get_primary_framework(directory="."):
    """Determine the primary framework of the project in the given directory."""
    path = Path(directory).resolve()
    primary_lang = get_primary_language(directory)

    # Framework indicators based on common files
    framework_indicators = {
        "requirements.txt": "Python (pip)",
        "pyproject.toml": "Python (Poetry)",
        "setup.py": "Python (setuptools)",
        "Pipfile": "Python (Pipenv)",
        "package.json": "Node.js",
        "composer.json": "PHP (Composer)",
        "Gemfile": "Ruby (Bundler)",
        "Cargo.toml": "Rust (Cargo)",
        "go.mod": "Go (Go Modules)",
        "build.gradle": "Java (Gradle)",
        "pom.xml": "Java (Maven)",
        "app.py": "Flask" if primary_lang == "Python" else None,
        "manage.py": "Django" if primary_lang == "Python" else None,
    }

    # Check for framework-specific files
    for file, framework in framework_indicators.items():
        if framework and (path / file).exists():
            # For Node.js, check package.json for specific frameworks
            if file == "package.json":
                try:
                    with open(path / file, "r") as f:
                        data = json.load(f)
                        deps = data.get("dependencies", {})
                        dev_deps = data.get("devDependencies", {})
                        all_deps = {**deps, **dev_deps}
                        if "express" in all_deps:
                            return "Node.js (Express)"
                        elif "react" in all_deps:
                            return "Node.js (React)"
                        elif "vue" in all_deps:
                            return "Node.js (Vue)"
                        elif "angular" in all_deps:
                            return "Node.js (Angular)"
                        else:
                            return "Node.js"
                except (json.JSONDecodeError, FileNotFoundError):
                    pass
            # For Python, check requirements.txt or pyproject.toml for frameworks
            elif file in ["requirements.txt", "pyproject.toml"] and primary_lang == "Python":
                if file == "requirements.txt":
                    try:
                        with open(path / file, "r") as f:
                            content = f.read().lower()
                            if "django" in content:
                                return "Python (Django)"
                            elif "flask" in content:
                                return "Python (Flask)"
                            elif "fastapi" in content:
                                return "Python (FastAPI)"
                    except FileNotFoundError:
                        pass
                elif file == "pyproject.toml":
                    try:
                        import tomllib
                        with open(path / file, "rb") as f:
                            data = tomllib.load(f)
                            deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
                            if "django" in str(deps).lower():
                                return "Python (Django)"
                            elif "flask" in str(deps).lower():
                                return "Python (Flask)"
                            elif "fastapi" in str(deps).lower():
                                return "Python (FastAPI)"
                    except (ImportError, FileNotFoundError, KeyError):
                        pass
            else:
                return framework

    # If no specific framework detected, return based on language
    if primary_lang == "Python":
        return "Python (Generic)"
    elif primary_lang == "JavaScript":
        return "Node.js (Generic)"
    elif primary_lang == "TypeScript":
        return "Node.js (TypeScript)"
    else:
        return f"{primary_lang} (Generic)" if primary_lang != "Unknown" else "Unknown"


if __name__ == "__main__":
    print(get_tree_with_library())
    print(get_primary_language())
    print(get_primary_framework())

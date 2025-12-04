from pathlib import Path


def get_directory_tree(pwd: str) -> str:
    """Generate a string representation of the directory tree starting from pwd."""
    root = Path(pwd)
    lines = []

    def add_tree(path: Path, prefix: str = ""):
        lines.append(f"{prefix}{path.name}/")
        for child in sorted(path.iterdir()):
            if child.is_dir():
                add_tree(child, prefix + "  ")
            else:
                lines.append(f"{prefix}  {child.name}")

    add_tree(root)
    return "\n".join(lines)

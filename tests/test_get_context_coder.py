from pathlib import Path

from tree_format import format_tree


def get_tree_with_library(directory=".", max_depth=3):
    """Generate tree using tree-format library"""
    path = Path(directory)

    def build_tree(p, depth=0):
        if depth > max_depth:
            return None

        if p.is_file():
            return (p.name, [])

        children = []
        try:
            for child in sorted(p.iterdir()):
                if child.name.startswith("."):  # Skip hidden files
                    continue
                subtree = build_tree(child, depth + 1)
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


if __name__ == "__main__":
    print(get_tree_with_library())

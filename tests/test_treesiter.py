import ast

code = """
class A:
    def _method(self):
        pass

def _f(x):
    return x

x = 10
y, z = 20, 30
"""

tree = ast.parse(code)

classes = []
functions = []
variables = []

for node in tree.body:  # Only top-level objects
    if isinstance(node, ast.ClassDef):
        classes.append(node.name)

    elif isinstance(node, ast.FunctionDef):
        functions.append(node.name)

    elif isinstance(node, ast.Assign):
        # Handle "x = 10" or "y, z = (20, 30)"
        for target in node.targets:
            if isinstance(target, ast.Name):
                variables.append(target.id)
            elif isinstance(target, ast.Tuple):
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        variables.append(elt.id)

print("Classes:", classes)
print("Functions:", functions)
print("Variables:", variables)

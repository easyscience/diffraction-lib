#!/usr/bin/env python
"""Find all public methods/functions missing docstrings in src/."""
import ast
import os
import sys


def has_docstring(node):
    return (
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    )


def is_public(name):
    return not name.startswith('_')


results = []
src_root = sys.argv[1] if len(sys.argv) > 1 else 'src'
for root, dirs, files in os.walk(src_root):
    dirs[:] = sorted([d for d in dirs if d != '__pycache__' and d != '_vendored'])
    for f in sorted(files):
        if not f.endswith('.py'):
            continue
        path = os.path.join(root, f)
        try:
            with open(path) as fh:
                tree = ast.parse(fh.read())
        except Exception as e:
            print(f'Error parsing {path}: {e}')
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if is_public(node.name) and not has_docstring(node):
                    results.append(f'{path}:{node.lineno}: {node.name}')

for r in results:
    print(r)
print(f'Total: {len(results)} methods missing docstrings')


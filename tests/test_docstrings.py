import ast
from pathlib import Path

import pytest

FILES = sorted(Path("src").rglob("*.py"))


@pytest.mark.parametrize("path", FILES, ids=str)
def test_docstring_lines_do_not_end_with_period(path: Path):
    """Договорённость проекта: в докстрингах нет точек в конце строк"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            doc = ast.get_docstring(node, clean=False)
            if doc is None:
                continue
            for line in doc.splitlines():
                stripped = line.rstrip()
                assert not (stripped.endswith(".") and not stripped.endswith("..")), (
                    f"{path}: {getattr(node, 'name', 'module')}: {stripped!r}"
                )

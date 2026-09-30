from __future__ import annotations

import ast
import importlib.util
from pathlib import Path


SRC = Path(__file__).resolve().parents[2] / "src" / "steg"

FORBIDDEN = {
    "steg.text": ("steg.engine", "steg.historical", "steg.corpus", "steg.compiler"),
    "steg.engine": ("steg.historical", "steg.corpus", "steg.compiler"),
    "steg.historical": ("steg.corpus", "steg.compiler"),
}


def _module_name(path: Path) -> str:
    relative = path.relative_to(SRC.parent).with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _imports(path: Path) -> tuple[str, ...]:
    module = _module_name(path)
    package = module if path.name == "__init__.py" else module.rpartition(".")[0]
    result: list[str] = []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            target = "." * node.level + (node.module or "")
            if node.level:
                target = importlib.util.resolve_name(target, package)
            result.append(target)
    return tuple(result)


def test_subsystems_do_not_import_up_the_dependency_graph():
    violations: list[str] = []
    for path in SRC.rglob("*.py"):
        module = _module_name(path)
        subsystem = next(
            (prefix for prefix in FORBIDDEN if module == prefix or module.startswith(prefix + ".")),
            None,
        )
        if subsystem is None:
            continue
        for imported in _imports(path):
            for forbidden in FORBIDDEN[subsystem]:
                if imported == forbidden or imported.startswith(forbidden + "."):
                    violations.append(f"{module} -> {imported}")
    assert not violations, "forbidden subsystem imports:\n" + "\n".join(sorted(violations))

from __future__ import annotations

from pathlib import Path

import pytest

from code_explorer_mcp.utils.paths import (
    COMMON_IGNORED_DIRECTORIES,
    ProjectPathError,
    normalize_relative_path,
    resolve_project_path,
    to_relative_path,
)


@pytest.mark.parametrize(
    ("raw_path", "expected"),
    [
        (".", "."),
        ("src\\code_explorer_mcp\\server.py", "src/code_explorer_mcp/server.py"),
        ("./tests/fixtures", "tests/fixtures"),
        ("src//code_explorer_mcp///parsing", "src/code_explorer_mcp/parsing"),
    ],
)
def test_normalize_relative_path(raw_path: str, expected: str) -> None:
    assert normalize_relative_path(raw_path) == expected



def test_normalize_relative_path_rejects_parent_traversal() -> None:
    with pytest.raises(ProjectPathError):
        normalize_relative_path("../secrets.txt")



def test_resolve_project_path_keeps_path_inside_root(tmp_path: Path) -> None:
    nested = tmp_path / "src" / "module.py"
    nested.parent.mkdir(parents=True)
    nested.write_text("pass\n", encoding="utf-8")

    assert resolve_project_path(tmp_path, "src/module.py") == nested.resolve()



def test_resolve_project_path_rejects_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("x\n", encoding="utf-8")

    with pytest.raises(ProjectPathError):
        resolve_project_path(tmp_path, "../outside.txt")



def test_resolve_project_path_rejects_absolute_input_inside_root(tmp_path: Path) -> None:
    nested = tmp_path / "src" / "module.py"
    nested.parent.mkdir(parents=True)
    nested.write_text("pass\n", encoding="utf-8")

    with pytest.raises(ProjectPathError):
        resolve_project_path(tmp_path, str(nested))



def test_normalize_relative_path_rejects_absolute_input_inside_root(tmp_path: Path) -> None:
    nested = tmp_path / "src" / "module.py"
    nested.parent.mkdir(parents=True)
    nested.write_text("pass\n", encoding="utf-8")

    with pytest.raises(ProjectPathError):
        normalize_relative_path(str(nested))



def test_normalize_relative_path_rejects_parent_traversal_that_normalizes_inside_root() -> None:
    with pytest.raises(ProjectPathError):
        normalize_relative_path("src/../src")



def test_to_relative_path_normalizes_filesystem_path(tmp_path: Path) -> None:
    nested = tmp_path / "src" / "pkg" / "mod.py"
    nested.parent.mkdir(parents=True)
    nested.write_text("pass\n", encoding="utf-8")

    assert to_relative_path(tmp_path, nested) == "src/pkg/mod.py"



def test_normalize_relative_path_returns_project_root_for_none_like_inputs() -> None:
    assert normalize_relative_path("") == "."
    assert normalize_relative_path(".") == "."



def test_normalize_relative_path_supports_set_based_deduplication() -> None:
    assert sorted({normalize_relative_path(path) for path in ["b.py", "a.py", "./a.py"]}) == [
        "a.py",
        "b.py",
    ]



def test_common_ignored_directories_include_plan_defaults() -> None:
    assert COMMON_IGNORED_DIRECTORIES >= {
        ".venv",
        "venv",
        "env",
        "node_modules",
        ".mypy_cache",
        ".pytest_cache",
        "dist",
        "build",
        "coverage",
        "__pycache__",
    }

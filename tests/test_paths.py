from __future__ import annotations

from pathlib import Path

import pytest

from code_explorer_mcp.utils.paths import (
    COMMON_IGNORED_DIRECTORIES,
    ProjectPathError,
    normalize_relative_path,
    normalize_relative_paths,
    resolve_project_path,
    to_relative_path,
    validate_relative_input,
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



def test_validate_relative_input_rejects_absolute_input_inside_root(tmp_path: Path) -> None:
    nested = tmp_path / "src" / "module.py"
    nested.parent.mkdir(parents=True)
    nested.write_text("pass\n", encoding="utf-8")

    with pytest.raises(ProjectPathError):
        validate_relative_input(tmp_path, str(nested))



def test_validate_relative_input_rejects_parent_traversal_that_normalizes_inside_root(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    with pytest.raises(ProjectPathError):
        validate_relative_input(tmp_path, "src/../src")



def test_to_relative_path_normalizes_filesystem_path(tmp_path: Path) -> None:
    nested = tmp_path / "src" / "pkg" / "mod.py"
    nested.parent.mkdir(parents=True)
    nested.write_text("pass\n", encoding="utf-8")

    assert to_relative_path(tmp_path, nested) == "src/pkg/mod.py"



def test_validate_relative_input_returns_project_root_for_none(tmp_path: Path) -> None:
    assert validate_relative_input(tmp_path, None) == "."



def test_normalize_relative_paths_sorts_and_deduplicates() -> None:
    assert normalize_relative_paths(["b.py", "a.py", "./a.py"]) == ["a.py", "b.py"]



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

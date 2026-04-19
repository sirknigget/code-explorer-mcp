from __future__ import annotations

from pathlib import Path

import pytest

from code_explorer_mcp.utils.paths import (
    COMMON_IGNORED_DIRECTORIES,
    ProjectPathError,
    project_relative_path,
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
def test_project_relative_path_normalizes_relative_input(
    raw_path: str,
    expected: str,
    tmp_path: Path,
) -> None:
    assert project_relative_path(tmp_path, raw_path) == expected


def test_project_relative_path_rejects_parent_traversal(tmp_path: Path) -> None:
    with pytest.raises(ProjectPathError):
        project_relative_path(tmp_path, "../secrets.txt")


def test_project_relative_path_keeps_relative_path_inside_root(tmp_path: Path) -> None:
    nested = tmp_path / "src" / "module.py"
    nested.parent.mkdir(parents=True)
    nested.write_text("pass\n", encoding="utf-8")

    assert project_relative_path(tmp_path, "src/module.py") == "src/module.py"


def test_project_relative_path_normalizes_filesystem_path(tmp_path: Path) -> None:
    nested = tmp_path / "src" / "pkg" / "mod.py"
    nested.parent.mkdir(parents=True)
    nested.write_text("pass\n", encoding="utf-8")

    assert project_relative_path(tmp_path, nested) == "src/pkg/mod.py"


def test_project_relative_path_rejects_absolute_input_string_inside_root(
    tmp_path: Path,
) -> None:
    nested = tmp_path / "src" / "module.py"
    nested.parent.mkdir(parents=True)
    nested.write_text("pass\n", encoding="utf-8")

    with pytest.raises(ProjectPathError):
        project_relative_path(tmp_path, str(nested))


def test_project_relative_path_rejects_parent_traversal_that_normalizes_inside_root(
    tmp_path: Path,
) -> None:
    with pytest.raises(ProjectPathError):
        project_relative_path(tmp_path, "src/../src")


def test_project_relative_path_returns_project_root_for_none_like_inputs(
    tmp_path: Path,
) -> None:
    assert project_relative_path(tmp_path, "") == "."
    assert project_relative_path(tmp_path, ".") == "."
    assert project_relative_path(tmp_path) == "."


def test_project_relative_path_supports_set_based_deduplication(tmp_path: Path) -> None:
    assert sorted(
        {project_relative_path(tmp_path, path) for path in ["b.py", "a.py", "./a.py"]}
    ) == ["a.py", "b.py"]


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

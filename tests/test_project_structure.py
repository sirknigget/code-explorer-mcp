from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from code_explorer_mcp.models import GetProjectStructureRequest
from code_explorer_mcp.runtime_context import configure_runtime_root
from code_explorer_mcp.tool_project_structure import get_project_structure


def write_file(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")



def make_fixture_repo(tmp_path: Path) -> Path:
    write_file(
        tmp_path / ".gitignore",
        "ignored.py\nignored_dir/\ndocs/*.tmp\n",
    )
    write_file(tmp_path / "README.md", "# fixture\n")
    write_file(tmp_path / "ignored.py", "IGNORED = True\n")
    write_file(tmp_path / "src" / "app.py", "print('app')\n")
    write_file(tmp_path / "src" / "pkg" / "module.py", "VALUE = 1\n")
    write_file(tmp_path / "src" / "pkg" / "component.ts", "export const component = 1;\n")
    write_file(tmp_path / "src" / "pkg" / "view.tsx", "export const View = () => null;\n")
    write_file(tmp_path / "tests" / "test_app.py", "def test_app():\n    assert True\n")
    write_file(tmp_path / "docs" / "plans" / "PLAN.md", "plan\n")
    write_file(tmp_path / "docs" / "notes.tmp", "ignored temp\n")
    write_file(tmp_path / "ignored_dir" / "kept.ts", "export const hidden = true;\n")
    write_file(tmp_path / "node_modules" / "left-pad" / "index.js", "module.exports = {};\n")
    write_file(tmp_path / ".venv" / "bin" / "python", "")
    write_file(tmp_path / "build" / "generated.py", "print('generated')\n")
    write_file(tmp_path / "coverage" / "index.html", "coverage\n")
    write_file(tmp_path / "pkg" / "__pycache__" / "module.pyc", "")
    return tmp_path



def test_get_project_structure_returns_full_deterministic_tree_and_capabilities(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project_root = make_fixture_repo(tmp_path)
    monkeypatch.chdir(project_root)
    configure_runtime_root(project_root)

    result = get_project_structure(GetProjectStructureRequest())

    assert asdict(result) == {
        "root": ".",
        "subfolder": None,
        "pattern": None,
        "structure": (
            "docs/\n"
            "  plans/\n"
            "    PLAN.md\n"
            "src/\n"
            "  pkg/\n"
            "    component.ts\n"
            "    module.py\n"
            "    view.tsx\n"
            "  app.py\n"
            "tests/\n"
            "  test_app.py\n"
            ".gitignore\n"
            "README.md"
        ),
        "languages_present": ("python", "typescript"),
        "available_symbol_types_by_language": {
            "python": ("imports", "globals", "classes", "functions"),
            "typescript": (
                "imports",
                "globals",
                "classes",
                "functions",
                "interfaces",
                "type_aliases",
                "enums",
                "re_exports",
            ),
        },
        "error": None,
    }



def test_get_project_structure_filters_to_subfolder(tmp_path: Path, monkeypatch) -> None:
    project_root = make_fixture_repo(tmp_path)
    monkeypatch.chdir(project_root)
    configure_runtime_root(project_root)

    result = get_project_structure(GetProjectStructureRequest(subfolder="src/pkg"))

    assert asdict(result) == {
        "root": ".",
        "subfolder": "src/pkg",
        "pattern": None,
        "structure": "src/\n  pkg/\n    component.ts\n    module.py\n    view.tsx",
        "languages_present": ("python", "typescript"),
        "available_symbol_types_by_language": {
            "python": ("imports", "globals", "classes", "functions"),
            "typescript": (
                "imports",
                "globals",
                "classes",
                "functions",
                "interfaces",
                "type_aliases",
                "enums",
                "re_exports",
            ),
        },
        "error": None,
    }



def test_get_project_structure_filters_by_comma_separated_patterns(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project_root = make_fixture_repo(tmp_path)
    monkeypatch.chdir(project_root)
    configure_runtime_root(project_root)

    result = get_project_structure(GetProjectStructureRequest(pattern="*.py,*.ts"))

    assert asdict(result) == {
        "root": ".",
        "subfolder": None,
        "pattern": "*.py,*.ts",
        "structure": (
            "src/\n"
            "  pkg/\n"
            "    component.ts\n"
            "    module.py\n"
            "  app.py\n"
            "tests/\n"
            "  test_app.py"
        ),
        "languages_present": ("python", "typescript"),
        "available_symbol_types_by_language": {
            "python": ("imports", "globals", "classes", "functions"),
            "typescript": (
                "imports",
                "globals",
                "classes",
                "functions",
                "interfaces",
                "type_aliases",
                "enums",
                "re_exports",
            ),
        },
        "error": None,
    }



def test_get_project_structure_supports_folder_style_wildcards(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project_root = make_fixture_repo(tmp_path)
    monkeypatch.chdir(project_root)
    configure_runtime_root(project_root)

    result = get_project_structure(GetProjectStructureRequest(pattern="src/pkg/*"))

    assert asdict(result) == {
        "root": ".",
        "subfolder": None,
        "pattern": "src/pkg/*",
        "structure": "src/\n  pkg/\n    component.ts\n    module.py\n    view.tsx",
        "languages_present": ("python", "typescript"),
        "available_symbol_types_by_language": {
            "python": ("imports", "globals", "classes", "functions"),
            "typescript": (
                "imports",
                "globals",
                "classes",
                "functions",
                "interfaces",
                "type_aliases",
                "enums",
                "re_exports",
            ),
        },
        "error": None,
    }



def test_get_project_structure_ignores_common_generated_and_gitignored_paths(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project_root = make_fixture_repo(tmp_path)
    monkeypatch.chdir(project_root)
    configure_runtime_root(project_root)

    result = get_project_structure(GetProjectStructureRequest(pattern="*.py,*.js,*.tmp,*.ts"))

    assert asdict(result) == {
        "root": ".",
        "subfolder": None,
        "pattern": "*.py,*.js,*.tmp,*.ts",
        "structure": (
            "src/\n"
            "  pkg/\n"
            "    component.ts\n"
            "    module.py\n"
            "  app.py\n"
            "tests/\n"
            "  test_app.py"
        ),
        "languages_present": ("python", "typescript"),
        "available_symbol_types_by_language": {
            "python": ("imports", "globals", "classes", "functions"),
            "typescript": (
                "imports",
                "globals",
                "classes",
                "functions",
                "interfaces",
                "type_aliases",
                "enums",
                "re_exports",
            ),
        },
        "error": None,
    }


def test_get_project_structure_supports_negated_gitignore_patterns(
    tmp_path: Path,
    monkeypatch,
) -> None:
    write_file(
        tmp_path / ".gitignore",
        "ignored_dir/*\n!ignored_dir/kept.ts\n",
    )
    write_file(tmp_path / "ignored_dir" / "kept.ts", "export const kept = true;\n")
    write_file(
        tmp_path / "ignored_dir" / "hidden.py",
        "HIDDEN = True\n",
    )
    monkeypatch.chdir(tmp_path)
    configure_runtime_root(tmp_path)

    result = get_project_structure(GetProjectStructureRequest(pattern="*.py,*.ts"))

    assert asdict(result) == {
        "root": ".",
        "subfolder": None,
        "pattern": "*.py,*.ts",
        "structure": "ignored_dir/\n  kept.ts",
        "languages_present": ("typescript",),
        "available_symbol_types_by_language": {
            "typescript": (
                "imports",
                "globals",
                "classes",
                "functions",
                "interfaces",
                "type_aliases",
                "enums",
                "re_exports",
            ),
        },
        "error": None,
    }


def test_get_project_structure_honors_root_anchored_gitignore_patterns(
    tmp_path: Path,
    monkeypatch,
) -> None:
    write_file(tmp_path / ".gitignore", "/ignored.py\n")
    write_file(tmp_path / "ignored.py", "IGNORED = True\n")
    write_file(tmp_path / "nested" / "ignored.py", "NESTED = True\n")
    monkeypatch.chdir(tmp_path)
    configure_runtime_root(tmp_path)

    result = get_project_structure(GetProjectStructureRequest(pattern="*.py"))

    assert asdict(result) == {
        "root": ".",
        "subfolder": None,
        "pattern": "*.py",
        "structure": "nested/\n  ignored.py",
        "languages_present": ("python",),
        "available_symbol_types_by_language": {
            "python": ("imports", "globals", "classes", "functions"),
        },
        "error": None,
    }

from __future__ import annotations

import shutil
from dataclasses import asdict
from pathlib import Path

import pytest
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures"
PYTHON_FIXTURE = FIXTURES / "python_sample.py"
TYPESCRIPT_FIXTURE = FIXTURES / "typescript_sample.ts"


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
    (tmp_path / "tests" / "fixtures").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(PYTHON_FIXTURE, tmp_path / "tests" / "fixtures" / "python_sample.py")
    shutil.copyfile(
        TYPESCRIPT_FIXTURE,
        tmp_path / "tests" / "fixtures" / "typescript_sample.ts",
    )
    return tmp_path


@pytest.mark.asyncio
async def test_stdio_client_lists_tools_and_calls_each_tool(tmp_path: Path) -> None:
    project_root = make_fixture_repo(tmp_path)
    transport = StdioTransport(
        command="uv",
        args=[
            "run",
            "--project",
            str(REPO_ROOT),
            "python",
            "-m",
            "code_explorer_mcp",
        ],
        cwd=str(project_root),
        keep_alive=False,
    )
    client = Client(transport)

    async with client:
        tools = await client.list_tools()
        assert [tool.name for tool in tools] == [
            "get_project_structure",
            "parse_file",
            "fetch_symbol",
        ]

        project_structure = await client.call_tool(
            "get_project_structure",
            {
                "pattern": "*.py,*.ts",
            },
        )
        parse_file_result = await client.call_tool(
            "parse_file",
            {
                "filename": "tests/fixtures/python_sample.py",
                "content": {"functions": True, "classes": True},
            },
        )
        fetch_symbol_result = await client.call_tool(
            "fetch_symbol",
            {
                "filename": "tests/fixtures/typescript_sample.ts",
                "symbol": "MyInterface",
            },
        )

    assert asdict(project_structure.data) == {
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
            "  fixtures/\n"
            "    python_sample.py\n"
            "    typescript_sample.ts\n"
            "  test_app.py"
        ),
        "languages_present": ["python", "typescript"],
        "available_symbol_types_by_language": {
            "python": ["imports", "globals", "classes", "functions"],
            "typescript": [
                "imports",
                "globals",
                "classes",
                "functions",
                "interfaces",
                "type_aliases",
                "enums",
                "re_exports",
            ],
        },
        "error": None,
    }
    assert asdict(parse_file_result.data) == {
        "filename": "tests/fixtures/python_sample.py",
        "language": "python",
        "available_symbol_types": ["imports", "globals", "classes", "functions"],
        "sections": {
            "classes": [
                {
                    "name": "MyClass",
                    "members": [
                        {"name": "count"},
                        {"name": "label"},
                    ],
                    "methods": [
                        {"name": "my_method"},
                        {"name": "my_async_method"},
                    ],
                    "inner_classes": [
                        {
                            "name": "InnerClass",
                            "members": [{"name": "inner_value"}],
                            "methods": [],
                            "inner_classes": [],
                        }
                    ],
                }
            ],
            "functions": [{"name": "top_level_function"}],
        },
        "error": None,
    }
    assert asdict(fetch_symbol_result.data) == {
        "filename": "tests/fixtures/typescript_sample.ts",
        "language": "typescript",
        "symbol": "MyInterface",
        "symbol_type": "interfaces",
        "code": "export interface MyInterface {\n  id: string;\n}",
        "error": None,
    }

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

PYTHON_FIXTURE = Path("tests/fixtures/python_sample.py")
TYPESCRIPT_FIXTURE = Path("tests/fixtures/typescript_sample.ts")


def write_file(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_fixture_repo(tmp_path: Path, repo_root: Path) -> Path:
    write_file(
        tmp_path / ".gitignore",
        "ignored.py\nignored_dir/\ndocs/*.tmp\n",
    )
    write_file(tmp_path / "README.md", "# fixture\n")
    write_file(tmp_path / "ignored.py", "IGNORED = True\n")
    write_file(tmp_path / "src" / "app.py", "print('app')\n")
    write_file(tmp_path / "src" / "pkg" / "module.py", "VALUE = 1\n")
    write_file(
        tmp_path / "src" / "pkg" / "component.ts", "export const component = 1;\n"
    )
    write_file(
        tmp_path / "src" / "pkg" / "view.tsx", "export const View = () => null;\n"
    )
    write_file(tmp_path / "tests" / "test_app.py", "def test_app():\n    assert True\n")
    write_file(tmp_path / "docs" / "plans" / "PLAN.md", "plan\n")
    write_file(tmp_path / "docs" / "notes.tmp", "ignored temp\n")
    write_file(tmp_path / "ignored_dir" / "kept.ts", "export const hidden = true;\n")
    write_file(
        tmp_path / "node_modules" / "left-pad" / "index.js", "module.exports = {};\n"
    )
    write_file(tmp_path / ".venv" / "bin" / "python", "")
    write_file(tmp_path / "build" / "generated.py", "print('generated')\n")
    write_file(tmp_path / "coverage" / "index.html", "coverage\n")
    write_file(tmp_path / "pkg" / "__pycache__" / "module.pyc", "")
    (tmp_path / "tests" / "fixtures").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(
        repo_root / PYTHON_FIXTURE,
        tmp_path / "tests" / "fixtures" / "python_sample.py",
    )
    shutil.copyfile(
        repo_root / TYPESCRIPT_FIXTURE,
        tmp_path / "tests" / "fixtures" / "typescript_sample.ts",
    )
    return tmp_path


@pytest.mark.asyncio
async def test_stdio_client_lists_tools_and_calls_each_tool(
    tmp_path: Path,
    pytestconfig: pytest.Config,
) -> None:
    project_root = make_fixture_repo(tmp_path, pytestconfig.rootpath)
    transport = StdioTransport(
        command="uv",
        args=[
            "run",
            "--project",
            str(pytestconfig.rootpath),
            "code-explorer-mcp",
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
        python_parse_result = await client.call_tool(
            "parse_file",
            {
                "filename": "tests/fixtures/python_sample.py",
                "content": {"functions": True, "classes": True},
            },
        )
        typescript_parse_result = await client.call_tool(
            "parse_file",
            {
                "filename": "tests/fixtures/typescript_sample.ts",
            },
        )
        typescript_fetch_result = await client.call_tool(
            "fetch_symbol",
            {
                "filename": "tests/fixtures/typescript_sample.ts",
                "symbol": "MyInterface",
            },
        )
        python_fetch_result = await client.call_tool(
            "fetch_symbol",
            {
                "filename": "tests/fixtures/python_sample.py",
                "symbol": "MyClass.my_async_method",
            },
        )

    assert project_structure.data == {
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
        "languages": {
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
    }
    assert python_parse_result.data == {
        "sections": {
            "classes": ["MyClass", "MyClass.InnerClass"],
            "functions": ["top_level_function"],
        }
    }
    assert typescript_parse_result.data == {
        "sections": {
            "imports": [
                'import Thing, { Helper } from "./types"',
                'import * as Utils from "./utils"',
            ],
            "globals": ["TOP_LEVEL_CONST", "arrowFunction", "mutableValue"],
            "classes": ["MyClass", "MyClass.InnerClass"],
            "functions": ["namedFunction", "arrowFunction"],
            "interfaces": ["MyInterface"],
            "type_aliases": ["MyType"],
            "enums": ["MyEnum"],
            "re_exports": [
                'export { SharedThing } from "./shared"',
                'export * from "./everything"',
            ],
        }
    }
    assert typescript_fetch_result.data == {
        "symbol_type": "interfaces",
        "code": "export interface MyInterface {\n  id: string;\n}",
    }
    assert python_fetch_result.data == {
        "symbol_type": "classes",
        "code": "async def my_async_method(self) -> str:\n        return self.label",
    }

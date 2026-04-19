from __future__ import annotations

import asyncio
from dataclasses import FrozenInstanceError, asdict
from pathlib import Path

import pytest

from code_explorer_mcp.models import FetchSymbolRequest, ParseFileRequest, ToolPlaceholderError
from code_explorer_mcp.runtime_config import RuntimeConfig
from code_explorer_mcp.server import create_mcp_server
from code_explorer_mcp.tool_file_parse import parse_file
from code_explorer_mcp.tool_symbol_fetch import fetch_symbol

FIXTURES = Path(__file__).resolve().parent / "fixtures"
PYTHON_FIXTURE = FIXTURES / "python_sample.py"
TYPESCRIPT_FIXTURE = FIXTURES / "typescript_sample.ts"
PYTHON_FILENAME = "tests/fixtures/python_sample.py"
TYPESCRIPT_FILENAME = "tests/fixtures/typescript_sample.ts"
TEST_RUNTIME_CONFIG = RuntimeConfig(project_root=Path(__file__).resolve().parents[1])


def test_runtime_config_is_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        TEST_RUNTIME_CONFIG.project_root = Path("/tmp/other")


def test_parse_file_routes_python_and_typescript_by_extension() -> None:
    python_response = parse_file(
        ParseFileRequest(filename=PYTHON_FILENAME),
        runtime_config=TEST_RUNTIME_CONFIG,
    )
    typescript_response = parse_file(
        ParseFileRequest(
            filename=TYPESCRIPT_FILENAME,
            content={"interfaces": True, "functions": True, "imports": False},
        ),
        runtime_config=TEST_RUNTIME_CONFIG,
    )
    typescript_full_response = parse_file(
        ParseFileRequest(filename=TYPESCRIPT_FILENAME),
        runtime_config=TEST_RUNTIME_CONFIG,
    )

    assert asdict(python_response) == {
        "filename": PYTHON_FILENAME,
        "language": "python",
        "available_symbol_types": ("imports", "globals", "classes", "functions"),
        "sections": {
            "imports": [
                {"module": "os", "name": None, "alias": None},
                {"module": "typing", "name": "Any", "alias": "TypingAny"},
                {"module": ".helpers", "name": "helper", "alias": "local_helper"},
            ],
            "globals": [
                {"name": "MY_GLOBAL"},
                {"name": "OTHER_GLOBAL"},
            ],
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
    assert asdict(typescript_response) == {
        "filename": TYPESCRIPT_FILENAME,
        "language": "typescript",
        "available_symbol_types": (
            "imports",
            "globals",
            "classes",
            "functions",
            "interfaces",
            "type_aliases",
            "enums",
            "re_exports",
        ),
        "sections": {
            "functions": [
                {"name": "namedFunction", "syntax": "function"},
                {"name": "arrowFunction", "syntax": "arrow"},
            ],
            "interfaces": [{"name": "MyInterface"}],
        },
        "error": None,
    }
    assert asdict(typescript_full_response) == {
        "filename": TYPESCRIPT_FILENAME,
        "language": "typescript",
        "available_symbol_types": (
            "imports",
            "globals",
            "classes",
            "functions",
            "interfaces",
            "type_aliases",
            "enums",
            "re_exports",
        ),
        "sections": {
            "imports": [
                {"module": "./types", "default": "Thing", "namespace": None, "named": ["Helper"]},
                {"module": "./utils", "default": None, "namespace": "Utils", "named": []},
            ],
            "globals": [
                {"name": "TOP_LEVEL_CONST", "declaration_kind": "const"},
                {"name": "arrowFunction", "declaration_kind": "const"},
                {"name": "mutableValue", "declaration_kind": "let"},
            ],
            "classes": [
                {
                    "name": "MyClass",
                    "members": [{"name": "value"}],
                    "methods": [{"name": "run"}],
                    "accessors": [
                        {"name": "label", "kind": "getter"},
                        {"name": "label", "kind": "setter"},
                    ],
                    "inner_classes": [
                        {
                            "name": "InnerClass",
                            "members": [],
                            "methods": [{"name": "runInner"}],
                            "accessors": [],
                            "inner_classes": [],
                        }
                    ],
                }
            ],
            "functions": [
                {"name": "namedFunction", "syntax": "function"},
                {"name": "arrowFunction", "syntax": "arrow"},
            ],
            "interfaces": [{"name": "MyInterface"}],
            "type_aliases": [{"name": "MyType"}],
            "enums": [{"name": "MyEnum"}],
            "re_exports": [
                {"module": "./shared", "names": ["SharedThing"]},
                {"module": "./everything", "names": []},
            ],
        },
        "error": None,
    }


def test_parse_file_reports_invalid_request_for_unknown_symbol_type() -> None:
    response = parse_file(
        ParseFileRequest(
            filename=TYPESCRIPT_FILENAME,
            content={"decorators": True},
        ),
        runtime_config=TEST_RUNTIME_CONFIG,
    )

    assert response.error == ToolPlaceholderError(
        code="unsupported_request",
        message="Unknown symbol types requested: decorators",
    )


def test_parse_file_and_fetch_symbol_return_mcp_errors_for_file_read_failures(
    monkeypatch,
) -> None:
    original_read_text = Path.read_text

    def raise_read_error(path: Path, *, encoding: str = "utf-8") -> str:
        if path == PYTHON_FIXTURE:
            raise OSError("Permission denied while reading fixture")
        return original_read_text(path, encoding=encoding)

    monkeypatch.setattr(Path, "read_text", raise_read_error)

    parse_response = parse_file(
        ParseFileRequest(filename=PYTHON_FILENAME),
        runtime_config=TEST_RUNTIME_CONFIG,
    )
    fetch_response = fetch_symbol(
        FetchSymbolRequest(filename=PYTHON_FILENAME, symbol="MyClass"),
        runtime_config=TEST_RUNTIME_CONFIG,
    )

    assert asdict(parse_response) == {
        "filename": PYTHON_FILENAME,
        "language": "unknown",
        "available_symbol_types": (),
        "sections": {},
        "error": {
            "code": "file_read_error",
            "message": (
                "Failed to read file tests/fixtures/python_sample.py: "
                "Permission denied while reading fixture"
            ),
        },
    }
    assert asdict(fetch_response) == {
        "filename": PYTHON_FILENAME,
        "language": "unknown",
        "symbol": "MyClass",
        "symbol_type": None,
        "code": None,
        "error": {
            "code": "file_read_error",
            "message": (
                "Failed to read file tests/fixtures/python_sample.py: "
                "Permission denied while reading fixture"
            ),
        },
    }


def test_fetch_symbol_routes_python_and_typescript_by_extension() -> None:
    python_response = fetch_symbol(
        FetchSymbolRequest(filename=PYTHON_FILENAME, symbol="MyClass.my_async_method"),
        runtime_config=TEST_RUNTIME_CONFIG,
    )
    typescript_response = fetch_symbol(
        FetchSymbolRequest(filename=TYPESCRIPT_FILENAME, symbol="MyEnum"),
        runtime_config=TEST_RUNTIME_CONFIG,
    )

    assert asdict(python_response) == {
        "filename": PYTHON_FILENAME,
        "language": "python",
        "symbol": "MyClass.my_async_method",
        "symbol_type": "classes",
        "code": "async def my_async_method(self) -> str:\n        return self.label",
        "error": None,
    }
    assert asdict(typescript_response) == {
        "filename": TYPESCRIPT_FILENAME,
        "language": "typescript",
        "symbol": "MyEnum",
        "symbol_type": "enums",
        "code": 'export enum MyEnum {\n  Ready = "ready",\n}',
        "error": None,
    }


def test_fetch_symbol_returns_symbol_not_found_error() -> None:
    response = fetch_symbol(
        FetchSymbolRequest(filename=TYPESCRIPT_FILENAME, symbol="Missing"),
        runtime_config=TEST_RUNTIME_CONFIG,
    )

    assert asdict(response) == {
        "filename": TYPESCRIPT_FILENAME,
        "language": "typescript",
        "symbol": "Missing",
        "symbol_type": None,
        "code": None,
        "error": {
            "code": "symbol_not_found",
            "message": "Symbol not found: Missing",
        },
    }


def test_parse_and_fetch_use_supplied_runtime_config_instead_of_process_cwd(
    tmp_path: Path,
    monkeypatch,
) -> None:
    runtime_root = tmp_path / "runtime-root"
    runtime_root.mkdir()
    fixture_path = runtime_root / "sample.py"
    fixture_path.write_text("VALUE = 1\n", encoding="utf-8")
    runtime_config = RuntimeConfig(project_root=runtime_root)
    monkeypatch.chdir(tmp_path)

    parse_response = parse_file(
        ParseFileRequest(filename="sample.py"),
        runtime_config=runtime_config,
    )
    fetch_response = fetch_symbol(
        FetchSymbolRequest(filename="sample.py", symbol="VALUE"),
        runtime_config=runtime_config,
    )

    assert asdict(parse_response) == {
        "filename": "sample.py",
        "language": "python",
        "available_symbol_types": ("imports", "globals", "classes", "functions"),
        "sections": {
            "imports": [],
            "globals": [{"name": "VALUE"}],
            "classes": [],
            "functions": [],
        },
        "error": None,
    }
    assert asdict(fetch_response) == {
        "filename": "sample.py",
        "language": "python",
        "symbol": "VALUE",
        "symbol_type": "globals",
        "code": "VALUE = 1",
        "error": None,
    }


def test_servers_use_their_own_runtime_configs_without_global_mutation(tmp_path: Path) -> None:
    first_root = tmp_path / "first-root"
    second_root = tmp_path / "second-root"
    first_root.mkdir()
    second_root.mkdir()
    (first_root / "sample.py").write_text("FIRST = 1\n", encoding="utf-8")
    (second_root / "sample.py").write_text("SECOND = 2\n", encoding="utf-8")

    first_server = create_mcp_server(
        runtime_config=RuntimeConfig(project_root=first_root),
    )
    second_server = create_mcp_server(
        runtime_config=RuntimeConfig(project_root=second_root),
    )

    first_tool = asyncio.run(first_server.get_tool("parse_file"))
    second_tool = asyncio.run(second_server.get_tool("parse_file"))
    first_result = first_tool.fn(filename="sample.py")
    second_result = second_tool.fn(filename="sample.py")

    assert asdict(first_result) == {
        "filename": "sample.py",
        "language": "python",
        "available_symbol_types": ("imports", "globals", "classes", "functions"),
        "sections": {
            "imports": [],
            "globals": [{"name": "FIRST"}],
            "classes": [],
            "functions": [],
        },
        "error": None,
    }
    assert asdict(second_result) == {
        "filename": "sample.py",
        "language": "python",
        "available_symbol_types": ("imports", "globals", "classes", "functions"),
        "sections": {
            "imports": [],
            "globals": [{"name": "SECOND"}],
            "classes": [],
            "functions": [],
        },
        "error": None,
    }

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from code_explorer_mcp.models import FetchSymbolRequest, ParseFileRequest, ToolPlaceholderError
from code_explorer_mcp.tool_file_parse import parse_file
from code_explorer_mcp.tool_symbol_fetch import fetch_symbol

FIXTURES = Path(__file__).resolve().parent / "fixtures"
PYTHON_FIXTURE = FIXTURES / "python_sample.py"
TYPESCRIPT_FIXTURE = FIXTURES / "typescript_sample.ts"
PYTHON_FILENAME = "tests/fixtures/python_sample.py"
TYPESCRIPT_FILENAME = "tests/fixtures/typescript_sample.ts"


def test_parse_file_routes_python_and_typescript_by_extension() -> None:
    python_response = parse_file(ParseFileRequest(filename=str(PYTHON_FIXTURE)))
    typescript_response = parse_file(
        ParseFileRequest(
            filename=str(TYPESCRIPT_FIXTURE),
            content={"interfaces": True, "functions": True, "imports": False},
        )
    )
    typescript_full_response = parse_file(ParseFileRequest(filename=str(TYPESCRIPT_FIXTURE)))

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
            filename=str(TYPESCRIPT_FIXTURE),
            content={"decorators": True},
        )
    )

    assert response.error == ToolPlaceholderError(
        code="unsupported_request",
        message="Unknown symbol types requested: decorators",
    )


def test_fetch_symbol_routes_python_and_typescript_by_extension() -> None:
    python_response = fetch_symbol(
        FetchSymbolRequest(filename=str(PYTHON_FIXTURE), symbol="MyClass.my_async_method"),
    )
    typescript_response = fetch_symbol(
        FetchSymbolRequest(filename=str(TYPESCRIPT_FIXTURE), symbol="MyEnum"),
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
        FetchSymbolRequest(filename=str(TYPESCRIPT_FIXTURE), symbol="Missing"),
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

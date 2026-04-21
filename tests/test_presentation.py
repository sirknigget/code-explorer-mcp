from __future__ import annotations

from code_explorer_mcp.models import (
    FetchSymbolToolResponse,
    GetProjectStructureToolResponse,
    ParseFileToolResponse,
    ToolPlaceholderError,
)
from code_explorer_mcp.presentation import (
    present_fetch_symbol,
    present_parse_file,
    present_project_structure,
)


def test_present_project_structure_success() -> None:
    response = GetProjectStructureToolResponse(
        subfolder=None,
        pattern="*.py,*.ts",
        structure="src/\n  pkg/\n    component.ts\n    module.py\n  app.py",
        languages_present=("python", "typescript"),
        available_symbol_types_by_language={
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
    )

    assert present_project_structure(response) == {
        "structure": "src/\n  pkg/\n    component.ts\n    module.py\n  app.py",
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


def test_present_project_structure_trims_to_requested_subfolder() -> None:
    response = GetProjectStructureToolResponse(
        subfolder="src/pkg",
        structure="src/\n  pkg/\n    component.ts\n    module.py\n    view.tsx",
        available_symbol_types_by_language={
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
    )

    assert present_project_structure(response) == {
        "structure": "component.ts\nmodule.py\nview.tsx",
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


def test_present_project_structure_error_passthrough() -> None:
    response = GetProjectStructureToolResponse(
        error=ToolPlaceholderError(code="invalid_path", message="bad path"),
    )

    assert present_project_structure(response) == {
        "error": {"code": "invalid_path", "message": "bad path"}
    }


def test_present_parse_file_python_sections() -> None:
    response = ParseFileToolResponse(
        filename="tests/fixtures/python_sample.py",
        language="python",
        available_symbol_types=("imports", "globals", "classes", "functions"),
        sections={
            "imports": [
                {"module": "os", "name": None, "alias": None},
                {"module": "typing", "name": "Any", "alias": "TypingAny"},
                {"module": ".helpers", "name": "helper", "alias": "local_helper"},
            ],
            "globals": [{"name": "MY_GLOBAL"}, {"name": "OTHER_GLOBAL"}],
            "classes": [
                {
                    "name": "MyClass",
                    "members": [{"name": "count"}, {"name": "label"}],
                    "methods": [{"name": "my_method"}],
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
    )

    assert present_parse_file(response) == {
        "sections": {
            "imports": [
                "import os",
                "from typing import Any as TypingAny",
                "from .helpers import helper as local_helper",
            ],
            "globals": ["MY_GLOBAL", "OTHER_GLOBAL"],
            "classes": ["MyClass", "MyClass.InnerClass"],
            "functions": ["top_level_function"],
        }
    }


def test_present_parse_file_typescript_sections() -> None:
    response = ParseFileToolResponse(
        filename="tests/fixtures/typescript_sample.ts",
        language="typescript",
        available_symbol_types=(
            "imports",
            "globals",
            "classes",
            "functions",
            "interfaces",
            "type_aliases",
            "enums",
            "re_exports",
        ),
        sections={
            "imports": [
                {
                    "module": "./types",
                    "default": "Thing",
                    "namespace": None,
                    "named": ["Helper"],
                },
                {
                    "module": "./utils",
                    "default": None,
                    "namespace": "Utils",
                    "named": [],
                },
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
                    "accessors": [{"name": "label", "kind": "getter"}],
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
    )

    assert present_parse_file(response) == {
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


def test_present_parse_file_omits_empty_sections() -> None:
    response = ParseFileToolResponse(
        filename="sample.ts",
        language="typescript",
        available_symbol_types=("functions", "interfaces"),
        sections={"functions": [], "interfaces": [{"name": "MyInterface"}]},
    )

    assert present_parse_file(response) == {"sections": {"interfaces": ["MyInterface"]}}


def test_present_parse_file_error_passthrough() -> None:
    response = ParseFileToolResponse(
        filename="sample.py",
        language="unknown",
        available_symbol_types=(),
        error=ToolPlaceholderError(code="unsupported_request", message="bad request"),
    )

    assert present_parse_file(response) == {
        "error": {"code": "unsupported_request", "message": "bad request"}
    }


def test_present_fetch_symbol_success_with_symbol_type() -> None:
    response = FetchSymbolToolResponse(
        filename="tests/fixtures/typescript_sample.ts",
        language="typescript",
        symbol="MyInterface",
        symbol_type="interfaces",
        code="export interface MyInterface {\n  id: string;\n}",
    )

    assert present_fetch_symbol(response) == {
        "code": "export interface MyInterface {\n  id: string;\n}",
        "symbol_type": "interfaces",
    }


def test_present_fetch_symbol_success_without_symbol_type() -> None:
    response = FetchSymbolToolResponse(
        filename="tests/fixtures/typescript_sample.ts",
        language="typescript",
        symbol="Missing",
        symbol_type=None,
        code="some code",
    )

    assert present_fetch_symbol(response) == {"code": "some code"}


def test_present_fetch_symbol_error_passthrough() -> None:
    response = FetchSymbolToolResponse(
        filename="sample.ts",
        language="typescript",
        symbol="Missing",
        symbol_type=None,
        code=None,
        error=ToolPlaceholderError(code="symbol_not_found", message="missing"),
    )

    assert present_fetch_symbol(response) == {
        "error": {"code": "symbol_not_found", "message": "missing"}
    }

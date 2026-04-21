from __future__ import annotations

from typing import Any, Mapping

from code_explorer_mcp.models import (
    ErrorPayload,
    FetchSymbolPayload,
    FetchSymbolSuccessPayload,
    FetchSymbolToolResponse,
    GetProjectStructurePayload,
    GetProjectStructureToolResponse,
    GetProjectStructureSuccessPayload,
    ParseFilePayload,
    ParseFileSectionsPayload,
    ParseFileToolResponse,
    ToolPlaceholderError,
)


def present_project_structure(
    response: GetProjectStructureToolResponse,
) -> GetProjectStructurePayload:
    if response.error is not None:
        return _error_payload(response.error)

    payload: GetProjectStructureSuccessPayload = {
        "structure": _trim_structure_to_subfolder(
            response.structure,
            response.subfolder,
        ),
        "languages": {
            language: list(symbol_types)
            for language, symbol_types in response.available_symbol_types_by_language.items()
        },
    }
    return payload


def present_parse_file(response: ParseFileToolResponse) -> ParseFilePayload:
    if response.error is not None:
        return _error_payload(response.error)

    sections: ParseFileSectionsPayload = {}
    for section_name, section_value in response.sections.items():
        presented_section = _present_section(section_name, section_value)
        if presented_section:
            sections[section_name] = presented_section
    return sections


def present_fetch_symbol(response: FetchSymbolToolResponse) -> FetchSymbolPayload:
    if response.error is not None:
        return _error_payload(response.error)

    payload: FetchSymbolSuccessPayload = {"code": response.code}
    if response.symbol_type is not None:
        payload["symbol_type"] = response.symbol_type
    return payload


def _error_payload(error: ToolPlaceholderError) -> ErrorPayload:
    return {
        "error": {
            "code": error.code,
            "message": error.message,
        }
    }


def _trim_structure_to_subfolder(structure: str, subfolder: str | None) -> str:
    if not structure or subfolder is None:
        return structure

    lines = structure.splitlines()
    subtree_segments = subfolder.split("/")
    stack: list[str] = []
    subtree_depth: int | None = None
    subtree_line_index: int | None = None

    for index, line in enumerate(lines):
        indent = _line_indent_level(line)
        stack = stack[:indent]
        stripped = line.strip()
        stack.append(stripped.removesuffix("/"))
        if stripped.endswith("/") and stack == subtree_segments:
            subtree_depth = indent
            subtree_line_index = index
            break

    if subtree_depth is None or subtree_line_index is None:
        return structure

    trimmed_lines: list[str] = []
    base_indent = subtree_depth + 1
    for line in lines[subtree_line_index + 1 :]:
        indent = _line_indent_level(line)
        if indent <= subtree_depth:
            break
        trimmed_lines.append(f"{'  ' * (indent - base_indent)}{line.lstrip()}")
    return "\n".join(trimmed_lines)


def _line_indent_level(line: str) -> int:
    return (len(line) - len(line.lstrip(" "))) // 2


def _present_section(section_name: str, section_value: object) -> list[str]:
    items = _as_mapping_list(section_value)

    if section_name == "imports":
        return [_present_import(item) for item in items]
    if section_name == "classes":
        return _flatten_class_names(items)
    if section_name == "re_exports":
        return [_present_re_export(item) for item in items]
    if section_name in {
        "globals",
        "functions",
        "interfaces",
        "type_aliases",
        "enums",
    }:
        return [str(item["name"]) for item in items]
    return []


def _as_mapping_list(value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _present_import(item: Mapping[str, Any]) -> str:
    if "default" in item or "namespace" in item or "named" in item:
        return _present_typescript_import(item)
    return _present_python_import(item)


def _present_python_import(item: Mapping[str, Any]) -> str:
    module = str(item["module"])
    name = item.get("name")
    alias = item.get("alias")

    if name is None:
        statement = f"import {module}"
    else:
        statement = f"from {module} import {name}"

    if alias:
        statement += f" as {alias}"
    return statement


def _present_typescript_import(item: Mapping[str, Any]) -> str:
    module = str(item["module"])
    parts: list[str] = []
    default_name = item.get("default")
    namespace = item.get("namespace")
    named = item.get("named")

    if default_name:
        parts.append(str(default_name))
    if namespace:
        parts.append(f"* as {namespace}")
    if isinstance(named, list) and named:
        parts.append("{ " + ", ".join(str(name) for name in named) + " }")

    if not parts:
        return f'import "{module}"'
    return f'import {", ".join(parts)} from "{module}"'


def _present_re_export(item: Mapping[str, Any]) -> str:
    module = str(item["module"])
    names = item.get("names")
    if isinstance(names, list) and names:
        rendered_names = ", ".join(str(name) for name in names)
        return f'export {{ {rendered_names} }} from "{module}"'
    return f'export * from "{module}"'


def _flatten_class_names(
    classes: list[Mapping[str, Any]],
    *,
    prefix: str = "",
) -> list[str]:
    names: list[str] = []
    for class_item in classes:
        class_name = str(class_item["name"])
        qualified_name = class_name if not prefix else f"{prefix}.{class_name}"
        names.append(qualified_name)
        inner_classes = _as_mapping_list(class_item.get("inner_classes", []))
        names.extend(_flatten_class_names(inner_classes, prefix=qualified_name))
    return names

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from code_explorer_mcp.models import FetchSymbolRequest, ParseFileRequest
from code_explorer_mcp.runtime_config import RuntimeConfig
from code_explorer_mcp.tool_file_parse import parse_file
from code_explorer_mcp.tool_symbol_fetch import fetch_symbol


def test_parse_file_rejects_absolute_filename_with_structured_error(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime-root"
    runtime_root.mkdir()
    fixture_path = runtime_root / "sample.py"
    fixture_path.write_text("VALUE = 1\n", encoding="utf-8")
    runtime_config = RuntimeConfig.from_project_root(runtime_root)

    response = parse_file(
        ParseFileRequest(filename=str(fixture_path)),
        runtime_config=runtime_config,
    )

    assert asdict(response) == {
        "filename": str(fixture_path),
        "language": "unknown",
        "available_symbol_types": (),
        "sections": {},
        "error": {
            "code": "invalid_path",
            "message": f"Path must be a simple relative path from the project root: {fixture_path}",
        },
    }


def test_fetch_symbol_rejects_normalized_parent_traversal_with_structured_error(
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "runtime-root"
    runtime_root.mkdir()
    src_dir = runtime_root / "src"
    src_dir.mkdir()
    fixture_path = src_dir / "sample.py"
    fixture_path.write_text("VALUE = 1\n", encoding="utf-8")
    runtime_config = RuntimeConfig.from_project_root(runtime_root)

    response = fetch_symbol(
        FetchSymbolRequest(filename="src/../src/sample.py", symbol="VALUE"),
        runtime_config=runtime_config,
    )

    assert asdict(response) == {
        "filename": "src/../src/sample.py",
        "language": "unknown",
        "symbol": "VALUE",
        "symbol_type": None,
        "code": None,
        "error": {
            "code": "invalid_path",
            "message": "Path must be a simple relative path from the project root: "
            "src/../src/sample.py",
        },
    }

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from code_explorer_mcp import main as main_module


class StubServer:
    def __init__(self) -> None:
        self.did_run = False

    def run(self) -> None:
        self.did_run = True


def test_main_defaults_to_current_working_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub_server = StubServer()
    create_server_calls: list[Path] = []
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(main_module, "create_mcp_server", lambda *, runtime_config: stub_server)
    monkeypatch.setattr(
        main_module.RuntimeConfig,
        "from_project_root",
        classmethod(
            lambda cls, project_root: create_server_calls.append(Path(project_root))
            or main_module.RuntimeConfig(project_root=Path(project_root).resolve())
        ),
    )
    monkeypatch.setattr(sys, "argv", ["code-explorer-mcp"])

    main_module.main()

    assert create_server_calls == [tmp_path.resolve()]
    assert Path.cwd() == tmp_path.resolve()
    assert stub_server.did_run is True


@pytest.mark.parametrize("argv", [[]])
def test_main_accepts_explicit_empty_argv(
    argv: list[str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub_server = StubServer()
    create_server_calls: list[Path] = []
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(main_module, "create_mcp_server", lambda *, runtime_config: stub_server)
    monkeypatch.setattr(
        main_module.RuntimeConfig,
        "from_project_root",
        classmethod(
            lambda cls, project_root: create_server_calls.append(Path(project_root))
            or main_module.RuntimeConfig(project_root=Path(project_root).resolve())
        ),
    )

    main_module.main(argv)

    assert create_server_calls == [tmp_path.resolve()]
    assert Path.cwd() == tmp_path.resolve()
    assert stub_server.did_run is True


def test_main_uses_path_argument_for_project_root_without_changing_cwd(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    start_directory = tmp_path / "start"
    project_root = tmp_path / "project"
    start_directory.mkdir()
    project_root.mkdir()

    stub_server = StubServer()
    create_server_calls: list[Path] = []
    monkeypatch.chdir(start_directory)
    monkeypatch.setattr(
        main_module,
        "create_mcp_server",
        lambda *, runtime_config: create_server_calls.append(runtime_config.project_root)
        or stub_server,
    )

    main_module.main(["--path", str(project_root)])

    assert create_server_calls == [project_root.resolve()]
    assert Path.cwd() == start_directory.resolve()
    assert stub_server.did_run is True


def test_main_rejects_non_directory_path(tmp_path: Path) -> None:
    missing_directory = tmp_path / "missing"

    with pytest.raises(SystemExit, match="2"):
        main_module.main(["--path", str(missing_directory)])

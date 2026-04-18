from __future__ import annotations

from pathlib import Path

_RUNTIME_ROOT: Path | None = None


def configure_runtime_root(path: str | Path) -> None:
    global _RUNTIME_ROOT
    _RUNTIME_ROOT = Path(path).resolve()


def get_runtime_root() -> Path:
    if _RUNTIME_ROOT is None:
        raise RuntimeError("Runtime root has not been configured")
    return _RUNTIME_ROOT

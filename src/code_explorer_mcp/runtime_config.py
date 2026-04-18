from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    project_root: Path

    @classmethod
    def from_project_root(cls, project_root: str | Path) -> "RuntimeConfig":
        return cls(project_root=Path(project_root).resolve())

from __future__ import annotations

from pathlib import Path
from typing import Iterable

COMMON_IGNORED_DIRECTORIES: frozenset[str] = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "env",
        "node_modules",
        ".mypy_cache",
        ".pytest_cache",
        "dist",
        "build",
        "coverage",
        "__pycache__",
    }
)


class ProjectPathError(ValueError):
    """Raised when a path is invalid for the current project root."""



def normalize_relative_path(path: str | Path) -> str:
    """Return a normalized project-relative path using '/' separators.

    The returned value never starts with './' and never contains '.' or '..'
    path segments. The project root itself is represented as '.'.
    """
    raw_path = str(path).replace("\\", "/").strip()
    if raw_path in {"", "."}:
        return "."

    parts: list[str] = []
    for part in raw_path.split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            raise ProjectPathError(f"Path escapes project root: {path}")
        parts.append(part)

    return "/".join(parts) if parts else "."



def resolve_project_path(project_root: Path, path: str | Path | None = None) -> Path:
    """Resolve a user-provided path within project_root.

    Returns the canonical filesystem path and rejects traversal outside the
    project root.
    """
    root = project_root.resolve()
    candidate = root if path is None else (root / str(path)).resolve()

    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ProjectPathError(f"Path escapes project root: {path}") from exc

    return candidate



def to_relative_path(project_root: Path, path: str | Path) -> str:
    """Convert a filesystem path to a normalized project-relative path."""
    root = project_root.resolve()
    resolved = resolve_project_path(root, path)
    return normalize_relative_path(resolved.relative_to(root))



def validate_relative_input(project_root: Path, path: str | Path | None) -> str:
    """Validate a user-facing relative path argument and normalize it.

    The input must remain inside project_root after resolution.
    """
    if path is None:
        return "."

    resolved = resolve_project_path(project_root, path)
    return normalize_relative_path(resolved.relative_to(project_root.resolve()))



def normalize_relative_paths(paths: Iterable[str | Path]) -> list[str]:
    """Normalize and sort a collection of relative paths deterministically."""
    return sorted({normalize_relative_path(path) for path in paths})

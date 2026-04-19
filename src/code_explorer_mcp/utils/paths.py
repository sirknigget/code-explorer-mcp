from __future__ import annotations

from pathlib import Path, PurePosixPath

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


def project_relative_path(project_root: Path, path: str | Path | None = None) -> str:
    """Return a canonical path relative to project_root."""
    root = project_root.resolve()
    if path is None:
        return "."

    if isinstance(path, Path):
        resolved = path.resolve()
        try:
            relative_path = resolved.relative_to(root)
        except ValueError as exc:
            raise ProjectPathError(
                f"Path must be inside the project root: {path}"
            ) from exc
        return _normalize_relative_path(relative_path)

    candidate = (root / _normalize_relative_path(path)).resolve()
    try:
        relative_path = candidate.relative_to(root)
    except ValueError as exc:
        raise ProjectPathError(
            f"Path must be a simple relative path from the project root: {path}",
        ) from exc

    return _normalize_relative_path(relative_path)


def _normalize_relative_path(path: str | Path) -> str:
    raw_path = str(path).replace("\\", "/").strip()
    if raw_path in {"", "."}:
        return "."

    pure_path = PurePosixPath(raw_path)
    if pure_path.is_absolute():
        raise ProjectPathError(
            f"Path must be a simple relative path from the project root: {path}",
        )

    parts: list[str] = []
    for part in pure_path.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            raise ProjectPathError(
                f"Path must be a simple relative path from the project root: {path}",
            )
        parts.append(part)

    return "/".join(parts) if parts else "."

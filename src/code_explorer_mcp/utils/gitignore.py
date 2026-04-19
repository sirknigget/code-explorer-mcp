from __future__ import annotations

from pathlib import Path

from pathspec import PathSpec

from code_explorer_mcp.utils.paths import normalize_relative_path


class GitIgnoreMatcher:
    def __init__(self, spec: PathSpec) -> None:
        self._spec = spec

    def matches_directory(self, relative_path: str) -> bool:
        normalized = normalize_relative_path(relative_path)
        if normalized == ".":
            return False
        return self._spec.match_file(f"{normalized}/")

    def matches_file(self, relative_path: str) -> bool:
        normalized = normalize_relative_path(relative_path)
        if normalized == ".":
            return False
        return self._spec.match_file(normalized)


EMPTY_GITIGNORE_MATCHER = GitIgnoreMatcher(PathSpec.from_lines("gitwildmatch", ()))


def load_gitignore_matcher(project_root: Path) -> GitIgnoreMatcher:
    gitignore_path = project_root / ".gitignore"
    if not gitignore_path.exists():
        return EMPTY_GITIGNORE_MATCHER

    lines = gitignore_path.read_text(encoding="utf-8").splitlines()
    return GitIgnoreMatcher(PathSpec.from_lines("gitwildmatch", lines))

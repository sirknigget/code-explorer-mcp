from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path

from code_explorer_mcp.models import GetProjectStructureRequest, GetProjectStructureResponse
from code_explorer_mcp.parser_registry import DEFAULT_PARSER_REGISTRY
from code_explorer_mcp.runtime_context import get_runtime_root
from code_explorer_mcp.utils.paths import (
    COMMON_IGNORED_DIRECTORIES,
    normalize_relative_path,
    to_relative_path,
    validate_relative_input,
)
from code_explorer_mcp.utils.tree import build_tree, render_tree


@dataclass(frozen=True, slots=True)
class IgnorePattern:
    pattern: str
    negated: bool
    directory_only: bool
    anchored: bool


@dataclass(frozen=True, slots=True)
class IgnoreRules:
    patterns: tuple[IgnorePattern, ...]

    def matches_directory(self, relative_path: str) -> bool:
        return self._is_ignored(normalize_relative_path(relative_path), is_directory=True)

    def matches_file(self, relative_path: str) -> bool:
        return self._is_ignored(normalize_relative_path(relative_path), is_directory=False)

    def _is_ignored(self, relative_path: str, *, is_directory: bool) -> bool:
        ignored = False
        for pattern in self.patterns:
            if not _matches_gitignore_pattern(pattern, relative_path, is_directory=is_directory):
                continue
            ignored = not pattern.negated
        return ignored


def get_project_structure(
    request: GetProjectStructureRequest,
) -> GetProjectStructureResponse:
    project_root = get_runtime_root()
    normalized_subfolder = (
        None
        if request.subfolder is None
        else validate_relative_input(project_root, request.subfolder)
    )
    start_path = project_root / normalized_subfolder if normalized_subfolder else project_root
    ignore_rules = load_ignore_rules(project_root)
    patterns = parse_patterns(request.pattern)

    matched_paths = discover_project_files(
        project_root=project_root,
        start_path=start_path,
        ignore_rules=ignore_rules,
        patterns=patterns,
    )
    structure = render_tree(build_tree(matched_paths)) if matched_paths else ""
    capabilities = DEFAULT_PARSER_REGISTRY.capabilities_for_paths(matched_paths)

    return GetProjectStructureResponse(
        root=".",
        subfolder=normalized_subfolder,
        pattern=request.pattern,
        structure=structure,
        languages_present=tuple(capabilities),
        available_symbol_types_by_language={
            language: tuple(symbol_types)
            for language, symbol_types in capabilities.items()
        },
    )


def load_ignore_rules(project_root: Path) -> IgnoreRules:
    gitignore_path = project_root / ".gitignore"
    if not gitignore_path.exists():
        return IgnoreRules(patterns=())

    patterns: list[IgnorePattern] = []
    for raw_line in gitignore_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        negated = stripped.startswith("!")
        raw_pattern = stripped[1:] if negated else stripped
        if not raw_pattern:
            continue

        directory_only = raw_pattern.endswith("/")
        anchored = raw_pattern.startswith("/")
        normalized_pattern = normalize_relative_path(raw_pattern.strip("/"))
        patterns.append(
            IgnorePattern(
                pattern=normalized_pattern,
                negated=negated,
                directory_only=directory_only,
                anchored=anchored,
            )
        )

    return IgnoreRules(patterns=tuple(patterns))


def parse_patterns(raw_pattern: str | None) -> tuple[str, ...]:
    if raw_pattern is None:
        return ()

    return tuple(part.strip() for part in raw_pattern.split(",") if part.strip())


def discover_project_files(
    *,
    project_root: Path,
    start_path: Path,
    ignore_rules: IgnoreRules,
    patterns: tuple[str, ...],
) -> list[str]:
    matched_paths: list[str] = []

    for current_root, dirnames, filenames in start_path.walk(top_down=True):
        relative_root = to_relative_path(project_root, current_root)
        kept_directories: list[str] = []
        for dirname in sorted(dirnames):
            if dirname in COMMON_IGNORED_DIRECTORIES:
                continue
            relative_directory = dirname if relative_root == "." else f"{relative_root}/{dirname}"
            if ignore_rules.matches_directory(relative_directory):
                continue
            kept_directories.append(dirname)
        dirnames[:] = kept_directories

        for filename in sorted(filenames):
            relative_file = filename if relative_root == "." else f"{relative_root}/{filename}"
            normalized_file = normalize_relative_path(relative_file)
            if ignore_rules.matches_file(normalized_file):
                continue
            if patterns and not any(fnmatchcase(normalized_file, pattern) for pattern in patterns):
                continue
            matched_paths.append(normalized_file)

    return matched_paths


def _matches_gitignore_pattern(
    pattern: IgnorePattern,
    relative_path: str,
    *,
    is_directory: bool,
) -> bool:
    if pattern.directory_only and not is_directory:
        return False

    candidate_paths = _candidate_paths(pattern, relative_path)
    return any(fnmatchcase(candidate_path, pattern.pattern) for candidate_path in candidate_paths)


def _candidate_paths(pattern: IgnorePattern, relative_path: str) -> tuple[str, ...]:
    if pattern.anchored:
        return (relative_path,)

    if "/" in pattern.pattern:
        parts = relative_path.split("/")
        return tuple("/".join(parts[index:]) for index in range(len(parts)))

    basename = relative_path.rsplit("/", maxsplit=1)[-1]
    return (basename,)

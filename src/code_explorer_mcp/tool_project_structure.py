from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path

from code_explorer_mcp.models import GetProjectStructureRequest, GetProjectStructureResponse
from code_explorer_mcp.runtime_context import get_runtime_root
from code_explorer_mcp.parser_registry import DEFAULT_PARSER_REGISTRY
from code_explorer_mcp.utils.paths import (
    COMMON_IGNORED_DIRECTORIES,
    normalize_relative_path,
    to_relative_path,
)
from code_explorer_mcp.utils.tree import build_tree, render_tree


@dataclass(frozen=True, slots=True)
class IgnoreRules:
    patterns: tuple[str, ...]

    def matches_directory(self, relative_path: str) -> bool:
        normalized = normalize_relative_path(relative_path)
        return any(
            _matches_gitignore_pattern(pattern, normalized, is_directory=True)
            for pattern in self.patterns
        )

    def matches_file(self, relative_path: str) -> bool:
        normalized = normalize_relative_path(relative_path)
        return any(
            _matches_gitignore_pattern(pattern, normalized, is_directory=False)
            for pattern in self.patterns
        )


def get_project_structure(
    request: GetProjectStructureRequest,
) -> GetProjectStructureResponse:
    project_root = get_runtime_root()
    normalized_subfolder = (
        None
        if request.subfolder is None
        else normalize_relative_path(request.subfolder)
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

    patterns: list[str] = []
    for raw_line in gitignore_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("!"):
            continue
        patterns.append(stripped)

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


def _matches_gitignore_pattern(pattern: str, relative_path: str, *, is_directory: bool) -> bool:
    normalized_pattern = normalize_relative_path(pattern.lstrip("/"))

    if pattern.endswith("/"):
        directory_pattern = normalize_relative_path(pattern.rstrip("/").lstrip("/"))
        if not is_directory:
            return relative_path.startswith(f"{directory_pattern}/")
        return relative_path == directory_pattern or relative_path.startswith(
            f"{directory_pattern}/"
        )

    if "/" in normalized_pattern:
        return fnmatchcase(relative_path, normalized_pattern)

    basename = relative_path.rsplit("/", maxsplit=1)[-1]
    path_segments = relative_path.split("/")
    return fnmatchcase(basename, normalized_pattern) or any(
        fnmatchcase(segment, normalized_pattern) for segment in path_segments[:-1]
    )

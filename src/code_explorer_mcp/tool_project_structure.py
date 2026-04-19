from __future__ import annotations

from fnmatch import fnmatchcase
from pathlib import Path

from code_explorer_mcp.models import GetProjectStructureRequest, GetProjectStructureResponse
from code_explorer_mcp.parser_registry import DEFAULT_PARSER_REGISTRY
from code_explorer_mcp.runtime_context import get_runtime_root
from code_explorer_mcp.utils.gitignore import GitIgnoreMatcher, load_gitignore_matcher
from code_explorer_mcp.utils.paths import (
    COMMON_IGNORED_DIRECTORIES,
    normalize_relative_path,
    to_relative_path,
    validate_relative_input,
)
from code_explorer_mcp.utils.tree import build_tree, render_tree


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
    gitignore_matcher = load_gitignore_matcher(project_root)
    patterns = parse_patterns(request.pattern)

    matched_paths = discover_project_files(
        project_root=project_root,
        start_path=start_path,
        gitignore_matcher=gitignore_matcher,
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


def parse_patterns(raw_pattern: str | None) -> tuple[str, ...]:
    if raw_pattern is None:
        return ()

    return tuple(part.strip() for part in raw_pattern.split(",") if part.strip())


def discover_project_files(
    *,
    project_root: Path,
    start_path: Path,
    gitignore_matcher: GitIgnoreMatcher,
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
            if gitignore_matcher.matches_directory(relative_directory):
                continue
            kept_directories.append(dirname)
        dirnames[:] = kept_directories

        for filename in sorted(filenames):
            relative_file = filename if relative_root == "." else f"{relative_root}/{filename}"
            normalized_file = normalize_relative_path(relative_file)
            if gitignore_matcher.matches_file(normalized_file):
                continue
            if patterns and not any(fnmatchcase(normalized_file, pattern) for pattern in patterns):
                continue
            matched_paths.append(normalized_file)

    return matched_paths

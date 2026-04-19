from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(slots=True)
class TreeNode:
    """A nested directory node for deterministic structure rendering."""

    directories: dict[str, TreeNode] = field(default_factory=dict)
    files: list[str] = field(default_factory=list)


def build_tree(relative_paths: Iterable[str]) -> TreeNode:
    """Build a nested tree from project-relative file and directory paths."""
    root = TreeNode()

    for raw_path in relative_paths:
        if raw_path == ".":
            continue

        is_directory = raw_path.endswith("/")
        parts = raw_path.rstrip("/").split("/")
        node = root

        for part in parts[:-1]:
            node = node.directories.setdefault(part, TreeNode())

        leaf = parts[-1]
        if is_directory:
            node.directories.setdefault(leaf, TreeNode())
            continue

        if leaf not in node.files:
            node.files.append(leaf)

    return root


def render_tree(tree: TreeNode) -> str:
    """Render a readable project structure string from a TreeNode."""
    lines: list[str] = []
    _render_node(tree, depth=0, lines=lines)
    return "\n".join(lines)


def _render_node(node: TreeNode, *, depth: int, lines: list[str]) -> None:
    indent = "  " * depth

    for directory_name in sorted(node.directories):
        lines.append(f"{indent}{directory_name}/")
        _render_node(node.directories[directory_name], depth=depth + 1, lines=lines)

    for file_name in sorted(node.files):
        lines.append(f"{indent}{file_name}")

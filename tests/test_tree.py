from __future__ import annotations

from code_explorer_mcp.utils.tree import build_tree, render_tree



def test_build_and_render_tree_produces_nested_non_redundant_output() -> None:
    tree = build_tree(
        [
            "src/code_explorer_mcp/parsing/base.py",
            "src/code_explorer_mcp/parsing/common.py",
            "src/code_explorer_mcp/utils/paths.py",
            "tests/test_tree.py",
        ]
    )

    assert render_tree(tree) == (
        "src/\n"
        "  code_explorer_mcp/\n"
        "    parsing/\n"
        "      base.py\n"
        "      common.py\n"
        "    utils/\n"
        "      paths.py\n"
        "tests/\n"
        "  test_tree.py"
    )



def test_build_tree_keeps_directories_before_files() -> None:
    tree = build_tree(["src/file.py", "src/nested/inner.py", "src/another.py"])

    assert render_tree(tree) == (
        "src/\n"
        "  nested/\n"
        "    inner.py\n"
        "  another.py\n"
        "  file.py"
    )



def test_build_tree_accepts_explicit_directory_entries() -> None:
    tree = build_tree(["docs/", "docs/plans/PLAN.md"])

    assert render_tree(tree) == "docs/\n  plans/\n    PLAN.md"

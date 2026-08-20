from pathlib import Path


def test_architecture_guide_exists() -> None:
    assert Path("docs/architecture.md").exists()
    assert "## Component Boundaries" in Path("docs/architecture.md").read_text()


def test_readme_documents_eval_command() -> None:
    assert "PYTHONPATH=src uv run python -m openrouter_demo.evals" in Path("README.md").read_text()


def test_failure_tree_and_quickstart_paths_resolve() -> None:
    assert Path("docs/failure-tree.md").exists()
    assert Path("docs/specs/failure-tree.md").exists() is False

    tree = Path("docs/failure-tree.md").read_text()
    assert "## High-level tree" in tree
    for category_term in (
        "malformed request",
        "invalid API key",
        "request validation error",
        "provider unavailable",
        "routing constraint too narrow",
        "timeout",
        "token metadata missing",
        "fallback hidden from user",
    ):
        assert category_term in tree

    assert "PYTHONPATH=src uv run python -m openrouter_demo.evals" in Path(
        "docs/specs/quickstart.md"
    ).read_text()

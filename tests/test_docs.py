from pathlib import Path


def test_architecture_guide_exists() -> None:
    assert Path("docs/architecture.md").exists()
    assert "## Component Boundaries" in Path("docs/architecture.md").read_text()


def test_readme_documents_eval_command() -> None:
    assert "PYTHONPATH=src uv run python -m openrouter_demo.evals" in Path("README.md").read_text()

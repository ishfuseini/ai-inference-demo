from pathlib import Path


def test_architecture_guide_exists() -> None:
    assert Path("docs/architecture.md").exists()
    assert "## Component Boundaries" in Path("docs/architecture.md").read_text()

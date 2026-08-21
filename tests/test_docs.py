from pathlib import Path


def test_architecture_guide_exists() -> None:
    assert Path("docs/architecture.md").exists()
    assert "## Component Boundaries" in Path("docs/architecture.md").read_text()


def test_readme_documents_eval_command() -> None:
    assert "PYTHONPATH=src uv run python -m openrouter_demo.evals" in Path("README.md").read_text()


def test_dockerfile_copies_static_assets() -> None:
    text = Path("Dockerfile").read_text()
    assert "COPY assets/ ./assets/" in text


def test_dockerfile_installs_dependencies_at_build_time() -> None:
    text = Path("Dockerfile").read_text()
    assert "COPY pyproject.toml uv.lock ./" in text
    assert "RUN uv sync --frozen --no-dev" in text
    assert 'CMD ["uv", "run", "--no-sync", "python", "app.py"]' in text


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


def test_focused_test_coverage() -> None:
    assert Path("tests/test_client.py").exists()
    assert "def test_stream_401_raises_auth_error" in Path("tests/test_client.py").read_text()
    assert Path("tests/test_ui.py").exists()

    assert Path("tests/test_routing.py").exists()
    assert (
        "def test_strategies_dict_contains_three_selectable_strategies"
        in Path("tests/test_routing.py").read_text()
    )

    assert Path("tests/test_telemetry.py").exists()
    assert (
        "def test_telemetry_evidence_round_trip_preserves_sentinels"
        in Path("tests/test_telemetry.py").read_text()
    )
    assert Path("tests/test_sqlite_store.py").exists()

    assert Path("tests/test_evals.py").exists()
    assert "def test_score_response_passes_and_fails" in Path("tests/test_evals.py").read_text()

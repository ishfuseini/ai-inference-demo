from pathlib import Path

from openrouter_demo.config import (
    LANGFUSE_BASE_URL,
    LANGFUSE_PUBLIC_KEY,
    LANGFUSE_SECRET_KEY,
    OPENROUTER_API_KEY,
    load_config,
)


def test_missing_openrouter_key_is_reported() -> None:
    config = load_config({})
    assert config.openrouter_ready is False
    assert config.missing_required == (OPENROUTER_API_KEY,)
    assert config.langfuse_ready is False


def test_openrouter_key_sets_required_ready() -> None:
    config = load_config({OPENROUTER_API_KEY: "test-key"})
    assert config.openrouter_ready is True
    assert config.missing_required == ()
    assert config.langfuse_ready is False


def test_load_config_reads_os_environ(monkeypatch) -> None:
    monkeypatch.setenv(OPENROUTER_API_KEY, "test-key")
    assert load_config().openrouter_ready is True


def test_langfuse_ready_requires_all_optional_vars() -> None:
    incomplete = load_config({LANGFUSE_PUBLIC_KEY: "pk"})
    complete = load_config({
        LANGFUSE_PUBLIC_KEY: "pk",
        LANGFUSE_SECRET_KEY: "sk",
        LANGFUSE_BASE_URL: "https://cloud.langfuse.com",
    })
    assert incomplete.langfuse_ready is False
    assert complete.langfuse_ready is True


def test_env_example_is_only_empty_assignments() -> None:
    text = Path(".env.example").read_text()
    for name in (OPENROUTER_API_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL):
        assert f"{name}=" in text
    assignments = [line for line in text.splitlines() if line and not line.startswith("#")]
    assert all(line.endswith("=") for line in assignments)


def test_readme_documents_setup() -> None:
    text = Path("README.md").read_text()
    for expected in (
        "uv sync",
        "uv run python app.py",
        OPENROUTER_API_KEY,
        LANGFUSE_PUBLIC_KEY,
        LANGFUSE_SECRET_KEY,
        LANGFUSE_BASE_URL,
    ):
        assert expected in text

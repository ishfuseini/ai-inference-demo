from pathlib import Path

SOURCE_PATHS = [Path("app.py"), *Path("src/openrouter_demo").glob("*.py")]


def implementation_text() -> str:
    # sqlite_store.py is the Phase 4 persistence layer and intentionally imports
    # sqlite3; the "no database" guard covers the core inference modules only.
    paths = [p for p in SOURCE_PATHS if p.name != "sqlite_store.py"]
    return "\n".join(path.read_text() for path in paths)


def test_phase1_has_no_fastapi_product_layer() -> None:
    assert "from fastapi" not in implementation_text()
    assert "import fastapi" not in implementation_text()


def test_phase1_has_no_database_imports() -> None:
    text = implementation_text()
    for forbidden in ("sqlite3", "sqlalchemy", "psycopg", "asyncpg"):
        assert forbidden not in text


def test_phase1_keeps_langfuse_tracing_isolated_to_telemetry() -> None:
    telemetry_path = Path("src/openrouter_demo/telemetry.py")
    assert "get_client(" in telemetry_path.read_text()
    core_modules = [
        Path("app.py"),
        Path("src/openrouter_demo/client.py"),
        Path("src/openrouter_demo/models.py"),
        Path("src/openrouter_demo/scenarios.py"),
        Path("src/openrouter_demo/ui.py"),
        Path("src/openrouter_demo/evals.py"),
    ]
    for path in core_modules:
        assert "get_client(" not in path.read_text()

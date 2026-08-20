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


def test_phase1_does_not_create_langfuse_traces() -> None:
    text = implementation_text()
    for forbidden in ("get_client(", ".trace(", ".start_span(", ".generation("):
        assert forbidden not in text

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

OPENROUTER_API_KEY = "OPENROUTER_API_KEY"
LANGFUSE_PUBLIC_KEY = "LANGFUSE_PUBLIC_KEY"
LANGFUSE_SECRET_KEY = "LANGFUSE_SECRET_KEY"
LANGFUSE_BASE_URL = "LANGFUSE_BASE_URL"

REQUIRED_ENV_VARS = (OPENROUTER_API_KEY,)
LANGFUSE_ENV_VARS = (LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL)


@dataclass(frozen=True)
class AppConfig:
    openrouter_ready: bool
    langfuse_ready: bool
    missing_required: tuple[str, ...]
    missing_langfuse: tuple[str, ...]


def _missing(environ: Mapping[str, str], names: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(name for name in names if not environ.get(name))


def load_config(environ: Mapping[str, str] | None = None) -> AppConfig:
    if environ is None:
        load_dotenv(dotenv_path=Path.cwd() / ".env", override=False)
    source = os.environ if environ is None else environ
    missing_required = _missing(source, REQUIRED_ENV_VARS)
    missing_langfuse = _missing(source, LANGFUSE_ENV_VARS)
    return AppConfig(
        openrouter_ready=not missing_required,
        langfuse_ready=not missing_langfuse,
        missing_required=missing_required,
        missing_langfuse=missing_langfuse,
    )

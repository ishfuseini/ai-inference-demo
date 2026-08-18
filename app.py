import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from nicegui import ui

from openrouter_demo.config import load_config
from openrouter_demo.ui import build_app


def main() -> None:
    config = load_config()
    build_app(config)
    ui.run(title="OpenRouter Production Inference Lab", reload=False)


if __name__ == "__main__":
    main()

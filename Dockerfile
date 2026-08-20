FROM python:3.12-slim

# Install uv (fast Python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies first (cached layer)
COPY pyproject.toml ./
RUN uv sync --no-dev

# Copy application code
COPY src/ ./src/
COPY app.py ./
COPY evals/ ./evals/
COPY data/ ./data/

# Expose the port NiceGUI listens on
EXPOSE 8080

# Run the app — uv runs in the project's virtualenv automatically
CMD ["uv", "run", "python", "app.py"]

FROM python:3.12-slim

# Install uv (fast Python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies first (cached layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy application code
COPY src/ ./src/
COPY app.py ./
COPY evals/ ./evals/
COPY data/ ./data/
COPY assets/ ./assets/

# Expose the port NiceGUI listens on
EXPOSE 8080

# Run the app without syncing at startup; dependencies are installed in the image.
CMD ["uv", "run", "--no-sync", "python", "app.py"]

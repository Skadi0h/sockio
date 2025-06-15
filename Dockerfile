FROM python:3.13.5-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY ./sockio/ /app/sockio/

WORKDIR /app

COPY uv.lock pyproject.toml ./
RUN uv sync --frozen --no-cache

CMD ["/app/.venv/bin/fastapi", "run", "/app/sockio/main.py", "--port", "80", "--host", "0.0.0.0", "--reload"]
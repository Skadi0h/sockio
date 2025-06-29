FROM python:3.13.5-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY ./sockio/ /app/sockio/
WORKDIR /app
COPY uv.lock pyproject.toml ./
RUN apt-get update && apt install -y libuv1-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/* \
    && uv sync --frozen --no-cache
# build stage
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app/

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=README.md,target=README.md \
    uv sync --frozen --no-install-project --no-dev --extra tqdm

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
COPY . /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --extra tqdm

# production stage
FROM python:3.13-slim AS production

LABEL maintainer="erik.o.gabrielsson@sectra.com"

COPY --from=builder --chown=app:app /app /app
ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT ["sectra_dpat_downloader"]
CMD ["--help"]
FROM registry.access.redhat.com/ubi9/python-312
COPY --from=ghcr.io/astral-sh/uv:0.5.2@sha256:ab5cd8c7946ae6a359a9aea9073b5effd311d40a65310380caae938a1abf55da /uv /bin/uv

ENV \
    # use venv from ubi image
    UV_PROJECT_ENVIRONMENT=$APP_ROOT \
    # compile bytecode for faster startup
    UV_COMPILE_BYTECODE="true" \
    # disable uv cache. it doesn't make sense in a container
    UV_NO_CACHE=true

COPY --chown=1001 . .
# Test lock file is up to date
RUN uv lock --locked
RUN uv sync --frozen --no-group dev

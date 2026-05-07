FROM registry.access.redhat.com/ubi9/python-312@sha256:21739f35258f21e23a7e02e79c763f2a69e605416fedd54b6ec9c5ef68fd1f43 AS prod
COPY --from=ghcr.io/astral-sh/uv:0.11.11@sha256:798712e57f879c5393777cbda2bb309b29fcdeb0532129d4b1c3125c5385975a /uv /bin/uv
COPY LICENSE /licenses/

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

FROM prod AS test
# Install test dependencies
RUN uv sync --frozen

# Run tests
RUN make test

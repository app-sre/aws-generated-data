FROM registry.access.redhat.com/ubi9/python-312@sha256:a370a755dd6a9a5697876e7a5ecb390c3cc528142e222116ad5fab6d71ba35f9 AS prod
COPY --from=ghcr.io/astral-sh/uv:0.11.3@sha256:90bbb3c16635e9627f49eec6539f956d70746c409209041800a0280b93152823 /uv /bin/uv
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

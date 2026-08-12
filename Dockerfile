FROM registry.access.redhat.com/ubi10/python-314-minimal@sha256:35ade79ab473652e587063682ef69cb92387327dc01315c53f83e597932477aa AS prod
COPY --from=ghcr.io/astral-sh/uv:0.12.3@sha256:2d890623d310b57771ce840f0da5eed5fc6d657da05ffaa45d82797b53fa3abc /uv /bin/uv
COPY LICENSE /licenses/

ENV \
    # use venv from ubi image
    UV_PROJECT_ENVIRONMENT=$APP_ROOT \
    # compile bytecode for faster startup
    UV_COMPILE_BYTECODE="true" \
    # disable uv cache. it doesn't make sense in a container
    UV_NO_CACHE=true

USER root
RUN microdnf install -y make
USER 1001

COPY --chown=1001 . .
# Test lock file is up to date
RUN uv lock --locked
RUN uv sync --frozen --no-group dev

FROM prod AS test
# Install test dependencies
RUN uv sync --frozen

# Run tests
RUN make test

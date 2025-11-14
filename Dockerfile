FROM registry.access.redhat.com/ubi9/python-312@sha256:c798f775119a2e9c676fcfdb14a0d24cb562790b1a4c1bb49d0966aec039c673 AS prod
COPY --from=ghcr.io/astral-sh/uv:0.9.9@sha256:f6e3549ed287fee0ddde2460a2a74a2d74366f84b04aaa34c1f19fec40da8652 /uv /bin/uv
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

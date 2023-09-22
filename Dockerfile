FROM registry.access.redhat.com/ubi9/python-311
USER 1000
ENV NO_COLOR 1

RUN pip install --upgrade pip && \
    pip install poetry==1.2.2
COPY --chown=1000 . .
RUN poetry install

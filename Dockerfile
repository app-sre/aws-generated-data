FROM registry.access.redhat.com/ubi9/python-311
USER 1000
ENV NO_COLOR 1
ENV VIRTUAL_ENV /opt/app-root

RUN pip install --upgrade pip && \
    pip install poetry==1.8.3
COPY --chown=1000 . .
RUN poetry config virtualenvs.create false
RUN poetry install --no-ansi

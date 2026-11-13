FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
RUN pip install . && useradd --create-home hub
COPY alembic.ini ./
COPY migrations ./migrations

FROM base AS test
RUN pip install '.[test]'
COPY tests ./tests
COPY scripts ./scripts
USER hub
CMD ["pytest", "-q", "-p", "no:cacheprovider"]

FROM base AS runtime
USER hub
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

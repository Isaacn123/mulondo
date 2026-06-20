FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BACKEND_PORT=8008

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app

EXPOSE 8008

CMD sh -c 'if [ "${STORAGE_BACKEND:-json}" = "database" ]; then \
  echo "STORAGE_BACKEND=database — waiting for MySQL at ${MYSQL_HOST:-mysql}:${MYSQL_PORT:-3306}..."; \
  python -m app.scripts.wait_for_mysql && alembic upgrade head; \
else \
  echo "STORAGE_BACKEND=${STORAGE_BACKEND:-json} — skipping MySQL migrations"; \
fi && exec uvicorn app.main:app --host 0.0.0.0 --port ${BACKEND_PORT}'

FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BACKEND_PORT=8008

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app

EXPOSE 8008

CMD sh -c 'if [ "${STORAGE_BACKEND:-json}" = "database" ]; then \
  echo "STORAGE_BACKEND=database — waiting for MySQL at ${MYSQL_HOST:-mysql}:${MYSQL_PORT:-3306}..."; \
  python -m app.scripts.wait_for_mysql; \
  if ! alembic upgrade head; then \
    echo "WARNING: alembic upgrade head failed — starting API anyway. Fix migrations and restart."; \
  fi; \
else \
  echo "STORAGE_BACKEND=${STORAGE_BACKEND:-json} — skipping MySQL migrations"; \
fi; exec uvicorn app.main:app --host 0.0.0.0 --port ${BACKEND_PORT}'

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

CMD sh -c 'ready=0; for i in $(seq 1 60); do python -c "import os,pymysql; pymysql.connect(host=os.getenv(\"MYSQL_HOST\",\"mysql\"), user=os.environ[\"MYSQL_USER\"], password=os.environ[\"MYSQL_PASSWORD\"], database=os.environ[\"MYSQL_DATABASE\"], connect_timeout=3)" && ready=1 && break; echo "Waiting for MySQL ($i/60)..."; sleep 2; done; if [ "$ready" != 1 ]; then echo "MySQL not available"; exit 1; fi; alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${BACKEND_PORT}'

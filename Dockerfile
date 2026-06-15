FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.lock.txt /app/backend/requirements.lock.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.lock.txt

COPY backend /app/backend

ENV YFINANCE_CACHE_PATH=/tmp/yfinance_cache
ENV PYTHONUNBUFFERED=1

WORKDIR /app/backend
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

FROM python:3.12-slim

# Security: run as non-root
RUN addgroup --system app && adduser --system --ingroup app app

RUN apt-get update && apt-get install -y --no-install-recommends sqlite3 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install deps first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY app/ ./app/
COPY seed_estoque.py . 

# Logs directory
RUN mkdir -p /app/logs && chown -R app:app /app
RUN mkdir -p /app/logs /app/data && chown -R app:app /app

USER app

EXPOSE 4000

# Gunicorn + Uvicorn workers for production concurrency
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "4000", \
     "--workers", "4", \
     "--loop", "uvloop", \
     "--reload", \
     "--access-log"]

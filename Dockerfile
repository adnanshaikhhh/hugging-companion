# Hugging Companion — single-container deploy
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps for cryptography-free stack (kept minimal)
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src ./src
COPY frontend ./frontend
COPY .env.example ./.env.example

# The app listens on 8000 (matches uvicorn below)
EXPOSE 8000

# Healthcheck for Railway / Fly
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/health || exit 1

# Data directory for SQLite (use a volume in production)
RUN mkdir -p /app/data
ENV HUGGING_COMPANION_DB_URL=sqlite:////app/data/hugging_companion.db

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
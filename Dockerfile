FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition
COPY pyproject.toml .

# Install dependencies using pip
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    "fastapi[standard]>=0.115.0" \
    "pydantic>=2.9.0" \
    "pydantic-settings>=2.5.0" \
    "sqlalchemy>=2.0.30" \
    "pgvector>=0.3.0" \
    "asyncpg>=0.29.0" \
    "psycopg2-binary>=2.9.9" \
    "httpx>=0.27.0" \
    "pypdf>=4.3.0" \
    "redis>=5.0.8" \
    "celery>=5.4.0" \
    "prometheus-client>=0.20.0" \
    "rapidfuzz>=3.9.0" \
    "alembic>=1.13.2" \
    "tiktoken>=0.7.0" \
    "langfuse>=2.0.0"

# Copy application source code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

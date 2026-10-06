# ClauseGuard — Contract Review API

ClauseGuard is a production-grade contract review and intelligence API designed to analyze legal and procurement agreements, extract risky clauses with structured schemas and verbatim citations, and answer queries via Server-Sent Events (SSE) streaming.

Every answer and extraction is grounded with verified source text and tested with an evaluation harness from Day 1 to ensure zero hallucination and continuous regression safety.

---

## FreeLLM Providers Configuration

ClauseGuard is built to run entirely on high-performance free-tier providers from **[FreeLLM.net](https://freellm.net/)** with automatic resilience and failover:

| Role | Provider | Model ID | Tier Limits (FreeLLM.net) | Capabilities |
|---|---|---|---|---|
| **Primary** | **Google Gemini** (Google AI Studio) | `gemini-flash-lite-latest` | 15 RPM / 1,500 RPD | 1M token context window, structured JSON mode, zero-cost development tier |
| **Fallback** | **Groq** | `openai/gpt-oss-120b` *(or `llama-3.3-70b-versatile`)* | 30 RPM / 1,000+ RPD | Ultra-low latency LPU inference, OpenAI-compatible format, zero-cost development tier |

### Setting Up API Credentials

1. **Google Gemini (Primary)**:
   - Generate your free API key at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey).
   - Add to `.env`: `GEMINI_API_KEY=your_key_here`
2. **Groq (Fallback)**:
   - Generate your free API key at [console.groq.com/keys](https://console.groq.com/keys).
   - Add to `.env`: `GROQ_API_KEY=your_key_here`
3. **Langfuse (Observability - Optional / Cloud)**:
   - Sign up at [cloud.langfuse.com](https://cloud.langfuse.com) (or Japan region `jp.cloud.langfuse.com`).
   - Add credentials to `.env`:
     ```env
     LANGFUSE_HOST=https://jp.cloud.langfuse.com
     LANGFUSE_PUBLIC_KEY=pk-lf-your_public_key
     LANGFUSE_SECRET_KEY=sk-lf-your_secret_key
     ```

---

## Core Architecture

ClauseGuard follows a strict layered FastAPI architecture:

```text
clauseguard/
├── app/
│   ├── api/v1/routes/        # Request validation (Pydantic), HTTP responses & SSE only
│   ├── services/             # Pure business logic, AI orchestration, citation verification
│   ├── repositories/         # SQLAlchemy 2.0 query layer extending BaseRepository
│   ├── models/               # SQLAlchemy ORM (Mapped/mapped_column) with pgvector
│   ├── pipeline/             # PDF parser, section detector, chunker, repair loop, citation verifier
│   ├── retrieval/            # Hybrid search with Reciprocal Rank Fusion (RRF) & embeddings
│   ├── llm/                  # Providers (Gemini & Groq), cost tracker, token pricing
│   │   └── resilience/       # Exponential backoff, 3-state CircuitBreaker, token-bucket RateLimiter
│   ├── observability/        # Prometheus metrics (/metrics), Langfuse v4 tracing, run ledger
│   └── workers/              # Celery background tasks for async document ingestion
├── eval/                     # CUAD golden samples & hallucination eval harness
├── migrations/               # Alembic versioned database migrations
└── tests/                    # Comprehensive unit tests
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Health check & active FreeLLM provider status |
| `POST` | `/api/v1/documents` | Upload contract PDF for asynchronous parsing, chunking & vector embedding |
| `GET` | `/api/v1/documents/{id}` | Check ingestion status and total parsed chunk count |
| `POST` | `/api/v1/extract` | Structured clause extraction (parallelized with concurrency cap & repair loop) |
| `GET` | `/api/v1/extractions/{id}` | Fetch historical extraction results with verified citations |
| `POST` | `/api/v1/ask` | Grounded contract Q&A streaming via Server-Sent Events (SSE) with verified citations |
| `GET` | `/metrics` | Prometheus metrics scrape endpoint |

---

## Quickstart & Local Development

### 1. Environment Configuration

Clone the repository and copy the environment template:

```bash
cp .env.example .env
```

Ensure your `.env` contains your `GEMINI_API_KEY` and database credentials:

```env
DATABASE_URL=postgresql+asyncpg://clauseguard:clauseguard_secret@localhost:5433/clauseguard
DATABASE_SYNC_URL=postgresql+psycopg2://clauseguard:clauseguard_secret@localhost:5433/clauseguard
REDIS_URL=redis://localhost:6379/0
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL_ID=gemini-flash-lite-latest
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL_ID=openai/gpt-oss-120b
```

### 2. Start PostgreSQL & Redis

Start the containerized `pgvector` database and Redis broker:

```bash
make db-up
# Alternatively: docker compose up -d postgres redis
```

Run database migrations:

```bash
make migrate
# Alternatively: .venv/bin/alembic upgrade head
```

### 3. Start the Celery Worker

In a dedicated terminal tab, start the Celery worker for background ingestion:

```bash
make worker
# Alternatively: .venv/bin/celery -A app.workers.celery_app worker --loglevel=info --pool=solo
```

> **Note for macOS / Apple Silicon:** The worker is configured with `--pool=solo` to prevent billiard multiprocessing spawn incompatibilities on macOS.

### 4. Start the FastAPI API Server

In another terminal tab, start the Uvicorn development server:

```bash
make server
# Alternatively: .venv/bin/uvicorn app.main:app --port 8000 --reload
```

Interactive Swagger documentation is available at: **`http://localhost:8000/docs`**

---

## Developer Command Reference (`Makefile`)

| Command | Action |
|---|---|
| `make db-up` | Starts Postgres (with pgvector) and Redis containers |
| `make db-down` | Stops and removes local Docker containers |
| `make migrate` | Applies pending Alembic database migrations |
| `make migrate-check` | Displays current migration revision |
| `make server` | Starts Uvicorn development server on port `8000` |
| `make worker` | Starts Celery ingestion worker (solo pool) |
| `make test` | Runs the entire unit test and eval suite |

---

## Full Stack Docker Compose

To boot all services (API, Celery Worker, Postgres, Redis, Prometheus) in containers:

```bash
docker compose up --build -d
```

- **API Server:** `http://localhost:8000`
- **Prometheus Dashboard:** `http://localhost:9090`
- **Postgres (pgvector):** `localhost:5432` *(in Docker network)*
- **Redis Broker:** `localhost:6379`

---

## Running Tests & Evaluation Harness

ClauseGuard includes an automated evaluation suite testing extraction recall, citation groundedness, and prompt injection defense against golden CUAD contract samples:

```bash
make test
# or: pytest tests/ eval/ -v
```

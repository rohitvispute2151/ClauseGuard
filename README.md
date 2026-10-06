# ClauseGuard — Contract Review API

ClauseGuard is a production-grade contract review API designed to analyze legal and procurement agreements, extract risky clauses with structured schemas and verbatim citations, and answer questions via streaming (SSE).

Answers cite exact source text and are programmatically verified. Built with an evaluation harness from Day 1 to ensure zero hallucination and continuous regression testing.

---

## FreeLLM Providers Configuration

Instead of proprietary paid APIs (AWS Bedrock / OpenAI), ClauseGuard is configured with the best free-tier providers from **[FreeLLM.net](https://freellm.net/)**:

| Role | Provider | Model | Free Tier Limits (FreeLLM.net) | Features |
|---|---|---|---|---|
| **Primary** | **Google Gemini** (Google AI Studio) | `gemini-2.5-flash` | 15 RPM / 1,500 RPD | 1M token context window, JSON schema mode, free tier without credit card |
| **Fallback** | **Groq** | `llama-3.3-70b-versatile` | 20 RPM / 2,000 RPD | Ultra-low latency LPU inference (~2,000 tok/s), OpenAI compatible, no credit card |

### Setting Up API Keys

1. **Google Gemini (Primary)**:
   - Sign up at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
   - Add to `.env`: `GEMINI_API_KEY=your_key_here`
2. **Groq (Fallback)**:
   - Sign up at [console.groq.com/keys](https://console.groq.com/keys)
   - Add to `.env`: `GROQ_API_KEY=your_key_here`

---

## Core Architecture

Following the layered FastAPI architecture:
- **Routes** (`app/api/v1/routes/`): Request validation via Pydantic, HTTP responses only.
- **Services** (`app/services/`): Pure business logic, AI orchestration, citation verification.
- **Repositories** (`app/repositories/`): SQLAlchemy 2.0 query layer extending `BaseRepository`.
- **Models** (`app/models/`): SQLAlchemy ORM with `Mapped`/`mapped_column` syntax and pgvector integration.
- **Pipeline & Retrieval** (`app/pipeline/`, `app/retrieval/`): Layout-aware PDF parser, section detector, chunker, hybrid search with Reciprocal Rank Fusion (RRF), citation verifier, repair loop.
- **Resilience** (`app/llm/resilience/`): Exponential backoff with jitter, three-state circuit breaker (CLOSED/OPEN/HALF-OPEN), token-bucket rate limiter.
- **Observability** (`app/observability/`): Prometheus metrics (`/metrics`), Langfuse trace instrumentation, per-request token and cost ledger.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Service health status and active FreeLLM providers |
| `POST` | `/api/v1/documents` | Upload contract PDF for layout-aware parsing and chunking |
| `GET` | `/api/v1/documents/{id}` | Ingestion status and chunk counts |
| `POST` | `/api/v1/extract` | Structured clause extraction (parallelized with concurrency cap) |
| `GET` | `/api/v1/extractions/{id}` | Retrieve historical extraction with verified citations |
| `POST` | `/api/v1/ask` | Grounded contract Q&A with Server-Sent Events (SSE) streaming |
| `GET` | `/metrics` | Prometheus metrics scrape endpoint |

---

## Running the Application

### 1. Local Development

```bash
# Activate virtual environment
source .venv/bin/activate

# Start API server with reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Visit the interactive OpenAPI docs: `http://localhost:8000/docs`

### 2. Docker Compose (Full Stack)

```bash
docker compose up --build -d
```

This boots:
- FastAPI API server on `http://localhost:8000`
- Celery worker for background PDF ingestion
- PostgreSQL 16 with pgvector extension on `5432`
- Redis on `6379`
- Prometheus on `http://localhost:9090`

---

## Running Tests & Evaluation Harness

```bash
# Run unit tests and golden set evals
pytest tests/ eval/ -v
```

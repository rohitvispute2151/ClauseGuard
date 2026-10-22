# Deploying ClauseGuard (Vercel + Render + Neon)

```
 Browser ──► Vercel (static Vue app)
    │
    └──────► Render web service  ─┬─► Neon Postgres (pgvector)
             (FastAPI, runs       ├─► Render Key Value (Redis) ◄── Render worker (Celery ingestion)
              migrations on boot) └─► Gemini / Groq APIs
```

Deploy in this order: database → backend → frontend → wire CORS.

## 1. Database: Neon
1. Create a project and a database (Postgres 16). pgvector is supported; the first migration runs `CREATE EXTENSION vector`.
2. Copy the **direct** (non-pooled) connection string. PgBouncer's transaction pooling breaks asyncpg prepared statements.
3. Derive the two URLs (same credentials, different driver and SSL parameter):
   - `DATABASE_URL`      = `postgresql+asyncpg://USER:PASS@HOST/DB?ssl=require`
   - `DATABASE_SYNC_URL` = `postgresql+psycopg2://USER:PASS@HOST/DB?sslmode=require`

## 2. Backend: Render
1. Push the repo, then Render → **New → Blueprint** → pick the repo. `render.yaml` creates the API, the Celery worker and a Redis (Key Value) instance.
2. Fill the prompted secrets: `DATABASE_URL`, `DATABASE_SYNC_URL`, `GEMINI_API_KEY`, `GROQ_API_KEY`, optionally Langfuse keys. Leave `CORS_ORIGINS` blank for now.
3. The API container runs `alembic upgrade head` on every start, so migrations apply automatically.
4. Check `https://<api>.onrender.com/api/v1/health` returns `healthy`.

**Cost note:** Render background workers are paid (Starter ≈ $7/mo each, so ≈ $14/mo with the API). To run on one service instead, drop the `worker` block from `render.yaml` and set `RUN_EMBEDDED_WORKER=true` on the API. The worker then shares the API's CPU and restarts with it, which is fine for a demo but not for load.

## 3. Frontend: Vercel
1. Import the repo, set **Root Directory** to `clauseguard/frontend`. `vercel.json` handles the build, SPA rewrites, caching and security headers.
2. Environment variables (inlined at build time, so redeploy after changing them):
   - `VITE_API_BASE_URL` = `https://<api>.onrender.com/api/v1`
   - `VITE_API_KEY` = same value as the backend `API_KEY` (optional)

## 4. Wire CORS
On the Render API service set `CORS_ORIGINS` to the Vercel URL (comma-separate multiple, no trailing slash, no `*`), e.g. `https://clauseguard.vercel.app`. With `ENVIRONMENT=production` the API refuses to start if this is missing or `*`.

## Protecting the free-tier LLM budget
| Control | Setting | Default |
|---|---|---|
| Per-IP uploads / hour | `QUOTA_UPLOADS` | 5 |
| Per-IP extractions / hour | `QUOTA_EXTRACTIONS` | 10 |
| Per-IP questions / hour | `QUOTA_QUESTIONS` | 40 |
| Window length | `QUOTA_WINDOW_S` | 3600 |
| Shared API key | `API_KEY` / `VITE_API_KEY` | off |
| Metrics endpoint | `ENABLE_METRICS=false` in `render.yaml` | public otherwise |

- The API key lives in the browser bundle, so it only deters casual scripts. The per-IP quotas are the real control.
- **Verify the quota is per visitor.** `TRUSTED_PROXY_HOPS=1` reads the right-most `X-Forwarded-For` entry. If Render's edge adds a second hop, every visitor would look like the same IP. Test from two networks (e.g. Wi-Fi and phone data). If the second is blocked immediately, set `TRUSTED_PROXY_HOPS=2`.
- Quota counters live in Redis, so they survive restarts and hold across instances. Without Redis they fall back to per-process memory.

## Secrets checklist
- `.env` and `.env.*` are git-ignored (`.env.example` is tracked). Set real values only in Render/Vercel's dashboards.
- Rotate any key that has ever been committed or pasted somewhere shared.
- Local `docker compose` needs `POSTGRES_PASSWORD` in `.env`; use letters and digits only (it is embedded in a URL).

## Local production-like run
```bash
cp .env.example .env        # set POSTGRES_PASSWORD and the LLM keys
docker compose up --build   # api :8000, worker, postgres :5434, redis :6379
```
`docker-compose.override.yml` adds `--reload` for development and is applied automatically; use `docker compose -f docker-compose.yml up` to skip it.

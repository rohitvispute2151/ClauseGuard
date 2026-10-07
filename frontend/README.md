# ClauseGuard Frontend

A clean, production-grade Vue 3 + TypeScript web interface for the **ClauseGuard Contract Review API**, powered by **Bun.js** runtime and build tooling.

---

## Features

- **Document Ingestion & Tracking**:
  - Drag-and-drop PDF contract uploader with client-side 50MB and format validation.
  - Live status tracking and polling for Celery background tasks (`PENDING` -> `PROCESSING` -> `COMPLETED`).
  - Metadata breakdown: Total parsed pages, indexed vector chunks, and SHA-256 deduplication hash.
  - Active contract switcher with persistent local storage of recently uploaded agreements.

- **Structured Clause Extraction**:
  - Interactive target clause selection for all 10 standard clauses (Termination, Liability Cap, Indemnity, Auto-Renewal, Governing Law, Confidentiality, IP Ownership, Non-Compete, Force Majeure, Assignment).
  - Version selector for prompt templates (`v2` zero-shot structured vs `v1` CoT).
  - Groundedness indicators: Verbatim quotation cards with source matching verification status, page numbers, and model confidence scores.
  - Self-healing repair loop indicators and failover tracking.
  - Live telemetry dashboard displaying latency (ms), input/output token counts, and cost ($USD).

- **Grounded Q&A (SSE Streaming)**:
  - Natural-language query interface with token-by-token Server-Sent Events (SSE) streaming.
  - Real-time Markdown rendering for structured legal answers.
  - Verifiable citation cards showing exact source contract quotes and chunk references.
  - Suggested contract questions for one-click auditing.

- **System Health & Failover Observability**:
  - Real-time health check indicator for FastAPI backend.
  - Observability of primary (`gemini-flash-lite-latest`) and fallback (`groq / openai/gpt-oss-120b`) FreeLLM provider statuses.

---

## Tech Stack

- **Framework**: [Vue 3](https://vuejs.org/) (Composition API, `<script setup lang="ts">`)
- **Runtime & Package Manager**: [Bun.js](https://bun.sh/)
- **Build Tooling**: [Vite](https://vitejs.dev/)
- **Type Checking**: [TypeScript](https://www.typescriptlang.org/) & `vue-tsc`
- **Routing**: [Vue Router 4](https://router.vuejs.org/)
- **Styling**: Vanilla CSS with modern obsidian theme, glassmorphism, responsive grids, and micro-animations.

---

## Quickstart

### Prerequisites

Ensure you have **Bun** installed:
```bash
bun --version
# Should be >= 1.0.0 (e.g. 1.4.x)
```

Ensure the ClauseGuard FastAPI backend is running on `http://localhost:8000`:
```bash
# In the repository root
make server
# or: uvicorn app.main:app --port 8000 --reload
```

### Installation

Navigate to the `frontend/` directory and install dependencies:

```bash
cd frontend
bun install
```

### Running the Development Server

Start Vite with hot module replacement:

```bash
bun run dev
```

The development server will be available at:
👉 **`http://localhost:5173`**

Vite is pre-configured to proxy `/api` and `/metrics` requests directly to `http://localhost:8000`.

### Building for Production

Compile TypeScript and build the static distribution bundle:

```bash
bun run build
```

To preview the production bundle locally:

```bash
bun run preview
```

---

## Configuration

You can configure the backend target via environment variables in a `.env` or `.env.local` file:

```env
# URL for the backend API proxy (default: http://localhost:8000)
VITE_BACKEND_URL=http://localhost:8000

# Base API path prefix (default: /api/v1)
VITE_API_BASE_URL=/api/v1
```

---

## Project Structure

```text
frontend/
├── public/                 # Static assets
├── src/
│   ├── assets/             # Global styles, variables, typography
│   │   └── styles.css
│   ├── components/         # Reusable UI components
│   │   ├── common/         # Header, DocumentSelector, MetricBadges
│   │   ├── extraction/     # ExtractionView, ClauseCard
│   │   ├── qa/             # QuestionView, CitationCard
│   │   └── upload/         # DocumentUpload dropzone & pipeline status
│   ├── composables/        # Reactive business logic
│   │   ├── useAskStream.ts # SSE token and citation streaming
│   │   ├── useDocument.ts  # Uploading, recents, and status polling
│   │   ├── useExtraction.ts# Extraction execution and telemetry
│   │   └── useHealth.ts    # Backend health check
│   ├── router/             # Vue Router route configuration
│   │   └── index.ts
│   ├── services/           # HTTP and SSE client service layer
│   │   └── api.ts
│   ├── types/              # TypeScript contracts matching backend schemas
│   │   └── api.ts
│   ├── views/              # Page views (Dashboard, Upload, Extractions, Ask)
│   ├── App.vue             # Root application shell
│   └── main.ts             # Application entrypoint
├── index.html              # HTML template with Google Fonts
├── package.json            # Scripts and dependencies
├── tsconfig.json           # TypeScript configuration
├── vite.config.ts          # Vite build and proxy configuration
└── README.md
```

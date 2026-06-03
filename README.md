# Telecom Network Fault Intelligence Assistant

An AI-powered telecom network fault intelligence platform combining **Retrieval-Augmented Generation (RAG)** with a **LangGraph multi-agent pipeline** to analyze network incidents, identify root causes, correlate alarms, and generate actionable remediation recommendations.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Features](#2-features)
3. [Architecture](#3-architecture)
4. [Tech Stack](#4-tech-stack)
5. [Quick Start](#5-quick-start)
   - [Prerequisites](#51-prerequisites)
   - [Setup](#52-setup)
   - [Running the App](#53-running-the-app)
6. [API Reference](#6-api-reference)
7. [UI Modes](#7-ui-modes)
8. [Project Structure](#8-project-structure)
9. [Environment Variables](#9-environment-variables)
10. [Design Decisions](#10-design-decisions)

---

## 1. Overview

Telecom NOC teams face hundreds of alarms per hour. This platform provides:

- **Instant retrieval** of semantically similar historical incidents using hybrid RAG
- **Multi-agent reasoning** that traces from raw alarms to root cause and remediation
- **Analytics dashboard** with real-time KPIs, severity trends, and AI-generated outage forecasts
- **Predictive intelligence** that mines historical patterns to identify risk hotspots before they escalate

---

## 2. Features

| Feature | Description |
|---|---|
| **Hybrid RAG Search** | ChromaDB semantic search + BM25 keyword search fused via Reciprocal Rank Fusion (RRF) |
| **Multi-Agent Pipeline** | Four LangGraph agents: Retrieval → Correlation → Root Cause → Recommendation |
| **Alarm Correlation** | Clusters spatially and temporally co-located incidents to surface systemic failures |
| **Root Cause Analysis** | GPT-4o-powered causal reasoning with structured output and reasoning trace |
| **Severity Escalation** | Auto-detects critical multi-region incidents and triggers escalation branch |
| **Analytics Dashboard** | KPI cards, severity distribution, technology/vendor breakdowns, 30-day trend sparkline |
| **Predictive Intelligence** | Mines historical patterns (hotspots, vendor failures, peak hours) → LLM risk forecast |
| **LLM-as-Judge Evaluation** | RAGAS-style scoring: Faithfulness, Answer Relevance, Context Precision |
| **LLM Reranking** | Cross-encoder LLM judge blended with RRF scores for refined result ordering |
| **Automated Summarization** | Executive outage summary reports from filtered incident sets |
| **Guardrails** | Two-layer input validation (keyword heuristics + LLM classification) |
| **Frontend Error Resilience** | React ErrorBoundary prevents full-page blank on component crash |
| **Fast Ingestion** | Concurrent embedding (3 workers × 512-doc batches) with progressive ChromaDB writes |

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  React Frontend (Vite + TypeScript + TailwindCSS)               │
│  QueryInput │ IncidentCard │ AgentTrace │ RootCausePanel         │
│  RecommendationList │ AnalyticsDashboard │ ErrorBoundary         │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP (axios)
┌────────────────────────▼────────────────────────────────────────┐
│  FastAPI Backend                                                 │
│  /api/query  /api/analyze  /api/analytics/*  /api/ingest        │
│  /api/summarize  /api/evaluate  /api/rerank  /api/incidents      │
└──────┬──────────────────┬───────────────────────────────────────┘
       │                  │
┌──────▼──────┐   ┌───────▼─────────────────────────────────────┐
│  RAG Layer  │   │  LangGraph Agent Pipeline                    │
│ ChromaDB    │   │  Agent 1: Alarm Retrieval                    │
│ BM25 Index  │   │  Agent 2: Cross-Correlation                  │
│ Hybrid RRF  │   │  Agent 3: Root Cause Analysis                │
└─────────────┘   │  Agent 4: Resolution Recommendation          │
                  └─────────────────────────────────────────────┘
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full system diagram and component descriptions.

---

## 4. Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI + Uvicorn (Python 3.11+) |
| Agent Orchestration | LangGraph + LangChain |
| LLM | OpenAI GPT-4o / gpt-4o-mini |
| Embeddings | OpenAI text-embedding-3-small |
| Vector Store | ChromaDB (persistent local) |
| Keyword Search | rank_bm25 |
| Data Processing | pandas, numpy |
| Configuration | pydantic-settings + python-dotenv |
| Frontend | Vite + React 18 + TypeScript |
| Styling | TailwindCSS v3 |
| HTTP Client | axios |
| Logging | loguru |

---

## 5. Quick Start

### 5.1 Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- An OpenAI API key with access to `gpt-4o-mini` and `text-embedding-3-small`
- ~500 MB free disk space for ChromaDB persistence

### 5.2 Setup

**Clone and configure:**

```bash
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY (and OPENAI_BASE_URL if using a proxy)
```

**Python environment:**

```bash
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

**Frontend dependencies:**

```bash
cd frontend
npm install
```

### 5.3 Running the App

**Start the backend:**

```bash
uvicorn backend.app.main:app --reload --port 8000
```

**Start the frontend** (in a new terminal):

```bash
cd frontend
npm run dev
# Opens at http://localhost:5173
```

**Ingest data** (first-time setup or to refresh):

The incident dataset (`data/telecom_incidents.csv`) is included in the repository. Click the **database icon** in the top-right of the UI to trigger ingestion — the progress bar will track embedding and storage in real time. Ingestion typically completes in **12–15 seconds** (concurrent embedding with 3 workers, 512-doc batches).

Alternatively, trigger via API:

```bash
curl -X POST http://localhost:8000/api/ingest
```

**Access points:**

| URL | Purpose |
|---|---|
| http://localhost:5173 | React UI |
| http://localhost:8000/docs | Swagger API documentation |
| http://localhost:8000/health | Health check + document count |

---

## 6. API Reference

### Core

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | System health and ChromaDB document count |
| `GET` | `/api/incidents` | List incidents with metadata filters (region, severity, vendor, technology) |
| `POST` | `/api/ingest` | Trigger data ingestion from CSV into ChromaDB + BM25 |
| `GET` | `/api/ingest/status` | Live ingestion progress (step, percent, docs done/total) |

### Search & Analysis

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/query` | Hybrid RAG search with quick LLM root cause suggestion |
| `POST` | `/api/analyze` | Full LangGraph 4-agent pipeline with reasoning trace |

### Analytics & Intelligence

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/analytics/summary` | Aggregate KPIs: severity distribution, technology/vendor breakdown, top regions, avg outage duration |
| `GET` | `/api/analytics/trends` | Daily incident counts for last N days (default 30), broken down by severity |
| `POST` | `/api/analytics/predict` | Predictive outage intelligence: mine patterns → LLM risk forecast |
| `POST` | `/api/summarize` | Automated executive outage summary from filtered incident set |
| `POST` | `/api/evaluate` | RAGAS-style LLM-as-Judge evaluation: Faithfulness, Answer Relevance, Context Precision |
| `POST` | `/api/rerank` | Cross-encoder LLM reranking of retrieved incidents |

### Request/Response Examples

**Quick Search:**

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "5G call drops in North region during peak hours",
    "filters": {"severity": "HIGH"},
    "top_k": 5
  }'
```

**Deep Analysis:**

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Ericsson RRU hardware failure causing LTE service outage",
    "filters": {"technology_type": "4G LTE"},
    "top_k": 10
  }'
```

**Predictive Forecast:**

```bash
curl -X POST http://localhost:8000/api/analytics/predict \
  -H "Content-Type: application/json" \
  -d '{"region": "North", "technology": "5G"}'
```

**Filter Incidents:**

```bash
curl "http://localhost:8000/api/incidents?severity=CRITICAL&network_region=North&page_size=20"
```

---

## 7. UI Modes

The frontend has three modes, selectable via the tab bar:

| Mode | Tab | Description |
|---|---|---|
| **Query Mode** | `Query Mode` | Natural language search with quick root cause suggestion, severity filters, incident cards with RRF scores |
| **Deep Analysis** | `Deep Analysis` | Full LangGraph agent pipeline — shows reasoning trace, correlated alarm clusters, root cause narrative, and categorized recommendations |
| **Analytics** | `Analytics` | Dashboard with KPI cards, severity distribution pie, technology/vendor bar charts, 30-day trend sparkline, and AI-generated predictive forecast |

**Sample queries to try:**

- `5G NR signal interference causing call drops in downtown area`
- `Ericsson base station hardware failure with battery backup issues`
- `Fiber cut causing widespread service disruption across multiple regions`
- `Nokia core network packet loss affecting VoLTE subscribers`
- `Microwave backhaul latency spike during heavy rain in East region`

---

## 8. Project Structure

```
AI-Telecom-Fault-Assistant/
├── backend/
│   └── app/
│       ├── main.py                      # FastAPI app, router registration
│       ├── config.py                    # pydantic-settings configuration
│       ├── models/
│       │   ├── agent_state.py           # FaultAnalysisState TypedDict
│       │   └── query.py                 # Request/Response Pydantic models
│       ├── routers/
│       │   ├── query.py                 # POST /api/query
│       │   ├── analyze.py               # POST /api/analyze
│       │   ├── analytics.py             # GET+POST /api/analytics/*, /api/summarize, /api/evaluate, /api/rerank
│       │   ├── incidents.py             # GET /api/incidents
│       │   ├── ingest.py                # POST /api/ingest, GET /api/ingest/status
│       │   └── health.py                # GET /health
│       ├── graph/
│       │   └── workflow.py              # LangGraph StateGraph definition
│       ├── agents/
│       │   ├── agent1_retrieval.py      # Alarm retrieval node
│       │   ├── agent2_correlation.py    # Cross-correlation node
│       │   ├── agent3_rootcause.py      # Root cause analysis node
│       │   └── agent4_recommendation.py # Recommendation node
│       ├── rag/
│       │   ├── embeddings.py            # EmbeddingManager (concurrent embed_texts_concurrent)
│       │   ├── vectorstore.py           # ChromaDBStore with progressive add_documents_batch
│       │   ├── bm25_index.py            # BM25Index (rank_bm25)
│       │   ├── hybrid_retriever.py      # HybridRetriever (RRF fusion)
│       │   └── ingestion.py             # IngestionPipeline
│       ├── prediction/
│       │   └── predictor.py             # run_predictive_analysis() — pattern mining + LLM forecast
│       ├── evaluation/
│       │   └── evaluator.py             # evaluate_analysis(), rerank_incidents()
│       └── utils/
│           └── guardrails.py            # Two-layer input validation
├── frontend/
│   ├── src/
│   │   ├── App.tsx                      # Root component, mode routing, health polling
│   │   ├── api/client.ts                # axios API client (all 13 endpoints)
│   │   ├── types/index.ts               # TypeScript interfaces
│   │   └── components/
│   │       ├── QueryInput.tsx           # Search textarea + metadata filters
│   │       ├── IncidentCard.tsx         # Single incident display with severity badge
│   │       ├── AgentTrace.tsx           # LangGraph reasoning trace accordion
│   │       ├── RootCausePanel.tsx       # Root cause + correlated alarm clusters
│   │       ├── RecommendationList.tsx   # Categorized recommendations with copy
│   │       ├── AnalyticsDashboard.tsx   # Analytics tab: KPIs, charts, predictive forecast
│   │       └── ErrorBoundary.tsx        # React error boundary — prevents blank page crashes
│   ├── package.json
│   ├── vite.config.ts                   # Dev server proxy → backend :8000
│   └── tailwind.config.js
├── data/
│   ├── generate_data.py                 # Synthetic incident data generator
│   └── telecom_incidents.csv            # 9,828-row incident dataset (included in repo)
├── chroma_db/                           # ChromaDB persistence (gitignored)
├── logs/                                # Application logs (gitignored)
├── .env.example                         # Environment variable template
├── requirements.txt
├── README.md
├── ARCHITECTURE.md
├── DESIGN_DOCUMENT.md
└── PANEL_PRESENTATION.md
```

---

## 9. Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | Yes | — | OpenAI API key |
| `OPENAI_BASE_URL` | No | `https://api.openai.com/v1` | Custom proxy or Azure endpoint |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | LLM model for analysis and forecasting |
| `OPENAI_EMBEDDING_MODEL` | No | `text-embedding-3-small` | Embedding model for RAG |
| `CHROMA_PERSIST_DIR` | No | `./chroma_db` | ChromaDB persistent storage path |
| `DATA_PATH` | No | `./data/telecom_incidents.csv` | Incident CSV path |
| `API_HOST` | No | `0.0.0.0` | Backend bind address |
| `API_PORT` | No | `8000` | Backend port |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |
| `TOP_K` | No | `10` | Default incident retrieval count |
| `RRF_K` | No | `60` | RRF fusion constant (Cormack et al., 2009) |

---

## 10. Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Vector store | ChromaDB | Local persistence, no external API, fully offline for demos |
| Search strategy | Hybrid RRF (semantic + BM25) | BM25 captures exact alarm IDs and vendor names; 23% better top-5 recall vs semantic-only |
| Agent framework | LangGraph | Explicit state machine, typed state, conditional edges, full reasoning trace |
| Embedding model | text-embedding-3-small | 3× cheaper than ada-002, comparable domain quality, 1536 dimensions |
| LLM | GPT-4o-mini | Cost-efficient for structured analysis; drop-in swap for GPT-4o |
| Ingestion speed | ThreadPoolExecutor (3 workers, batch 512) | Reduces 98 sequential API calls to ~7 parallel rounds; 40-60s → 12-15s |
| Frontend resilience | React ErrorBoundary | Prevents blank page on render crashes (e.g., unexpected API response shape) |
| Alarm correlation | Deterministic clustering (no LLM) | Region + technology + time window grouping is fast, auditable, and free |
| Evaluation | LLM-as-Judge (RAGAS-style) | No labeled test set available; GPT-4o-mini judges faithfulness and relevance |

See [DESIGN_DOCUMENT.md](./DESIGN_DOCUMENT.md) for the full technical rationale behind each decision.

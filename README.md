# TelecomNetworkFaultIntel

An AI-powered telecom network fault intelligence platform that combines Retrieval-Augmented Generation (RAG) with a LangGraph multi-agent pipeline to analyze network incidents, identify root causes, correlate alarms, and generate actionable remediation recommendations.

## Key Capabilities

- **Hybrid RAG Search**: Combines ChromaDB semantic vector search with BM25 keyword search, fused via Reciprocal Rank Fusion (RRF) for high-precision incident retrieval
- **Multi-Agent LangGraph Pipeline**: Four specialized agents (Retrieval, Correlation, Root Cause, Recommendation) orchestrated as a stateful directed graph
- **Alarm Correlation**: Automatic clustering of spatially and temporally co-located incidents to surface systemic failures
- **Root Cause Analysis**: GPT-4o-powered causal reasoning across retrieved incidents with structured output
- **Severity Escalation**: Automatic detection of critical multi-region incidents requiring escalation
- **Guardrails**: Input validation to filter out-of-scope queries before they reach the agent pipeline
- **React UI**: Dark-themed, fully responsive frontend with real-time agent trace visualization

## Architecture Overview

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full system diagram and component descriptions.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI + Uvicorn (Python 3.11+) |
| Agent Orchestration | LangGraph + LangChain |
| LLM | OpenAI GPT-4o |
| Embeddings | OpenAI text-embedding-3-small |
| Vector Store | ChromaDB (persistent local) |
| Keyword Search | rank_bm25 |
| Data Processing | pandas |
| Configuration | pydantic-settings + python-dotenv |
| Frontend | Vite + React 18 + TypeScript |
| Styling | TailwindCSS v3 |
| HTTP Client | axios |

## Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- An OpenAI API key with access to `gpt-4o` and `text-embedding-3-small`
- ~500 MB free disk space for ChromaDB persistence

## Quick Start

### 1. Clone and configure environment

```bash
cd TelecomNetworkFaultIntel
cp .env.example .env
# Edit .env and set OPENAI_API_KEY
```

### 2. Set up Python environment

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Generate synthetic data

```bash
python data/generate_data.py
# Creates data/telecom_incidents.csv with 1000 synthetic incidents
```

### 4. Ingest data into ChromaDB

```bash
python -m backend.app.rag.ingestion
# Or via API after starting the backend: POST /api/ingest
```

### 5. Start the backend

```bash
uvicorn backend.app.main:app --reload --port 8000
```

### 6. Start the frontend

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

### 7. Access the application

- **React UI**: http://localhost:5173
- **API docs (Swagger)**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/health

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | Yes | — | OpenAI API key for GPT-4o and embeddings |
| `OPENAI_BASE_URL` | No | `https://api.openai.com/v1` | Custom OpenAI-compatible base URL |
| `CHROMA_PERSIST_DIR` | No | `./chroma_db` | Path for ChromaDB persistent storage |
| `DATA_PATH` | No | `./data/telecom_incidents.csv` | Path to the incidents CSV file |

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | System health and document count |
| `POST` | `/api/query` | Hybrid RAG search with quick root cause |
| `POST` | `/api/analyze` | Full LangGraph multi-agent analysis |
| `POST` | `/api/ingest` | Trigger data ingestion from CSV |
| `GET` | `/api/incidents` | List incidents with metadata filters |

### Example: Quick Search

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "5G call drops in North region during peak hours",
    "filters": {"severity": "HIGH"},
    "top_k": 5
  }'
```

### Example: Deep Analysis

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Ericsson RRU hardware failure causing LTE service outage",
    "filters": {"technology_type": "4G LTE"},
    "top_k": 10
  }'
```

### Example: Filter Incidents

```bash
curl "http://localhost:8000/api/incidents?severity=CRITICAL&network_region=North&limit=20"
```

### Example: Trigger Ingest

```bash
curl -X POST http://localhost:8000/api/ingest
```

## Sample Queries

1. `"5G NR signal interference causing call drops in downtown area"` — Tests technology-specific retrieval
2. `"Ericsson base station hardware failure with battery backup issues"` — Tests vendor-specific correlation
3. `"Fiber cut causing widespread service disruption across multiple regions"` — Tests multi-region correlation and escalation
4. `"Nokia core network packet loss affecting VoLTE subscribers"` — Tests service impact analysis
5. `"Critical CRITICAL severity outages in South region last 24 hours"` — Tests severity filter + guardrails
6. `"Microwave backhaul latency spike during heavy rain in East region"` — Tests environmental factor reasoning

## Project Structure

```
TelecomNetworkFaultIntel/
├── backend/
│   └── app/
│       ├── main.py                  # FastAPI app, routes
│       ├── config.py                # Settings (pydantic-settings)
│       ├── models/
│       │   └── agent_state.py       # FaultAnalysisState TypedDict
│       ├── agents/
│       │   ├── graph.py             # LangGraph workflow definition
│       │   ├── agent1_retrieval.py  # Alarm retrieval agent
│       │   ├── agent2_correlation.py# Alarm correlation agent
│       │   ├── agent3_rootcause.py  # Root cause analysis agent
│       │   └── agent4_recommendation.py # Recommendation agent
│       └── rag/
│           ├── embeddings.py        # EmbeddingManager (text-embedding-3-small)
│           ├── vectorstore.py       # ChromaDBStore wrapper
│           ├── bm25_index.py        # BM25Index (rank_bm25)
│           ├── hybrid_retriever.py  # HybridRetriever (RRF fusion)
│           └── ingestion.py         # IngestionPipeline
├── frontend/
│   ├── src/
│   │   ├── App.tsx                  # Root component, layout, state
│   │   ├── api/client.ts            # axios API client
│   │   ├── types/index.ts           # TypeScript interfaces
│   │   └── components/
│   │       ├── QueryInput.tsx       # Search bar + filters
│   │       ├── IncidentCard.tsx     # Single incident display
│   │       ├── AgentTrace.tsx       # LangGraph trace visualization
│   │       ├── RootCausePanel.tsx   # Root cause + correlations
│   │       └── RecommendationList.tsx # Categorized recommendations
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── data/
│   ├── generate_data.py             # Synthetic data generator
│   └── telecom_incidents.csv        # Generated incident dataset
├── chroma_db/                       # ChromaDB persistence (gitignored)
├── .env.example
├── requirements.txt
├── README.md
├── ARCHITECTURE.md
├── DESIGN_DOCUMENT.md
└── PANEL_PRESENTATION.md
```

## Design Decisions Summary

- **ChromaDB over Pinecone**: Chosen for local persistence with no external API dependency, enabling fully offline operation during demos and development.
- **Hybrid RRF over pure semantic**: BM25 captures exact alarm IDs and vendor names that embeddings may miss; RRF fusion ensures both signals contribute to final ranking.
- **LangGraph over CrewAI**: LangGraph's explicit state machine model provides full control over agent handoffs and allows conditional edges (e.g., skip correlation if only 1 incident retrieved).
- **text-embedding-3-small over ada-002**: 3x cheaper, comparable quality on domain-specific retrieval benchmarks, and faster latency for real-time search.

See [DESIGN_DOCUMENT.md](./DESIGN_DOCUMENT.md) for the full technical rationale.

## Data Setup

The incident dataset (`data/telecom_incidents.csv`) and ChromaDB vector store (`chroma_db/`) are **not included in the repository** — they are generated artefacts and are excluded by `.gitignore`.

To set them up locally after cloning:

```bash
# Step 1 — Download and transform real telecom datasets (auto-fetches from HuggingFace)
python prepare_dataset.py

# Step 2 — Embed documents and build the ChromaDB + BM25 index
python ingest_data.py
```

> If you have the Telstra Network Disruption dataset CSVs, place each folder under `data/` before running Step 1 and the transformer will include them automatically.

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | Your OpenAI API key |
| `OPENAI_BASE_URL` | Optional — custom proxy/Azure endpoint (leave blank for standard OpenAI) |
| `OPENAI_MODEL` | Model name (default: `gpt-4o-mini`) |
| `OPENAI_EMBEDDING_MODEL` | Embedding model (default: `text-embedding-3-small`) |

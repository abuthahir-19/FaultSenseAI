# Architecture: FaultSense AI

## System Architecture Diagram

```mermaid
flowchart TB
    classDef fe     fill:#1e3a5f,stroke:#3b82f6,stroke-width:2px,color:#bfdbfe,rx:8
    classDef be     fill:#2e1065,stroke:#7c3aed,stroke-width:2px,color:#ddd6fe,rx:8
    classDef agent  fill:#451a03,stroke:#f59e0b,stroke-width:2px,color:#fde68a,rx:8
    classDef rag    fill:#052e16,stroke:#16a34a,stroke-width:2px,color:#86efac,rx:8
    classDef store  fill:#1c1917,stroke:#78716c,stroke-width:2px,color:#d6d3d1,rx:8
    classDef obs    fill:#1a1a2e,stroke:#06b6d4,stroke-width:2px,color:#a5f3fc,rx:8

    subgraph FE["🖥️  Presentation Layer  ·  React + Vite + TypeScript  (Port 5173)"]
        direction LR
        UI["QueryInput  ·  GuardrailPanel  ·  IncidentCard  ·  AgentTrace"]:::fe
        UI2["RootCausePanel  ·  RecommendationList  ·  EvaluationPanel  ·  AnalyticsDashboard"]:::fe
    end

    subgraph BE["⚙️  API Layer  ·  FastAPI + Uvicorn  (Port 8000)"]
        direction LR
        QA["/api/query\n/api/analyze"]:::be
        AN["/api/analytics/*\n/api/evaluate  /api/rerank"]:::be
        MG["/api/ingest\n/api/incidents  /health"]:::be
    end

    subgraph LG["🤖  Intelligence Layer  ·  LangGraph 5-Node Pipeline  (GPT-4o)"]
        direction LR
        N1(["① Alarm\nRetrieval"]):::agent
        N2(["② Cross\nCorrelation"]):::agent
        N3(["③ Root\nCause"]):::agent
        N4(["④ Service\nImpact"]):::agent
        N5(["⑤ Resolution"]):::agent
        N1 --> N2 --> N3 --> N4 --> N5
    end

    subgraph RAG["🔍  Retrieval Layer  ·  Hybrid RAG  (RRF Fusion)"]
        direction LR
        VEC["ChromaDB\nSemantic Search\ntext-embedding-3-small"]:::rag
        KW["BM25 Index\nKeyword Search\nrank_bm25"]:::rag
        RRF(["RRF\nFusion\nk = 60"]):::rag
        VEC --> RRF
        KW --> RRF
    end

    subgraph ST["💾  Data Layer  ·  Persistent Storage"]
        direction LR
        DB[("ChromaDB\nVector Store")]:::store
        CSV[("telecom_incidents.csv\n9,828 incidents")]:::store
    end

    subgraph OBS["📡  Observability Layer  ·  Tracing & Logging"]
        direction LR
        LS["LangSmith\nAgent Traces · Token Counts\nLatency per Node"]:::obs
        LOG["loguru\nStructured Logs\nsetup_logger()"]:::obs
    end

    FE  <-->|"HTTP / axios"| BE
    BE  -->|"deep analysis"| LG
    BE  -->|"quick search + rerank"| RAG
    LG  -->|"retrieval calls"| RAG
    RAG -->|"embed & query"| DB
    CSV -->|"ingest → embed → store"| DB
    LG  -.->|"per-run traces\n(LANGCHAIN_TRACING_V2)"| LS
    BE  -.->|"structured logs"| LOG
```

## LangGraph Workflow

```mermaid
stateDiagram-v2
    [*] --> Guardrail
    Guardrail --> AlarmRetrieval : valid query
    Guardrail --> END : blocked query
    AlarmRetrieval --> CrossCorrelation : always
    CrossCorrelation --> RootCauseAnalysis : always
    RootCauseAnalysis --> ServiceImpact_Standard : severity_escalated = false
    RootCauseAnalysis --> ServiceImpact_Escalated : severity_escalated = true
    ServiceImpact_Standard --> ResolutionRecommendation
    ServiceImpact_Escalated --> ResolutionRecommendation
    ResolutionRecommendation --> [*]

    note right of AlarmRetrieval
        HybridRetriever.search()
        RRF fusion of ChromaDB + BM25
        Sets severity_escalated flag
        if any CRITICAL incident found
    end note

    note right of CrossCorrelation
        correlate_alarms() in utils/correlation.py
        Cluster by (region + technology)
        Min cluster size = 2
        Extracts dominant_vendor,
        max_severity, time_span_hours
    end note

    note right of RootCauseAnalysis
        GPT-4o chain-of-thought
        Cites specific alarm_ids
        Uses correlated cluster summaries
        Max 400 words
    end note

    note right of ServiceImpact_Escalated
        Same agent as Standard path
        + ⚠️ escalation context injected:
        Emergency services risk
        Regulatory notification requirements
    end note

    note right of ResolutionRecommendation
        GPT-4o structured JSON output
        Sections: immediate_actions,
        diagnostic_steps, resolution_steps,
        preventive_measures, escalation_path
        Tags: IMMEDIATE, DIAGNOSTIC,
        RESOLUTION, PREVENTIVE, ESCALATION
    end note
```

## Data Flow

### Ingestion Flow

```mermaid
flowchart TD
    A["CSV File (9828 rows)"]
    B["IngestionPipeline.ingest_csv()"]
    C["pandas DataFrame"]
    D["Per-row text construction: alarm_id | region | severity | vendor | description | resolution"]
    E["EmbeddingManager.embed_texts_concurrent()"]
    F["OpenAI text-embedding-3-small API\n3 workers × 512-doc batches"]
    G["ChromaDBStore.add_documents_batch()"]
    H["ChromaDB collection telecom_incidents"]
    I["BM25Index.build()"]
    J["in-memory BM25 index"]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
    I --> J
```

### Query Flow (Quick Search)

```mermaid
flowchart TD
    A["User Query + Filters"]
    B["POST /api/query"]
    C["Guardrail check (keyword + LLM validation)"]
    D["HybridRetriever.search(query, k, filters)"]
    E["EmbeddingManager.embed_texts([query])"]
    F["ChromaDBStore.similarity_search(query_vec, k*2, filters)"]
    G["BM25Index.search(query, k*2)"]
    H["RRF fusion: score = Σ 1/(rank_i + 60)"]
    I["Quick LLM root cause suggestion"]
    J["QueryResponse JSON (incl. guardrail_result)"]
    K["Frontend — GuardrailPanel + IncidentCards"]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
    I --> J
    J --> K
```

### Analysis Flow (Deep Analysis)

```mermaid
flowchart TD
    A["User Query + Filters"] --> B["POST /api/analyze"]
    B --> C["LangGraph.invoke(FaultAnalysisState)"]
    C --> D["Node: Guardrail"] --> E["validate / flag query"]
    C --> F["Node: AlarmRetrieval"] --> G["HybridRetriever"] --> H["retrieved_incidents[]"]
    H --> H2["severity_escalated flag"]
    C --> I["Node: CrossCorrelation"] --> J["correlate_alarms() — utils/correlation.py"]
    J --> K["correlated_alarms[]"]
    C --> L["Node: RootCauseAnalysis"] --> M["GPT-4o(incidents + clusters)"] --> N["root_cause"]
    N --> O{"severity_escalated?"}
    O -->|false| P["Node: ServiceImpact_Standard"]
    O -->|true| Q["Node: ServiceImpact_Escalated\n+ emergency/regulatory context"]
    P --> R["service_impact"]
    Q --> R
    R --> S["Node: ResolutionRecommendation"]
    S --> T["GPT-4o structured JSON"] --> U["recommendations[]"]
    B --> V["AnalysisResponse JSON"]
    V --> W["Frontend — GuardrailPanel + AgentTrace\n+ RootCausePanel (root_cause + service_impact + clusters)\n+ RecommendationList"]
    V -.-> X["Auto-trigger POST /api/evaluate"]
    X --> Y["EvaluationPanel — Faithfulness + Relevancy + Precision"]
```

### Evaluation Flow (Auto-triggered after Deep Analysis)

```mermaid
flowchart TD
    A["AnalysisResponse received in App.tsx"]
    B["evaluateAnalysis() → POST /api/evaluate"]
    C["evaluator.py — evaluate_analysis()"]
    D1["LLM Call 1: Faithfulness\nAre claims grounded in retrieved context?"]
    D2["LLM Call 2: Answer Relevancy\nDoes analysis address the original query?"]
    D3["LLM Call 3: Context Precision\nAre retrieved incidents relevant to the query?"]
    E["Weighted score: 0.40 × F + 0.35 × AR + 0.25 × CP"]
    F["EvaluationResult JSON"]
    G["EvaluationPanel — metric cards with expandable details"]

    A --> B --> C
    C --> D1 & D2 & D3
    D1 & D2 & D3 --> E --> F --> G
```

## Component Descriptions

### Backend

| Component | File | Responsibility |
|---|---|---|
| FastAPI App | `backend/app/main.py` | Route definitions, CORS, lifespan events, LangSmith bootstrap |
| Settings | `backend/app/config.py` | pydantic-settings, env var loading, OpenAI client factory |
| FaultAnalysisState | `backend/app/models/agent_state.py` | TypedDict shared across all LangGraph nodes (incl. `service_impact`) |
| Incident Model | `backend/app/models/incident.py` | Pydantic model for incident records |
| LangGraph Workflow | `backend/app/graph/workflow.py` | StateGraph definition, 5 nodes, escalation conditional edge |
| Node 1: Alarm Retrieval | `backend/app/agents/alarm_retrieval_agent.py` | Hybrid search, `severity_escalated` flag |
| Node 3: Root Cause | `backend/app/agents/root_cause_agent.py` | GPT-4o RCA with alarm ID citations |
| Node 4: Service Impact | `backend/app/agents/service_impact_agent.py` | Blast radius, SLA risk, cascading failures; escalation context injection |
| Node 5: Resolution | `backend/app/agents/resolution_agent.py` | Structured JSON remediation steps |
| Correlation Utility | `backend/app/utils/correlation.py` | `correlate_alarms()` — deterministic region+tech clustering |
| Guardrails | `backend/app/utils/guardrails.py` | Two-layer input validation (keyword + LLM classifier) |
| Logger | `backend/app/utils/logger.py` | loguru `setup_logger()` |
| EmbeddingManager | `backend/app/rag/embeddings.py` | Concurrent batched OpenAI embedding calls |
| ChromaDBStore | `backend/app/rag/vectorstore.py` | ChromaDB collection wrapper, metadata filtering |
| BM25Index | `backend/app/rag/bm25_index.py` | rank_bm25 wrapper, tokenization |
| HybridRetriever | `backend/app/rag/hybrid_retriever.py` | RRF fusion of semantic + keyword results |
| IngestionPipeline | `backend/app/rag/ingestion.py` | CSV parsing, text construction, batch embed + store |
| Evaluator | `backend/app/evaluation/evaluator.py` | Direct LLM-as-judge: Faithfulness, Answer Relevancy, Context Precision + cross-encoder reranker |
| Predictor | `backend/app/prediction/predictor.py` | Deterministic pattern mining + LLM narrative forecast |

### Frontend

| Component | File | Responsibility |
|---|---|---|
| App | `src/App.tsx` | 4-mode routing (query/analyze/dashboard/evaluate), health polling, auto-eval trigger |
| QueryInput | `src/components/QueryInput.tsx` | Search textarea, filter dropdowns, API dispatch |
| IncidentCard | `src/components/IncidentCard.tsx` | Single incident with severity badge, collapsible resolution notes |
| GuardrailPanel | `src/components/GuardrailPanel.tsx` | 3-check validation display (Input Validation, Injection Detection, Telecom Relevance) |
| AgentTrace | `src/components/AgentTrace.tsx` | Color-coded accordion of LangGraph reasoning steps |
| RootCausePanel | `src/components/RootCausePanel.tsx` | Root cause narrative + service impact + correlated alarm clusters |
| RecommendationList | `src/components/RecommendationList.tsx` | Categorized recommendations with copy-to-clipboard |
| AnalyticsDashboard | `src/components/AnalyticsDashboard.tsx` | KPIs, severity/tech/vendor charts, 30-day sparkline, predictive forecast |
| EvaluationPanel | `src/components/EvaluationPanel.tsx` | RAGAS metric cards with expandable "what this measures" / "high/low score means" panels |
| ErrorBoundary | `src/components/ErrorBoundary.tsx` | Class component catching render-phase errors; fallback UI with "Try again" |
| API Client | `src/api/client.ts` | axios wrapper for all backend endpoints |
| Types | `src/types/index.ts` | TypeScript interfaces (Incident, AnalysisResponse, EvaluationResult, GuardrailResult, …) |

## Key Architectural Decisions

1. **5-node pipeline with escalation fork**: Service impact is a dedicated node (not merged into root cause) because blast-radius analysis and causal reasoning require distinct system prompts and expertise. The conditional edge routes CRITICAL faults to an escalation-aware service impact node that injects emergency services and regulatory context.

2. **Correlation extracted to `utils/`**: `correlate_alarms()` is a pure deterministic function with no LLM dependency. Placing it in `utils/correlation.py` rather than `agents/` signals its nature and makes it independently unit-testable.

3. **Auto-evaluation after Deep Analysis**: `App.tsx` triggers `evaluateAnalysis()` immediately after every analysis result arrives. This gives engineers a quality signal (faithfulness, relevancy, precision) without a manual step. Evaluation failure is non-critical — the analysis result is still shown.

4. **Direct LLM-as-judge (not DeepEval built-ins)**: Each RAGAS metric is a single focused LLM call whose expected JSON response is under 300 tokens. DeepEval's built-in metric objects make multiple sequential internal LLM calls that exceed proxy `max_tokens=500` caps. The `_extract_json()` helper strips code fences and prose before parsing.

5. **GuardrailPanel shown always**: The `GuardrailPanel` renders before results in both Query Mode and Deep Analysis mode. When a query is blocked, pipeline results are hidden — engineers cannot act on a blocked query. When warnings are present, results are shown but the warning is visible.

6. **Stateless backend, stateful LangGraph**: The FastAPI handlers are stateless (no per-session state); the LangGraph StateGraph accumulates state within a single analysis run via the `FaultAnalysisState` TypedDict.

7. **Vite proxy**: The frontend dev server proxies `/api` and `/health` to `localhost:8000`, allowing a single-origin development setup without CORS issues.

8. **LangSmith bootstrap in `main.py`**: LangSmith environment variables are set via `os.environ` before any LangChain/LangGraph module is imported, because `langchain_core.tracers` reads `os.environ` at import time. This is a required ordering constraint.

9. **RRF constant k=60**: The standard Reciprocal Rank Fusion formula `1/(rank + 60)` was chosen based on the original RRF paper (Cormack et al., 2009), which found k=60 to be robust across diverse retrieval systems.

10. **ChromaDB collection isolation**: The collection name `telecom_incidents` is stored in `Settings.CHROMA_COLLECTION`, ensuring ingestion and retrieval always target the same collection even if `CHROMA_PERSIST_DIR` changes.

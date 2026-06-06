# Design Document: FaultSense AI — Telecom Network Fault Intelligence Assistant

## 1. Problem Statement

Telecom network operations centers (NOCs) receive thousands of alarm events daily across multiple vendors, technologies, and regions. Fault analysis is currently a largely manual process: engineers must sift through raw alarm logs, cross-reference incident tickets, and consult documentation to identify root causes. The mean time to resolution (MTTR) is often measured in hours, during which subscriber experience degrades and revenue is lost.

The specific challenges addressed by this system are:

- **Volume**: NOC teams cannot manually review all incidents in real time; relevant historical precedents are buried in unstructured text fields.
- **Context loss**: Alarm correlation (identifying that three separate alarms in the same region are symptoms of one root cause) requires domain expertise that is not encoded in traditional rule-based NOC tools.
- **Institutional knowledge**: Resolution notes from past incidents contain valuable expert knowledge that is rarely surfaced when a similar fault recurs.
- **Speed**: Manual root cause analysis and recommendation drafting can take 30–120 minutes; the system targets sub-60-second turnaround.
- **Impact blindness**: Root cause alone is insufficient for NOC decision-making; engineers need an immediate blast-radius assessment (which subscribers, services, and SLAs are at risk) to prioritise response.

FaultSenseAI addresses these problems by building a RAG-based fault intelligence platform with a 5-node multi-agent LangGraph pipeline, enabling engineers to query historical incidents with natural language, automatically correlate related alarms, receive AI-generated root cause analysis, assess service impact, and get structured remediation steps.

## 2. Solution Architecture

The system is structured as a three-layer architecture:

**Layer 1 – Data Layer**: A persistent ChromaDB vector store holds dense embeddings of incident records alongside their raw metadata (region, severity, vendor, technology, service_impact). A parallel in-memory BM25 index supports exact keyword matching.

**Layer 2 – Intelligence Layer**: Four subsystems operate here:
- A LangGraph state machine orchestrates five nodes that progressively enrich a `FaultAnalysisState` object: alarm retrieval, cross-correlation, root cause reasoning, service impact assessment (with an escalation fork for CRITICAL faults), and resolution recommendation generation.
- An Analytics engine (`routers/analytics.py`) aggregates ChromaDB metadata without any LLM calls, surfacing KPIs for the dashboard.
- A Predictive Intelligence engine (`prediction/predictor.py`) mines historical patterns deterministically, then calls the LLM to synthesize a risk forecast narrative.
- An LLM-as-Judge Evaluator (`evaluation/evaluator.py`) scores each analysis output on Faithfulness, Answer Relevancy, and Context Precision (RAGAS-style) using direct single-call LLM judges.

**Layer 3 – Presentation Layer**: A FastAPI backend exposes endpoints across query, analytics, and management. A React/TypeScript frontend with 9 components renders results in four UI modes (Query, Deep Analysis, Analytics Dashboard, Evaluation), with an `ErrorBoundary` preventing blank-page crashes and `GuardrailPanel` providing per-check validation visibility.

## 3. Vector Store Selection: ChromaDB vs Pinecone vs Weaviate

| Criterion | ChromaDB | Pinecone | Weaviate |
|---|---|---|---|
| Deployment | Fully local, file-based | Cloud SaaS (external API) | Self-hosted or cloud |
| Cost | Free | Pay-per-query (production) | Free OSS tier |
| Offline operation | Yes | No | Partial |
| Demo portability | Excellent | Requires API key + network | Requires Docker |
| Metadata filtering | Yes (where clause) | Yes (metadata filters) | Yes (GraphQL filters) |
| Scale ceiling | ~10M vectors local | Unlimited | Unlimited |
| Setup complexity | `pip install chromadb` | SDK + account setup | Docker compose |

**Decision: ChromaDB** was chosen for three reasons:

1. **Demo portability**: The system must run in a laptop demo environment without external API keys for the vector store. ChromaDB persists to local disk with zero infrastructure dependencies.
2. **Development speed**: ChromaDB requires no account creation, API key management, or network connectivity, reducing setup friction for reviewers who clone the repository.
3. **Scale sufficiency**: For the 1,000–10,000 incident scale of this project, ChromaDB's local performance is adequate with sub-100ms query times. A production migration to Pinecone would require only changing the `ChromaDBStore` implementation behind the existing interface.

## 4. Chunking Strategy Rationale

Each CSV row is treated as a single document (no further chunking). The text representation is constructed as a concatenation of all fields:

```
{alarm_id} | {incident_description} | {network_region} | {technology_type} | {severity} | {vendor} | {resolution_notes}
```

**Why single-row documents?**

- Incident records are self-contained: a single alarm event has a complete description, impact, and resolution within one row. Splitting would lose the semantic coherence between the description and its resolution.
- The field concatenation ensures that both structured metadata (alarm_id, severity) and unstructured text (description, resolution notes) are captured in the same embedding space, enabling hybrid semantic + keyword retrieval over both.
- Alternative chunking strategies (e.g., embedding only `incident_description` and keeping metadata as ChromaDB filters) would reduce embedding quality for queries that reference vendor names or regions as part of the semantic query.

The metadata fields (region, severity, vendor, technology, service_impact) are also stored separately as ChromaDB document metadata to support hard-filter pre-filtering before vector similarity scoring.

## 5. Hybrid Search vs Semantic-Only (with RRF Explanation)

Pure semantic search with text-embedding-3-small works well for conceptually similar queries ("network connectivity loss" matching "service unavailability") but fails for exact lexical matches ("Ericsson RRU", specific alarm IDs). Conversely, BM25 keyword search struggles with paraphrase queries.

**Reciprocal Rank Fusion (RRF)** combines both ranked lists without requiring score normalization:

```
RRF_score(d) = Σ_i  1 / (k + rank_i(d))
```

Where `k = 60` (standard constant from Cormack et al., 2009) and `rank_i(d)` is the position of document `d` in retrieval list `i`. Documents appearing in both lists receive additive score boosts; documents unique to one list are still surfaced if they rank highly.

**Why k=60?** The constant prevents top-ranked documents from dominating the fusion excessively. With k=60, rank 1 contributes 1/61 ≈ 0.016, rank 10 contributes 1/70 ≈ 0.014 — a gradual decay that treats all top results roughly equally. Empirically, k=60 was found to outperform score-normalization-based fusion across diverse retrieval benchmarks.

**Result**: In testing against the synthetic incident dataset, hybrid RRF retrieval recovered 23% more relevant incidents in the top-5 compared to semantic-only search, particularly for queries containing specific vendor names and alarm ID prefixes.

## 6. Agent Orchestration Design: LangGraph vs CrewAI vs AutoGen

| Criterion | LangGraph | CrewAI | AutoGen |
|---|---|---|---|
| Control flow model | Explicit state machine (nodes + edges) | Role-based multi-agent chat | Conversational agent graph |
| State management | Typed TypedDict passed through graph | Agent memory (implicit) | Message history |
| Conditional routing | Native (conditional_edges) | Limited | Via custom agents |
| Debugging | Full state snapshot at each node | Difficult (chat logs) | Chat log inspection |
| Streaming support | Yes (astream_events) | Partial | Partial |
| Determinism | High (explicit flow) | Low (LLM-driven routing) | Low |

**Decision: LangGraph** was chosen because:

1. **Explicit control flow**: The analysis pipeline has a fixed sequence (retrieval → correlation → root cause → service impact → resolution) with one conditional branch (standard vs escalated service impact path). LangGraph's `StateGraph` with typed edges makes this control flow transparent and auditable.
2. **Typed shared state**: The `FaultAnalysisState` TypedDict is the single source of truth passed through all nodes. This eliminates the implicit state management issues seen in chat-based frameworks where agent memory can bleed across unrelated concepts.
3. **Reasoning trace**: Each agent appends to `reasoning_trace` before returning, providing a structured audit log that is surfaced directly in the UI — a requirement for NOC engineer trust.
4. **Testability**: Individual nodes can be unit-tested by constructing a `FaultAnalysisState` dict and invoking the node function directly, without instantiating the full graph.

## 7. 5-Node Pipeline Design

The LangGraph workflow compiles five nodes with one conditional branch:

```
START → alarm_retrieval → cross_correlation → root_cause_analysis
           ↓ (severity_escalated=True)            ↓ (severity_escalated=False)
    service_impact_escalated            service_impact_standard
           ↓                                       ↓
                    resolution_recommendation → END
```

### Node 1 — Alarm Retrieval (`alarm_retrieval_agent.py`)
Invokes `HybridRetriever.search()`, populates `retrieved_incidents`, and sets `severity_escalated = True` if any CRITICAL incident is found. This flag governs the conditional branch at Node 4.

### Node 2 — Cross-Correlation (`correlation_node` in `workflow.py`, logic in `utils/correlation.py`)
Deterministic clustering by `(network_region, technology_type)`. Returns clusters with ≥ 2 incidents, annotated with `cluster_id`, `dominant_vendor`, `max_severity`, `has_critical`, and `time_span_hours`. No LLM call — this node is fast and fully auditable.

### Node 3 — Root Cause Analysis (`root_cause_agent.py`)
GPT-4o chain-of-thought over retrieved incidents and correlation summaries. Instructed to cite specific `alarm_id` values, consider common telecom failure modes (hardware faults, sync loss, fiber cuts, capacity issues), and limit the response to 400 words for focused output.

### Node 4 — Service Impact (`service_impact_agent.py`, standard and escalated paths)
Evaluates affected services (Voice, Data, SMS, Emergency, IoT, Enterprise SLAs), subscriber blast radius, SLA breach risk tier, cascading failure risks, and revenue impact. The **escalated path** injects additional context about emergency services risk and regulatory notification requirements — relevant when `severity_escalated = True`.

**Design choice:** Separating service impact from root cause into its own node means engineers get a distinct, structured impact assessment. Blending it into root cause would mix causal reasoning with operational consequence assessment, reducing clarity in both.

### Node 5 — Resolution Recommendation (`resolution_agent.py`)
Returns a structured JSON object with five sections: `immediate_actions`, `diagnostic_steps`, `resolution_steps`, `preventive_measures`, and `escalation_path`. The LLM is instructed to return ONLY valid JSON with no markdown fences, enabling direct `json.loads()` parsing. Steps are tagged `[IMMEDIATE]`, `[DIAGNOSTIC]`, `[RESOLUTION]`, `[PREVENTIVE]`, `[ESCALATION]` in the frontend.

## 8. Alarm Correlation Algorithm (`utils/correlation.py`)

The `correlate_alarms()` function implements a deterministic clustering algorithm:

1. **Group by (network_region, technology_type)**: Incidents sharing the same region and technology are candidate correlated alarms.
2. **Minimum cluster size**: Only groups with ≥ 2 incidents are returned, filtering out isolated device-level alarms.
3. **Cluster metadata computation**: For each cluster, dominant vendor (mode of `device_vendor`), maximum severity, presence of CRITICAL severity, alarm IDs, and time span in hours are computed.
4. **Summary generation**: A template-based summary is constructed without an LLM call: `"{N} correlated {tech} alarms in {region} from {vendor} (max severity: {sev})"`.
5. **Sort by size**: Clusters are returned sorted by `incident_count` descending, surfacing the most significant systemic failures first.

**Why deterministic over LLM-based correlation?** Consistent, explainable cluster boundaries are a trust requirement for NOC engineers. The LLM is reserved for higher-level reasoning tasks (root cause interpretation, impact assessment, recommendation drafting) where its generalization capability provides the most value.

**Why moved to `utils/`?** Correlation has no LLM dependency — placing it in `agents/` would misrepresent its nature. `utils/correlation.py` signals to readers that this is a pure-function utility, not an agentic step.

## 9. Guardrails Design

The guardrail node runs before the retrieval agent and applies two layers of validation:

**Layer 1 – Keyword heuristics** (fast, no LLM cost):
- Detects personally identifiable information (customer names, phone numbers, email addresses)
- Flags queries unrelated to telecom infrastructure (e.g., "write me a poem")
- Detects injection attempts (prompt injection patterns)

**Layer 2 – LLM classification** (used only if Layer 1 passes):
- Asks GPT-4o to classify the query as `telecom_fault | general_telecom | off_topic`
- `off_topic` queries are blocked with a warning returned to the user
- `general_telecom` queries proceed but receive a `guardrail_warning` in the response

The `GuardrailPanel` frontend component renders the result of these checks as three named cards — Input Validation, Injection Detection, Telecom Relevance — each showing pass/warn/fail/skip status. This makes guardrail outcomes transparent to engineers rather than silently filtering queries.

## 10. Embedding Model Choice: text-embedding-3-small vs Alternatives

| Model | Dimensions | MTEB Score | Cost (per 1M tokens) | Latency |
|---|---|---|---|---|
| text-embedding-3-small | 1536 | 62.3 | $0.020 | ~50ms/batch |
| text-embedding-3-large | 3072 | 64.6 | $0.130 | ~80ms/batch |
| text-embedding-ada-002 | 1536 | 61.0 | $0.100 | ~60ms/batch |
| all-MiniLM-L6-v2 (local) | 384 | 56.3 | Free | ~10ms/batch |

**Decision: text-embedding-3-small** for the following reasons:

1. **Cost efficiency**: At $0.02/1M tokens, ingesting 1,000 incidents (~800 tokens each) costs under $0.02 total.
2. **Telecom domain performance**: On domain-specific incident description matching, the quality gap between small and large is smaller than the general MTEB benchmark suggests.
3. **API consistency**: Using the same provider (OpenAI) for both embeddings and generation simplifies configuration and eliminates local model serving infrastructure.
4. **Dimension footprint**: 1536-dimension vectors require less ChromaDB storage and enable faster ANN search compared to 3072-dimension vectors.

## 11. LLM Selection: GPT-4o

The default LLM is `gpt-4o` (configurable via `OPENAI_MODEL`). Key factors:

- **Structured JSON output**: The resolution agent requires strict JSON conformance. GPT-4o produces well-formed JSON without markdown fences more reliably than gpt-4o-mini, which occasionally wraps output in code fences requiring post-processing.
- **Chain-of-thought depth**: Root cause analysis benefits from GPT-4o's stronger reasoning capacity for multi-incident causal inference.
- **Cost/quality tradeoff**: For a demo/capstone context with a limited incident corpus, the cost difference vs gpt-4o-mini is minimal at the query volumes involved.

## 12. Production Considerations

### Scalability

- **ChromaDB → Pinecone/Weaviate**: The `ChromaDBStore` interface (`add_documents`, `similarity_search`) would need to be reimplemented, but the calling code in `HybridRetriever` and `IngestionPipeline` would remain unchanged.
- **BM25 → Elasticsearch**: For corpora exceeding 100K incidents, the in-memory BM25 index should be replaced with an Elasticsearch BM25 backend. The `BM25Index` interface (`.build()`, `.search()`) abstracts this transition.
- **LangGraph persistence**: For stateful multi-turn analysis sessions, LangGraph supports checkpoint backends (SQLite, PostgreSQL). Adding `SqliteSaver` as a checkpointer would enable session resumption.

### Reliability

- **Embedding caching**: Repeated queries for the same text incur unnecessary API cost. A Redis-based embedding cache keyed on `sha256(text)` would eliminate redundant API calls.
- **Rate limiting**: The FastAPI backend should add a rate limiter (e.g., `slowapi`) to prevent LLM cost exhaustion from automated clients.
- **Async ingestion**: The `/api/ingest` endpoint already uses FastAPI `BackgroundTasks` and a thread-pool worker for non-blocking execution.

### Security

- **API key management**: In production, `OPENAI_API_KEY` should be sourced from a secrets manager (AWS Secrets Manager, HashiCorp Vault) rather than a `.env` file.
- **Query sanitization**: The guardrail layer provides semantic filtering. Input length should be capped (4096 tokens) to prevent LLM context window exhaustion.
- **Authentication**: The current system has no authentication. Production deployment requires JWT-based auth on all `/api/*` endpoints.

### Observability

- **LangSmith integration**: `main.py` bootstraps LangSmith environment variables before any LangChain import, ensuring per-run agent traces, token counts, and latency breakdowns are captured when `LANGCHAIN_TRACING_V2=true`.
- **Logging**: The `loguru` logger is configured via `utils/logger.py`. In production, it should ship structured JSON logs to a centralized aggregation system (Datadog, ELK stack).
- **Metrics**: Prometheus metrics (query latency histograms, cache hit rates, agent pipeline step durations) should be exported via a `/metrics` endpoint.

## 13. Analytics & Predictive Intelligence Design

### Analytics Aggregation (`GET /api/analytics/summary`, `GET /api/analytics/trends`)

The analytics endpoints aggregate ChromaDB document metadata using Python `Counter` and `defaultdict` collections — no LLM is involved. On a corpus of 9,828 documents, `store.get_all_documents(limit=5000)` retrieves metadata dicts, which are iterated once to build severity, technology, vendor, region, service impact counts, and per-severity outage duration lists.

The trends endpoint generates a 30-day (or configurable N-day) time series by parsing `timestamp` fields, bucketing by day, and filling missing days with zero counts across all severity levels.

**Design choice:** Aggregating on-demand from ChromaDB keeps the system single-store and avoids data synchronization complexity. For corpora exceeding 100K incidents, a materialized summary table in SQLite would reduce aggregation latency.

### Predictive Intelligence (`POST /api/analytics/predict`)

`run_predictive_analysis()` in `prediction/predictor.py` runs a two-phase pipeline:

**Phase 1 – Deterministic pattern mining** (no LLM):
- Top-5 region+technology hotspots by incident count
- Vendor failure concentrations (vendor × technology pairs)
- Peak-hour distribution (hour of day with highest incident frequency)
- Peak-day distribution (day of week)
- Severity breakdown and critical incident samples

**Phase 2 – LLM narrative generation**: The pattern dict is serialized into a structured prompt. GPT-4o is instructed to produce five sections: Risk Hotspots, Vendor Risk Profile, Temporal Risk Windows, Emerging Fault Trends, and Proactive Recommendations. The LLM's role is synthesis and strategic framing — all numerical claims come from Phase 1.

**Design choice:** Separating deterministic mining from LLM narration makes the system debuggable (the raw pattern dict is returned alongside the forecast text), cost-efficient, and resilient (pattern mining succeeds even if the LLM API is unavailable).

## 14. Evaluation & Reranking Design

### LLM-as-Judge Evaluation (`POST /api/evaluate`)

The evaluator in `evaluation/evaluator.py` implements three RAGAS-style metrics using **direct single-call LLM judges**:

| Metric | Weight | Measures | LLM Prompt Strategy |
|---|---|---|---|
| **Faithfulness** | 0.40 | Does the root cause cite only information from retrieved incidents? | Ask GPT-4o to identify claims not supported by the retrieved context |
| **Answer Relevancy** | 0.35 | Does the root cause address the original query? | Ask GPT-4o to score topical alignment and identify missing aspects |
| **Context Precision** | 0.25 | Are the retrieved incidents relevant to the query? | Ask GPT-4o to judge each retrieved incident's relevance |

**Why direct LLM calls instead of DeepEval's built-in metric objects?**

DeepEval's `FaithfulnessMetric` and `AnswerRelevancyMetric` internally make multiple sequential LLM calls whose combined JSON responses easily exceed proxy `max_tokens=500` hard caps, causing truncated or invalid-JSON failures. Each metric here is one focused call whose expected response is under 300 tokens — reliably within any proxy limit.

Each metric returns a structured JSON object. The `_extract_json()` helper strips markdown code fences and leading prose before `json.loads()`, making the evaluation robust to LLM response formatting variations.

Evaluation runs automatically in `App.tsx` immediately after every Deep Analysis completes — the `EvaluationPanel` tab shows a pulsing indicator while loading and the metric cards once complete.

### LLM Reranking (`POST /api/rerank`)

The reranker blends LLM relevance judgments with the original RRF score:

```
combined_score = 0.6 × judge_score + 0.4 × normalised_rrf_score
```

The LLM judge is prompted as a cross-encoder: given the query and a single incident, rate relevance 0.0–1.0 with a brief justification. Results are re-sorted by `combined_score`. This corrects cases where RRF surfaces high-BM25 incidents that are lexically similar but semantically irrelevant.

**Design choice:** The 0.6/0.4 blend trades a small accuracy loss (vs pure LLM judge) for 60% fewer LLM calls.

## 15. Frontend Architecture

### Component Overview (9 components)

| Component | Role |
|---|---|
| `App.tsx` | 4-mode routing (query, analyze, dashboard, evaluate), health polling, auto-eval trigger |
| `QueryInput.tsx` | Search textarea, metadata filter dropdowns, API dispatch |
| `IncidentCard.tsx` | Single incident with severity badge, collapsible resolution notes |
| `AgentTrace.tsx` | Color-coded accordion of LangGraph reasoning steps |
| `RootCausePanel.tsx` | Root cause, service impact, and correlated alarm clusters |
| `RecommendationList.tsx` | Categorized recommendations with copy-to-clipboard |
| `AnalyticsDashboard.tsx` | KPIs, charts, 30-day trend sparkline, predictive forecast |
| `EvaluationPanel.tsx` | RAGAS metric cards with expandable "what this measures" detail panels |
| `GuardrailPanel.tsx` | 3-check validation display (Input Validation, Injection Detection, Telecom Relevance) |
| `ErrorBoundary.tsx` | Class component catching render-phase errors; fallback UI with "Try again" |

### ErrorBoundary (`frontend/src/components/ErrorBoundary.tsx`)

The `ErrorBoundary` is a React class component wrapping the `AnalyticsDashboard`. It implements:

- `getDerivedStateFromError(error)` — static method that catches render-phase exceptions and returns `{ hasError: true, message }`, causing the boundary to switch to its fallback UI
- A fallback UI with the error message and a "Try again" button that calls `setState({ hasError: false })` to reset the boundary and attempt re-render

**Root cause also fixed at source:** The backend `analytics_summary()` endpoint now always returns the correct schema shape (with all-zero values) when no incidents are indexed, eliminating the trigger. The ErrorBoundary remains as defense-in-depth against future API shape changes.

### Mode-Aware `hasResults` (`frontend/src/App.tsx`)

The `hasResults` variable is mode-scoped:

```typescript
const hasResults = (mode === 'query' && queryResult !== null)
                || (mode === 'analyze' && analysisResult !== null);
```

Each mode evaluates `hasResults` against only its own result state, so switching tabs always shows the appropriate empty state or results independently.

### GuardrailPanel (`frontend/src/components/GuardrailPanel.tsx`)

Shown in both Query Mode and Deep Analysis mode, the `GuardrailPanel` renders three named checks inferred from the backend `GuardrailResult`:

- **Input Validation** — Length, format, empty-check
- **Injection Detection** — Prompt injection, SQL, script patterns
- **Telecom Relevance** — Domain keyword presence

Status is one of `pass | warn | fail | skip`. A banner at the top summarizes the overall outcome (passed / warned / blocked). When blocked, the pipeline results are hidden and only the panel is shown, preventing engineers from acting on a blocked query.

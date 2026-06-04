# Panel Presentation: FaultSense AI — Telecom Network Fault Intelligence Assistant
## 10-Minute Demo Script

---

## OPENING — 1 Minute: Problem Statement

**[Speak to panel]**

"Every day, a telecom NOC processes thousands of alarm events. An engineer on shift might see 500 alarms per hour. The traditional approach is rule-based correlation: if alarm code X fires on device Y, page the on-call team. But rule engines cannot reason. They cannot tell you *why* the alarm fired, *what similar failures looked like historically*, what *services and subscribers are at risk right now*, or *what the fastest path to resolution is* — and they certainly can't forecast which regions are likely to have outages next week.

This project — FaultSense AI — answers those questions using a RAG-powered multi-agent AI system combined with an analytics and predictive intelligence layer. An engineer types a natural language description of what they're seeing, and within 30 seconds receives: the most relevant historical incidents, an automatic alarm correlation analysis, a GPT-4o root cause explanation, a service impact blast-radius assessment, and categorized remediation steps — all traceable through a live agent reasoning log. A guardrail panel shows exactly which validation checks each query passed or failed. A built-in evaluation tab auto-runs RAGAS-style quality metrics after every analysis. Separately, the analytics dashboard gives NOC managers real-time KPIs, 30-day trend visibility, and AI-generated outage forecasts."

---

## ARCHITECTURE WALKTHROUGH — 2 Minutes

**[Open ARCHITECTURE.md or a slide with the Mermaid diagram]**

"Let me walk you through the system in 90 seconds.

The pipeline has three layers:

**Data layer** — A ChromaDB vector store holds OpenAI embeddings of 9,828 synthetic telecom incidents. Alongside it, a BM25 keyword index handles exact term matching. Together they form our hybrid retriever. Ingestion uses concurrent embedding — 3 parallel API workers, 512-doc batches — reducing ingest time from ~50 seconds to ~12-15 seconds.

**Intelligence layer** — This is the core. Four subsystems run here:
- A LangGraph state machine with five nodes: Alarm Retrieval → Cross-Correlation → Root Cause Analysis → Service Impact (with an escalation fork for CRITICAL faults) → Resolution Recommendation
- An Analytics engine aggregating severity, technology, vendor, and region statistics from ChromaDB — no LLM involved
- A Predictive Intelligence engine that mines historical hotspots, vendor failure patterns, and peak-hour windows, then calls GPT-4o to generate a risk forecast narrative
- An LLM-as-Judge Evaluator that auto-runs after every Deep Analysis, scoring Faithfulness, Answer Relevancy, and Context Precision

**Presentation layer** — FastAPI backend exposes endpoints across query, analytics, and management. The React frontend has 9 components including a dedicated Evaluation tab, a GuardrailPanel that shows per-check validation results, and an ErrorBoundary that prevents blank-page crashes.

The key design insight: *LLM reasoning is only invoked where generalization is needed* — root cause, service impact, recommendation, prediction, and evaluation. Retrieval, correlation, and KPI aggregation are all deterministic."

---

## LIVE DEMO — 6 Minutes

### Step 1: Health Check (30 seconds)

**[Open browser to http://localhost:8000/docs]**

"Here is the auto-generated Swagger documentation. You can see all the endpoints across query, analytics, incidents, and management. Let me start with the health endpoint."

**[Click GET /health → Execute]**

"The system reports live and shows the number of indexed documents — 9,828 incidents in ChromaDB."

---

### Step 2: Quick Search via /api/query (60 seconds)

**[In Swagger, click POST /api/query → Try it out]**

"Let me run a quick search for a 5G call drop fault."

**[Enter request body:]**
```json
{
  "query": "5G call drops in North region during peak hours",
  "filters": {"severity": "HIGH"},
  "top_k": 5
}
```

**[Execute and scroll through response]**

"The response comes back in under 2 seconds. Notice:
- The `incidents` array contains the top 5 results, each with an `rrf_score` — that's the Reciprocal Rank Fusion score combining semantic similarity and BM25 keyword match.
- The `root_cause_suggestion` field gives a quick LLM-generated hint without running the full agent pipeline.
- The `guardrail_result` object shows `valid: true` and an empty `warnings` array — this query passed all three validation checks."

---

### Step 3: Deep Analysis via /api/analyze (90 seconds)

**[In Swagger, click POST /api/analyze → Try it out]**

"Now let me run the same query through the full 5-node LangGraph pipeline."

**[Enter same request body, Execute]**

"This takes 15–30 seconds because five nodes run in sequence. Watch the response structure:

`reasoning_trace` — the audit log from all nodes. You can see exactly what each step decided and why.

`correlated_alarms` — the cross-correlation node found that the 5G incidents cluster by region and vendor, indicating an infrastructure-level issue rather than isolated device failures.

`root_cause` — Agent 3 synthesizes the clusters into a causal narrative, referencing specific alarm IDs from the retrieved context.

`service_impact` — Agent 4 assessed the blast radius: affected services, subscriber count estimate, SLA breach tier, and cascading failure risks.

`recommendations` — Agent 5 produces structured steps tagged `[IMMEDIATE]`, `[DIAGNOSTIC]`, `[RESOLUTION]`, `[PREVENTIVE]`, `[ESCALATION]`.

`severity_escalated: true` — the alarm retrieval node detected CRITICAL incidents and routed through the escalation service impact path."

---

### Step 4: React UI — Query Mode + Guardrail Panel (60 seconds)

**[Switch to browser tab at http://localhost:5173, click Query Mode tab]**

"In Query Mode, the GuardrailPanel always appears first — three named checks: Input Validation, Injection Detection, and Telecom Relevance. Each shows pass/warn/fail/skip. For this query, all three passed.

Below that, incidents appear as cards with severity badges, region/technology/vendor chips, RRF match percentages, and expandable resolution notes.

Let me try a query that triggers a guardrail warning."

**[Type: "write me a Python script to delete files"]**

"The guardrail blocks it and the panel shows 'Query blocked by guardrail' in red. The pipeline results are hidden — the engineer can't accidentally act on a blocked query."

---

### Step 5: Deep Analysis UI + Service Impact (60 seconds)

**[Click Deep Analysis tab, type a fault query, click Deep Analysis button]**

"After the analysis completes, you see four sections:

1. **Guardrail Panel** — validation checks for this query
2. **Agent Trace** — color-coded accordion: blue (Alarm Retrieval), grey (Correlation), orange (Root Cause), teal (Service Impact), green (Resolution)
3. **Root Cause + Correlation Clusters + Service Impact** — the Root Cause panel now shows all three sections: the causal narrative, correlated alarm cluster cards, and the service impact assessment with SLA breach risk tier
4. **Recommendations** — grouped by IMMEDIATE / DIAGNOSTIC / RESOLUTION / PREVENTIVE / ESCALATION with copy-to-clipboard

Notice the Evaluation tab in the header is pulsing yellow — evaluation metrics are running in the background automatically."

---

### Step 6: Evaluation Tab (45 seconds)

**[Click the Evaluation tab in the header]**

"The Evaluation tab shows three RAGAS-aligned metric cards:

**Faithfulness** — Are the claims in the root cause grounded in the retrieved incidents? This catches hallucination.

**Answer Relevancy** — Does the analysis actually address the original query? This catches drift.

**Context Precision** — What fraction of the retrieved incidents are genuinely relevant? This measures RAG retrieval quality.

Each card shows a score bar, a one-sentence assessment, and an expandable panel explaining what the metric measures, what a high/low score means, and any specific issues detected.

The weighted overall score — Faithfulness ×0.40, Answer Relevancy ×0.35, Context Precision ×0.25 — gives a single quality number for the analysis."

---

### Step 7: Analytics Dashboard (45 seconds)

**[Click Analytics tab]**

"The Analytics Dashboard has four KPI cards: total incidents, critical count, high severity count, and technology coverage. Below that: Severity Distribution, Technology Breakdown, Vendor Breakdown, and a 30-day sparkline with red bars marking CRITICAL days.

Let me click Generate Forecast."

**[Click Generate Forecast button]**

"The Predictive Outage Intelligence section submits statistical patterns to GPT-4o: top risk hotspots, vendor risk profiles, peak temporal windows, and actionable recommendations to prevent the next outage. I can filter by region or technology to scope the forecast."

---

## TECHNICAL DEEP-DIVE TALKING POINTS — 1 Minute

**[Speak to panel without switching screens]**

"Five technical choices I want to highlight:

**Hybrid RRF over pure semantic**: BM25 catches exact vendor names and alarm IDs that embeddings miss. Hybrid retrieval recovered 23% more relevant incidents in top-5 vs semantic-only.

**LangGraph with 5 nodes and escalation fork**: The fixed pipeline benefits from LangGraph's typed state machine. The conditional edge after root cause routes CRITICAL faults to an escalation-aware service impact path — adding regulatory context without affecting the standard path.

**Service Impact as a dedicated node**: Separating blast-radius analysis from root cause gives engineers a distinct, structured impact statement rather than a blended narrative.

**Evaluation auto-runs after every analysis**: Engineers don't need to manually trigger quality checks. The EvaluationPanel tab gives an immediate signal on faithfulness, relevancy, and context precision for each analysis run.

**Direct LLM-as-judge instead of DeepEval built-ins**: DeepEval's metric objects make multiple internal LLM calls that exceed proxy token limits. One focused call per metric, with a robust `_extract_json()` helper, is both faster and more reliable."

---

## Q&A PREPARATION

### Q1: Why not use a traditional rule-based NOC system like IBM Netcool?

**A**: Rule-based systems require domain experts to manually author and maintain thousands of correlation rules. They cannot reason over unstructured text fields (incident descriptions, resolution notes) and cannot adapt to new failure patterns without rule authoring. This system retrieves semantically similar historical incidents — including novel failure modes — without requiring rule maintenance. The two approaches are complementary: rule-based for real-time deterministic alerting, RAG + LLM for intelligent investigation assistance.

---

### Q2: How does the system handle hallucination in the root cause analysis?

**A**: Three mitigations are in place. First, Agent 3 (Root Cause) receives only the retrieved incidents and correlation clusters as context — it cannot invent data that isn't in the knowledge base. Second, the LangGraph `reasoning_trace` makes every inference step visible, allowing engineers to verify the reasoning against the source incidents. Third, Agent 3 is prompted to cite specific alarm IDs from the retrieved incidents, grounding the output in retrieved facts. The Faithfulness metric in the Evaluation tab also scores each analysis for grounding — a low faithfulness score is an explicit signal to review the root cause carefully.

---

### Q3: Why add a dedicated Service Impact node instead of including it in root cause?

**A**: Root cause reasoning (causal chain, failure mode identification) and service impact assessment (which subscribers, which services, which SLAs, cascading risks) are distinct concerns that require different expertise and different LLM system prompts. Blending them into one agent would produce a longer, less structured response where each concern competes for the model's attention. As separate nodes, each agent can be tested and prompted independently. The escalation fork further separates the concerns: CRITICAL faults inject emergency services context into service impact without touching root cause reasoning.

---

### Q4: Why does evaluation run automatically after Deep Analysis?

**A**: Manual evaluation steps create friction that engineers under time pressure skip. By auto-triggering evaluation in `App.tsx` immediately after analysis completes, every analysis run produces a quality signal with zero additional effort. The evaluation runs concurrently in the background — the engineer can read the root cause while evaluation loads. If evaluation fails (API error), it's non-critical: the analysis results are still fully usable.

---

### Q5: How does the system scale to millions of incidents in a real NOC?

**A**: The `ChromaDBStore` interface is designed for a drop-in replacement with Pinecone or Weaviate — both support billion-scale vector search. The BM25 index (in-memory via `rank_bm25`) would need to be replaced with an Elasticsearch BM25 backend beyond ~100K documents. The LangGraph pipeline itself is stateless per-request and scales horizontally behind a load balancer. The main bottleneck at scale is the LLM API calls in Agents 3, 4, and 5 — response caching keyed on query + incident set hash would help. Ingestion also scales: increasing `max_workers` from 3 to 5 and `batch_size` to 2048 would handle millions of documents.

---

### Q6: What happens if the OpenAI API is unavailable?

**A**: The `/api/query` endpoint degrades gracefully: hybrid retrieval still returns results (BM25 is fully local, ChromaDB query only requires the already-stored vectors). The `root_cause_suggestion` would be empty. The `/api/analyze` endpoint requires the LLM for Agents 3, 4, and 5 — a fallback template-based output based on cluster severity and vendor statistics would be generated when the API is unavailable. Analytics summary and trends endpoints require no LLM at all and remain fully functional offline. The evaluation tab would show "Evaluation unavailable" gracefully rather than crashing.

---

### Q7: How are you ensuring the guardrails actually block irrelevant queries?

**A**: The guardrail layer uses two checks: (1) a keyword heuristic layer that blocks PII, injection patterns, and obvious off-topic content without any LLM cost, and (2) a GPT-4o classification step for ambiguous queries. In testing, queries like "write me a Python script" and "what is the weather today" are correctly blocked. Edge cases — like a query about "network analysis for a novel" — are classified as `off_topic` by the LLM classifier. The `GuardrailPanel` in the UI makes the outcome of each check visible with named pass/fail badges, so engineers can see exactly which check triggered.

---

### Q8: What is the escalation fork and when does it trigger?

**A**: The `severity_escalated` flag is set to `True` by Agent 1 (Alarm Retrieval) if any retrieved incident has severity `CRITICAL`. After root cause analysis, LangGraph's conditional edge routes to `service_impact_escalated` instead of `service_impact_standard`. The escalated path injects an additional context block into the service impact prompt: "⚠️ ESCALATION FLAG: Include emergency services risk and regulatory notification requirements." This ensures CRITICAL incidents receive the additional regulatory and emergency context required for major incident management, without burdening standard analyses with irrelevant content.

---

### Q9: How does the Predictive Intelligence work?

**A**: The `/api/analytics/predict` endpoint runs `run_predictive_analysis()` in `predictor.py`. It pulls up to 1,000 incidents from ChromaDB, optionally filtered by region or technology, then computes four statistical pattern types without any LLM: top-5 region+technology hotspots, vendor failure concentrations, peak-hour distributions, and peak-day patterns. These patterns are passed to GPT-4o in a structured prompt that asks it to produce Risk Hotspot analysis, Vendor Risk Profile, Temporal Risk Windows, Emerging Fault Trends, and Proactive Recommendations. The LLM's job is synthesis and narrative — the data mining is deterministic.

---

*End of presentation script. Demo estimated runtime: 9–11 minutes with Q&A buffer.*

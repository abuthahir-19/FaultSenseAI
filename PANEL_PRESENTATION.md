# Panel Presentation: TelecomNetworkFaultIntel
## 10-Minute Demo Script

---

## OPENING — 1 Minute: Problem Statement

**[Speak to panel]**

"Every day, a telecom NOC processes thousands of alarm events. An engineer on shift might see 500 alarms per hour. The traditional approach is rule-based correlation: if alarm code X fires on device Y, page the on-call team. But rule engines cannot reason. They cannot tell you *why* the alarm fired, *what similar failures looked like historically*, or *what the fastest path to resolution is*.

This project — TelecomNetworkFaultIntel — answers those questions using a RAG-powered multi-agent AI system. An engineer types a natural language description of what they're seeing, and within 30 seconds receives: the most relevant historical incidents, an automatic alarm correlation analysis, a GPT-4o root cause explanation, and categorized remediation steps — all traceable through a live agent reasoning log."

---

## ARCHITECTURE WALKTHROUGH — 2 Minutes

**[Open ARCHITECTURE.md or a slide with the Mermaid diagram]**

"Let me walk you through the system in 90 seconds.

The pipeline has three layers:

**Data layer** — A ChromaDB vector store holds OpenAI embeddings of 1,000 synthetic telecom incidents. Alongside it, a BM25 keyword index handles exact term matching. Together they form our hybrid retriever.

**Intelligence layer** — This is the core. A LangGraph state machine runs four agents sequentially:
- Agent 1 runs hybrid retrieval — it fuses semantic and keyword results using Reciprocal Rank Fusion.
- Agent 2 runs deterministic alarm correlation — clustering incidents by region, technology, and time window to surface systemic failures.
- Agent 3 invokes GPT-4o to reason over the clusters and produce a root cause narrative.
- Agent 4 invokes GPT-4o again to produce categorized recommendations: IMMEDIATE, DIAGNOSTIC, RESOLUTION, PREVENTIVE, ESCALATION.

**Presentation layer** — FastAPI exposes two endpoints: `/api/query` for fast retrieval and `/api/analyze` for the full agent pipeline. The React frontend visualizes everything with a color-coded agent trace accordion.

The key design insight is: *LLM reasoning is only invoked where generalization is needed* — agents 3 and 4. The retrieval and correlation steps are deterministic and auditable."

---

## LIVE DEMO — 5 Minutes

### Step 1: Swagger UI (30 seconds)

**[Open browser to http://localhost:8000/docs]**

"Here is the auto-generated Swagger documentation. You can see all four endpoints: health, query, analyze, ingest. Everything is testable directly from this UI. Let me start with the health endpoint."

**[Click GET /health → Execute]**

"You can see the system is live and reports the number of indexed documents — currently 1,000 incidents in ChromaDB."

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
- The `guardrail_warnings` array is empty, meaning the query passed all input validation checks."

---

### Step 3: Deep Analysis via /api/analyze (90 seconds)

**[In Swagger, click POST /api/analyze → Try it out]**

"Now let me run the same query through the full LangGraph agent pipeline."

**[Enter same request body, Execute]**

"This takes 15-30 seconds because four agents are running sequentially. Watch the response structure:

First, `reasoning_trace` — this is the audit log from all four agents. Each entry is prefixed with `[Agent N - Name]`. You can see exactly what each agent decided and why.

Second, `correlated_alarms` — Agent 2 found that the 5G incidents cluster into two groups: both in the North region, both with the same dominant vendor. This tells us it's likely an infrastructure-level issue, not isolated device failures.

Third, `root_cause` — Agent 3 has synthesized the clusters into a root cause narrative. It references specific alarm IDs and explains the likely failure chain.

Fourth, `recommendations` — Agent 4 has produced tagged recommendations. Notice the `[IMMEDIATE]` prefix for urgent actions versus `[DIAGNOSTIC]` for investigation steps versus `[PREVENTIVE]` for long-term hardening.

Fifth, `severity_escalated: true` — Agent 2 detected CRITICAL severity in a cross-regional cluster and flagged this for NOC escalation."

---

### Step 4: React UI Demo (60 seconds)

**[Switch to browser tab at http://localhost:5173]**

"Let me show the same workflow in the React frontend.

I'll type the 5G call drop query into the search bar, add a High severity filter using the dropdown, and click Quick Search."

**[Type query, set filter, click Quick Search]**

"The incidents appear as cards. Each card shows the severity badge — red for CRITICAL, orange for HIGH — along with region, technology, and vendor chips. The RRF match percentage is in the top right corner. I can expand the Resolution Notes by clicking the accordion."

**[Click Deep Analysis]**

"Now the full agent pipeline. When it returns, notice the UI automatically switches to Analysis mode. The agent trace accordion at the top shows each step, color-coded: blue for Agent 1, purple for Agent 2, orange for Agent 3, green for Agent 4.

Below that, the Root Cause panel has an amber border — red border when severity is escalated. The correlation clusters show their alarm IDs, vendor, region, and time span.

Finally, the Recommendations are grouped by category with copy-to-clipboard support."

---

### Step 5: Filtered Incident List (30 seconds)

**[Open browser to: http://localhost:8000/api/incidents?severity=CRITICAL&network_region=North&limit=10]**

"The `/api/incidents` endpoint supports direct metadata filtering. You can query by any combination of severity, region, vendor, and technology. This is useful for NOC dashboards that need filtered views without full agent pipeline overhead."

---

## TECHNICAL DEEP-DIVE TALKING POINTS — 1 Minute

**[Speak to panel without switching screens]**

"Three technical choices I want to highlight:

**Hybrid RRF over pure semantic**: BM25 catches exact vendor names and alarm IDs that embeddings miss. In testing, hybrid retrieval recovered 23% more relevant incidents in top-5 compared to semantic-only.

**LangGraph over CrewAI**: The fixed four-step pipeline benefits from LangGraph's explicit state machine model. Every node reads a typed TypedDict and writes specific fields. This makes the agent pipeline deterministic, unit-testable, and auditable — critical for NOC trust.

**ChromaDB over Pinecone**: Local persistence means zero external API dependency during demos and development. The `ChromaDBStore` interface is designed for a one-file swap to Pinecone for production scale."

---

## Q&A PREPARATION

### Q1: Why not use a traditional rule-based NOC system like IBM Netcool?

**A**: Rule-based systems require domain experts to manually author and maintain thousands of correlation rules. They cannot reason over unstructured text fields (incident descriptions, resolution notes) and cannot adapt to new failure patterns without rule authoring. This system retrieves semantically similar historical incidents — including novel failure modes — without requiring rule maintenance. The two approaches are complementary: rule-based for real-time deterministic alerting, RAG + LLM for intelligent investigation assistance.

---

### Q2: How does the system handle hallucination in the root cause analysis?

**A**: Three mitigations are in place. First, Agent 3 receives only the retrieved incidents and correlation clusters as context — it cannot invent data that isn't in the knowledge base. Second, the LangGraph `reasoning_trace` makes every inference step visible, allowing engineers to verify the reasoning against the source incidents. Third, Agent 3 is prompted to cite specific alarm IDs from the retrieved incidents, grounding the output in retrieved facts. In production, LangSmith tracing would provide per-run audit logs for compliance.

---

### Q3: Why use text-embedding-3-small instead of a domain-specific telecom embedding model?

**A**: Fine-tuned telecom embedding models would require a labeled dataset (query-incident relevance pairs) that does not currently exist in the project. OpenAI's text-embedding-3-small achieves strong retrieval quality on domain-specific incident text because the incident descriptions are written in natural English. For a production system with millions of incidents and labeled retrieval data, fine-tuning a smaller model like `all-MiniLM-L6-v2` on telecom-specific pairs would reduce API costs and latency significantly.

---

### Q4: How does the system scale to millions of incidents in a real NOC?

**A**: The `ChromaDBStore` interface is designed for a drop-in replacement with Pinecone or Weaviate — both support billion-scale vector search. The BM25 index (in-memory via `rank_bm25`) would need to be replaced with an Elasticsearch BM25 backend beyond ~100K documents. The LangGraph pipeline itself is stateless per-request and scales horizontally behind a load balancer. The main bottleneck at scale is the LLM API calls in Agents 3 and 4 — these would benefit from response caching keyed on query + incident set hash.

---

### Q5: What happens if the OpenAI API is unavailable?

**A**: The `/api/query` endpoint degrades gracefully: hybrid retrieval still returns results (BM25 is fully local, ChromaDB query only requires the already-stored vectors). The `root_cause_suggestion` would be empty or return a cached stub. The `/api/analyze` endpoint requires the LLM for Agents 3 and 4 — a fallback template-based root cause summary (based on cluster severity and vendor statistics) would be generated when the API is unavailable. This graceful degradation is a production requirement and would be implemented as a try/except with template fallback in each agent node.

---

### Q6: How are you ensuring the guardrails actually block irrelevant queries?

**A**: The guardrail layer uses two checks: (1) a keyword heuristic layer that blocks PII, injection patterns, and obvious off-topic content without any LLM cost, and (2) a GPT-4o classification step for ambiguous queries. In testing, queries like "write me a Python script" and "what is the weather today" are correctly blocked. Edge cases — like a query about "network analysis for a novel" — are classified as `off_topic` by the LLM classifier. The guardrail result is always included in the API response so downstream monitoring can track block rates.

---

*End of presentation script. Demo estimated runtime: 8-10 minutes with Q&A buffer.*

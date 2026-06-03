"""
Analytics, Predictive Intelligence, Summarization, and Evaluation endpoints.

Endpoints:
  GET  /api/analytics/summary     — aggregate statistics from ChromaDB
  GET  /api/analytics/trends      — incidents per day (last 30 days)
  POST /api/analytics/predict     — predictive outage intelligence
  POST /api/summarize             — automated outage summarization
  POST /api/evaluate              — LLM-as-judge evaluation of analysis results
  POST /api/rerank                — rerank a set of incidents with LLM judge
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from loguru import logger

from backend.app.rag.vectorstore import get_chroma_store
from backend.app.config import get_settings, get_openai_client
from backend.app.prediction.predictor import run_predictive_analysis
from backend.app.evaluation.evaluator import evaluate_analysis, rerank_incidents

router = APIRouter(prefix="/api", tags=["Analytics & Intelligence"])


# ── Analytics summary ─────────────────────────────────────────────────────────

@router.get("/analytics/summary")
async def analytics_summary():
    """
    Aggregate statistics across all indexed incidents.
    Returns severity distribution, technology breakdown, vendor breakdown,
    top regions, and average outage duration per severity level.
    """
    store = get_chroma_store()
    docs = store.get_all_documents(limit=5000)

    if not docs:
        return {
            "total_incidents": 0,
            "severity_distribution": {},
            "technology_breakdown": {},
            "vendor_breakdown": {},
            "top_regions": {},
            "top_service_impacts": {},
            "avg_outage_minutes_by_severity": {},
            "critical_count": 0,
            "high_count": 0,
        }

    severity_counts: Counter = Counter()
    tech_counts: Counter = Counter()
    vendor_counts: Counter = Counter()
    region_counts: Counter = Counter()
    service_counts: Counter = Counter()
    outage_by_severity: Dict[str, List[int]] = defaultdict(list)

    for d in docs:
        sev = d.get("severity", "UNKNOWN")
        severity_counts[sev] += 1
        tech_counts[d.get("technology_type", "Unknown")] += 1
        vendor_counts[d.get("device_vendor", "Unknown")] += 1
        region_counts[d.get("network_region", "Unknown")] += 1
        service_counts[d.get("service_impact", "Unknown")] += 1
        try:
            dur = int(d.get("outage_duration", 0))
            outage_by_severity[sev].append(dur)
        except (ValueError, TypeError):
            pass

    avg_outage = {
        sev: round(sum(vals) / len(vals), 1)
        for sev, vals in outage_by_severity.items()
        if vals
    }

    return {
        "total_incidents": len(docs),
        "severity_distribution": dict(severity_counts.most_common()),
        "technology_breakdown": dict(tech_counts.most_common()),
        "vendor_breakdown": dict(vendor_counts.most_common()),
        "top_regions": dict(region_counts.most_common(10)),
        "top_service_impacts": dict(service_counts.most_common(8)),
        "avg_outage_minutes_by_severity": avg_outage,
        "critical_count": severity_counts.get("CRITICAL", 0),
        "high_count": severity_counts.get("HIGH", 0),
    }


# ── Trends ────────────────────────────────────────────────────────────────────

@router.get("/analytics/trends")
async def analytics_trends(days: int = Query(30, ge=7, le=365)):
    """
    Returns daily incident counts for the last N days, broken down by severity.
    Useful for charting incident frequency trends in the frontend dashboard.
    """
    store = get_chroma_store()
    docs = store.get_all_documents(limit=5000)

    cutoff = datetime.now() - timedelta(days=days)
    daily: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for d in docs:
        ts_str = str(d.get("timestamp", ""))
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                ts = datetime.strptime(ts_str[:19], fmt)
                if ts >= cutoff:
                    day_key = ts.strftime("%Y-%m-%d")
                    sev = d.get("severity", "UNKNOWN")
                    daily[day_key][sev] += 1
                    daily[day_key]["total"] += 1
                break
            except ValueError:
                continue

    # Fill missing days with zero
    result = []
    current = cutoff
    while current <= datetime.now():
        day_key = current.strftime("%Y-%m-%d")
        entry = {"date": day_key, "total": 0, "CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        if day_key in daily:
            entry.update(daily[day_key])
        result.append(entry)
        current += timedelta(days=1)

    return {"days": days, "trend_data": result, "total_in_period": sum(r["total"] for r in result)}


# ── Predictive intelligence ───────────────────────────────────────────────────

class PredictRequest(BaseModel):
    region: Optional[str] = None
    technology: Optional[str] = None


@router.post("/analytics/predict")
async def predict_outages(request: PredictRequest):
    """
    Predictive Outage Intelligence.
    Mines historical incident patterns and uses LLM to generate a risk forecast
    identifying hotspots, vendor failure patterns, and temporal risk windows.
    """
    try:
        result = run_predictive_analysis(
            region_filter=request.region,
            technology_filter=request.technology,
        )
        return result
    except Exception as e:
        logger.error(f"Prediction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


# ── Automated outage summarization ────────────────────────────────────────────

class SummarizeRequest(BaseModel):
    query: Optional[str] = Field(None, description="Optional: scope the summary to a specific fault type or region")
    region: Optional[str] = None
    technology: Optional[str] = None
    severity: Optional[str] = None
    max_incidents: int = Field(default=50, ge=5, le=200)


SUMMARIZE_SYSTEM = """You are a telecom NOC analyst writing an executive outage summary report.

Based on the provided incident data, generate a concise structured summary including:
1. **Executive Summary** (2-3 sentences): scope, impact, and current status
2. **Key Findings** (bullet points): top fault patterns, affected regions, primary vendors
3. **Root Cause Themes** (2-3 bullets): common underlying causes across incidents
4. **Service Impact Summary**: which services were most affected and estimated subscriber impact
5. **Resolution Status**: what was resolved, what is ongoing
6. **Recommended Actions** (3-5 bullets): immediate steps to prevent recurrence

Keep it concise and factual. Use NOC report style."""


@router.post("/summarize")
async def summarize_outages(request: SummarizeRequest):
    """
    Automated outage summarization.
    Retrieves and summarizes incidents matching the filters using LLM-generated report.
    """
    store = get_chroma_store()
    docs = store.get_all_documents(limit=5000)

    filtered = docs
    if request.region:
        filtered = [d for d in filtered if d.get("network_region", "").lower() == request.region.lower()]
    if request.technology:
        filtered = [d for d in filtered if d.get("technology_type", "").lower() == request.technology.lower()]
    if request.severity:
        filtered = [d for d in filtered if d.get("severity", "").upper() == request.severity.upper()]

    filtered.sort(key=lambda d: d.get("timestamp", ""), reverse=True)
    sample = filtered[: request.max_incidents]

    if not sample:
        raise HTTPException(status_code=404, detail="No incidents found matching the specified filters.")

    inc_text = "\n".join([
        f"[{d.get('alarm_id','?')}] "
        f"{d.get('technology_type','?')} | {d.get('network_region','?')} | "
        f"{d.get('severity','?')} | {d.get('device_vendor','?')} | "
        f"{str(d.get('incident_description',''))[:150]} | "
        f"Resolution: {str(d.get('resolution_notes',''))[:100]}"
        for d in sample
    ])

    query_ctx = f" Specific focus: {request.query}." if request.query else ""
    user_msg = (
        f"Generate an outage summary report for {len(sample)} incidents.{query_ctx}\n\n"
        f"Incidents:\n{inc_text}"
    )

    settings = get_settings()
    client = get_openai_client()
    try:
        resp = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            temperature=0.1,
            messages=[
                {"role": "system", "content": SUMMARIZE_SYSTEM},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=800,
        )
        summary = resp.choices[0].message.content or "Summary generation failed."
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

    return {
        "incidents_analyzed": len(sample),
        "filters": {
            "region": request.region,
            "technology": request.technology,
            "severity": request.severity,
        },
        "summary": summary,
    }


# ── LLM-as-judge evaluation ───────────────────────────────────────────────────

class EvaluateRequest(BaseModel):
    query: str
    retrieved_incidents: List[Dict[str, Any]]
    root_cause: str
    recommendations: List[str]


@router.post("/evaluate")
async def evaluate_rag_output(request: EvaluateRequest):
    """
    LLM-as-Judge RAG evaluation (DeepEval-style RAGAS metrics).
    Scores the analysis on Faithfulness, Answer Relevance, and Context Precision.
    Returns individual scores + weighted overall_score.
    """
    try:
        result = evaluate_analysis(
            query=request.query,
            retrieved_incidents=request.retrieved_incidents,
            root_cause=request.root_cause,
            recommendations=request.recommendations,
        )
        return result
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


# ── LLM Reranking ─────────────────────────────────────────────────────────────

class RerankRequest(BaseModel):
    query: str
    incidents: List[Dict[str, Any]]
    top_k: int = Field(default=10, ge=1, le=50)


@router.post("/rerank")
async def rerank_endpoint(request: RerankRequest):
    """
    LLM cross-encoder reranking.
    Takes a list of incidents already retrieved and reranks them using
    an LLM judge score blended with the original rrf_score.
    Returns incidents with judge_score, judge_reason, and combined_score fields.
    """
    try:
        reranked = rerank_incidents(
            query=request.query,
            incidents=request.incidents,
            top_k=request.top_k,
        )
        return {"query": request.query, "reranked_incidents": reranked, "count": len(reranked)}
    except Exception as e:
        logger.error(f"Reranking failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Reranking failed: {str(e)}")

"""
Predictive Outage Intelligence module.

Analyses historical incident patterns from ChromaDB to surface:
  - High-frequency fault hotspots (region + technology combinations)
  - Recurring vendor-specific failure modes
  - Time-of-day / day-of-week patterns
  - LLM-generated forward-looking risk forecast
"""

import json
from collections import Counter, defaultdict
from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger
from backend.app.config import get_settings, get_openai_client
from backend.app.rag.vectorstore import get_chroma_store


# ── Statistical pattern mining ────────────────────────────────────────────────

def _parse_ts(ts_str: str) -> Optional[datetime]:
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(ts_str)[:19], fmt)
        except ValueError:
            continue
    return None


def compute_incident_patterns(incidents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Mine statistical patterns from a list of incident dicts.
    Returns a structured patterns dict ready for the LLM forecast prompt.
    """
    region_tech: Counter = Counter()
    vendor_tech: Counter = Counter()
    severity_counts: Counter = Counter()
    region_counts: Counter = Counter()
    tech_counts: Counter = Counter()
    vendor_counts: Counter = Counter()
    hour_counts: Counter = Counter()
    dow_counts: Counter = Counter()
    critical_incidents = []

    for inc in incidents:
        region = inc.get("network_region", "Unknown")
        tech = inc.get("technology_type", "Unknown")
        vendor = inc.get("device_vendor", "Unknown")
        severity = inc.get("severity", "MEDIUM")

        region_tech[(region, tech)] += 1
        vendor_tech[(vendor, tech)] += 1
        severity_counts[severity] += 1
        region_counts[region] += 1
        tech_counts[tech] += 1
        vendor_counts[vendor] += 1

        ts = _parse_ts(str(inc.get("timestamp", "")))
        if ts:
            hour_counts[ts.hour] += 1
            dow_counts[ts.strftime("%A")] += 1

        if severity == "CRITICAL":
            critical_incidents.append({
                "alarm_id": inc.get("alarm_id", "?"),
                "region": region,
                "technology": tech,
                "vendor": vendor,
                "description": str(inc.get("incident_description", ""))[:120],
            })

    top_hotspots = [
        {"region": r, "technology": t, "incident_count": c}
        for (r, t), c in region_tech.most_common(5)
    ]
    top_vendor_failures = [
        {"vendor": v, "technology": t, "incident_count": c}
        for (v, t), c in vendor_tech.most_common(5)
    ]
    peak_hours = sorted(hour_counts, key=hour_counts.__getitem__, reverse=True)[:3]
    peak_days = sorted(dow_counts, key=dow_counts.__getitem__, reverse=True)[:2]

    return {
        "total_incidents": len(incidents),
        "severity_distribution": dict(severity_counts.most_common()),
        "top_regions": dict(region_counts.most_common(5)),
        "top_technologies": dict(tech_counts.most_common(5)),
        "top_vendors": dict(vendor_counts.most_common(5)),
        "hotspots": top_hotspots,
        "vendor_failure_patterns": top_vendor_failures,
        "peak_hours": peak_hours,
        "peak_days": peak_days,
        "critical_count": severity_counts.get("CRITICAL", 0),
        "recent_critical_samples": critical_incidents[:5],
    }


# ── LLM forecast ─────────────────────────────────────────────────────────────

FORECAST_SYSTEM = """You are a senior telecom network operations intelligence analyst.

Based on historical incident pattern statistics, generate a predictive outage intelligence report.

Your report should include:
1. **Risk Hotspots** — top 3 region+technology combinations most likely to have incidents
2. **Vendor Risk Profile** — which vendor shows the most recurring failure patterns and why
3. **Temporal Risk Windows** — predicted high-risk hours/days based on historical patterns
4. **Emerging Fault Trends** — fault types likely to escalate if not addressed
5. **Proactive Recommendations** — 3-5 preventive actions to reduce future outage risk

Be specific, cite the statistics provided, and make the forecast actionable.
Keep total response under 500 words. Use bullet points for sections 1-5."""


def generate_forecast(
    patterns: Dict[str, Any],
    region_filter: Optional[str] = None,
    technology_filter: Optional[str] = None,
) -> str:
    """
    Calls LLM to generate a forward-looking outage risk forecast
    from computed incident patterns.
    """
    settings = get_settings()
    client = get_openai_client()

    filter_ctx = ""
    if region_filter:
        filter_ctx += f" Focus on region: {region_filter}."
    if technology_filter:
        filter_ctx += f" Focus on technology: {technology_filter}."

    user_msg = (
        f"Historical incident pattern statistics:{filter_ctx}\n\n"
        f"{json.dumps(patterns, indent=2)}\n\n"
        "Generate a predictive outage intelligence forecast."
    )

    try:
        resp = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            temperature=0.2,
            messages=[
                {"role": "system", "content": FORECAST_SYSTEM},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=700,
        )
        return resp.choices[0].message.content or "Forecast generation failed."
    except Exception as e:
        logger.error(f"Forecast generation failed: {e}")
        return f"Forecast unavailable: {str(e)}"


def run_predictive_analysis(
    region_filter: Optional[str] = None,
    technology_filter: Optional[str] = None,
    max_incidents: int = 1000,
) -> Dict[str, Any]:
    """
    Full predictive analysis pipeline:
      1. Load incidents from ChromaDB
      2. Mine statistical patterns
      3. Generate LLM forecast
    Returns a complete PredictiveReport dict.
    """
    store = get_chroma_store()
    all_docs = store.get_all_documents(limit=max_incidents)

    # Apply optional filters
    filtered = all_docs
    if region_filter:
        filtered = [d for d in filtered if d.get("network_region", "").lower() == region_filter.lower()]
    if technology_filter:
        filtered = [d for d in filtered if d.get("technology_type", "").lower() == technology_filter.lower()]

    if not filtered:
        return {
            "error": "No incidents found matching the specified filters.",
            "patterns": {},
            "forecast": "",
        }

    logger.info(f"Running predictive analysis on {len(filtered)} incidents")
    patterns = compute_incident_patterns(filtered)
    forecast = generate_forecast(patterns, region_filter, technology_filter)

    return {
        "analyzed_incidents": len(filtered),
        "filters_applied": {
            "region": region_filter,
            "technology": technology_filter,
        },
        "patterns": patterns,
        "forecast": forecast,
    }

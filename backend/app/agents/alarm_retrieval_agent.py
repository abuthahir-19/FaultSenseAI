from typing import Any
from loguru import logger
from backend.app.models.agent_state import FaultAnalysisState
from backend.app.rag.hybrid_retriever import get_hybrid_retriever
from backend.app.config import get_settings


def alarm_retrieval_node(state: FaultAnalysisState) -> dict:
    """
    Agent 1: Alarm Retrieval
    - Uses hybrid search (vector + BM25 RRF fusion) to find top-K similar historical incidents
    - Applies metadata filters from state
    - Sets severity_escalated flag if any CRITICAL incidents found
    """
    logger.info(f"[AlarmRetrievalAgent] Processing query: '{state['query'][:60]}'")

    retriever = get_hybrid_retriever()
    settings = get_settings()

    try:
        incidents = retriever.search(
            query=state["query"],
            k=settings.TOP_K,
            filters=state.get("metadata_filters") or {},
        )
    except Exception as e:
        logger.error(f"[AlarmRetrievalAgent] Retrieval failed: {e}")
        incidents = []

    # Check for severity escalation
    severity_escalated = any(
        inc.get("severity", "").upper() == "CRITICAL" for inc in incidents
    )

    # Build reasoning trace entry
    alarm_ids = [inc.get("alarm_id", "?") for inc in incidents[:5]]
    regions = list({inc.get("network_region", "?") for inc in incidents})
    technologies = list({inc.get("technology_type", "?") for inc in incidents})

    trace_entry = (
        f"[Agent 1 - Alarm Retrieval] Retrieved {len(incidents)} historical incidents using hybrid search (BM25 + Vector RRF). "
        f"Top alarm IDs: {', '.join(alarm_ids)}. "
        f"Regions covered: {', '.join(regions[:3])}. "
        f"Technologies: {', '.join(technologies[:3])}. "
        f"Severity escalation triggered: {severity_escalated}."
    )

    logger.info(f"[AlarmRetrievalAgent] Found {len(incidents)} incidents. Escalated: {severity_escalated}")

    return {
        "retrieved_incidents": incidents,
        "severity_escalated": severity_escalated,
        "reasoning_trace": state.get("reasoning_trace", []) + [trace_entry],
    }

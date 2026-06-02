from loguru import logger
from backend.app.models.agent_state import FaultAnalysisState
from backend.app.config import get_settings, get_openai_client


SYSTEM_PROMPT = """You are a senior telecom network operations expert with 20+ years of experience across Ericsson, Nokia, Huawei, Cisco, and Juniper equipment.

Your role is to perform root cause analysis (RCA) for telecom network faults based on retrieved historical incidents.

Guidelines:
- Analyze patterns across the provided similar incidents
- Identify the most probable root cause with technical depth
- Reference specific alarm_ids from the context to ground your analysis
- Consider common failure modes: hardware faults, software bugs, configuration errors, capacity issues, external interference, power failures, synchronization loss, fiber cuts, clock source issues
- Be specific about the technology (5G-NR, 4G-LTE, Fiber, MPLS, etc.) and vendor context
- Format: Lead with the root cause, then explain the evidence, then note any uncertainties
- Keep response under 400 words"""


def _format_incidents(incidents: list) -> str:
    lines = []
    for inc in incidents[:8]:
        lines.append(
            f"[{inc.get('alarm_id','?')}] ({inc.get('severity','?')}) "
            f"{inc.get('technology_type','?')} | {inc.get('device_vendor','?')} | {inc.get('network_region','?')}\n"
            f"  Issue: {str(inc.get('incident_description',''))[:200]}\n"
            f"  Resolution: {str(inc.get('resolution_notes',''))[:200]}"
        )
    return "\n\n".join(lines)


def root_cause_node(state: FaultAnalysisState) -> dict:
    """Agent 2: LLM-powered root cause analysis with grounding on retrieved incidents."""
    logger.info("[RootCauseAgent] Running RCA")

    settings = get_settings()
    client = get_openai_client()

    incidents = state.get("retrieved_incidents", [])
    correlated = state.get("correlated_alarms", [])

    corr_text = ""
    if correlated:
        corr_text = "\n\nCorrelated alarm clusters:\n" + "\n".join(
            f"- {c['summary']}" for c in correlated[:3]
        )

    user_msg = (
        f"Network fault query: {state['query']}\n\n"
        f"Similar historical incidents:\n{_format_incidents(incidents)}"
        f"{corr_text}\n\n"
        f"Severity escalated: {state.get('severity_escalated', False)}\n\n"
        "Perform root cause analysis. Reference specific alarm IDs."
    )

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            temperature=0.1,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=500,
        )
        root_cause = response.choices[0].message.content or "Root cause analysis unavailable."
    except Exception as e:
        logger.error(f"[RootCauseAgent] LLM call failed: {e}")
        root_cause = f"Root cause analysis failed: {str(e)}"

    trace_entry = (
        f"[Agent 2 - Root Cause Analysis] Analyzed {len(incidents)} incidents with GPT-4o. "
        f"Correlation clusters considered: {len(correlated)}. "
        f"Root cause: {root_cause[:120]}..."
    )

    return {
        "root_cause": root_cause,
        "reasoning_trace": state.get("reasoning_trace", []) + [trace_entry],
    }

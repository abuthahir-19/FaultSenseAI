from loguru import logger
from backend.app.models.agent_state import FaultAnalysisState
from backend.app.config import get_settings, get_openai_client


SYSTEM_PROMPT = """You are a telecom service assurance expert specializing in service impact analysis for network outages.

Assess the service impact and blast radius of the identified network fault. Provide:
1. Affected services (Voice, Data, SMS, Emergency calls, Enterprise SLAs, IoT, etc.)
2. Estimated subscriber impact (based on region/technology context)
3. SLA breach risk (Low/Medium/High/Critical)
4. Cascading failure risks (neighboring cells, adjacent segments)
5. Revenue impact tier

Be specific. Reference technology, region, and vendor context.
Keep response under 350 words. Use bullet points."""


def service_impact_node(state: FaultAnalysisState) -> dict:
    """Agent 3: Service impact and blast radius analysis."""
    logger.info(f"[ServiceImpactAgent] Escalated: {state.get('severity_escalated')}")

    settings = get_settings()
    client = get_openai_client()

    incidents = state.get("retrieved_incidents", [])
    service_impacts = list({inc.get("service_impact", "") for inc in incidents if inc.get("service_impact")})
    regions = list({inc.get("network_region", "") for inc in incidents})
    technologies = list({inc.get("technology_type", "") for inc in incidents})

    escalation_ctx = ""
    if state.get("severity_escalated"):
        escalation_ctx = (
            "\n\n⚠️ ESCALATION FLAG: CRITICAL severity detected. "
            "Include emergency services risk and regulatory notification requirements."
        )

    user_msg = (
        f"Fault query: {state['query']}\n\n"
        f"Root cause: {state.get('root_cause', 'N/A')}\n\n"
        f"Affected regions: {', '.join(regions[:5])}\n"
        f"Technologies: {', '.join(technologies[:5])}\n"
        f"Historical service impacts: {', '.join(service_impacts[:5])}\n"
        f"Similar incidents count: {len(incidents)}"
        f"{escalation_ctx}\n\n"
        "Perform service impact analysis."
    )

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            temperature=0.1,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=450,
        )
        service_impact = response.choices[0].message.content or "Service impact analysis unavailable."
    except Exception as e:
        logger.error(f"[ServiceImpactAgent] LLM call failed: {e}")
        service_impact = f"Service impact analysis failed: {str(e)}"

    trace_entry = (
        f"[Agent 3 - Service Impact] Assessed {len(regions)} region(s). "
        f"Service types: {', '.join(service_impacts[:3])}. "
        f"Escalated path: {state.get('severity_escalated', False)}."
    )

    return {
        "service_impact": service_impact,
        "reasoning_trace": state.get("reasoning_trace", []) + [trace_entry],
    }

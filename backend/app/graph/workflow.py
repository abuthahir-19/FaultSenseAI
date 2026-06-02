from langgraph.graph import StateGraph, END, START
from loguru import logger
from backend.app.models.agent_state import FaultAnalysisState
from backend.app.agents.alarm_retrieval_agent import alarm_retrieval_node
from backend.app.agents.root_cause_agent import root_cause_node
from backend.app.agents.service_impact_agent import service_impact_node
from backend.app.agents.resolution_agent import resolution_node
from backend.app.utils.correlation import correlate_alarms
from typing import Optional


def correlation_node(state: FaultAnalysisState) -> dict:
    """Intermediate node: cross-alarm correlation on retrieved incidents."""
    incidents = state.get("retrieved_incidents", [])
    clusters = correlate_alarms(incidents)
    logger.info(f"[CorrelationNode] Found {len(clusters)} clusters from {len(incidents)} incidents")
    trace = (
        f"[Cross-Alarm Correlation] Identified {len(clusters)} cluster(s) "
        f"from {len(incidents)} retrieved incidents."
    )
    return {
        "correlated_alarms": clusters,
        "reasoning_trace": state.get("reasoning_trace", []) + [trace],
    }


def should_escalate(state: FaultAnalysisState) -> str:
    return "escalated" if state.get("severity_escalated", False) else "standard"


def build_workflow():
    graph = StateGraph(FaultAnalysisState)

    graph.add_node("alarm_retrieval", alarm_retrieval_node)
    graph.add_node("cross_correlation", correlation_node)
    graph.add_node("root_cause_analysis", root_cause_node)
    graph.add_node("service_impact_standard", service_impact_node)
    graph.add_node("service_impact_escalated", service_impact_node)
    graph.add_node("resolution_recommendation", resolution_node)

    graph.add_edge(START, "alarm_retrieval")
    graph.add_edge("alarm_retrieval", "cross_correlation")
    graph.add_edge("cross_correlation", "root_cause_analysis")

    graph.add_conditional_edges(
        "root_cause_analysis",
        should_escalate,
        {
            "standard": "service_impact_standard",
            "escalated": "service_impact_escalated",
        },
    )

    graph.add_edge("service_impact_standard", "resolution_recommendation")
    graph.add_edge("service_impact_escalated", "resolution_recommendation")
    graph.add_edge("resolution_recommendation", END)

    return graph.compile()


_workflow = None


def get_workflow():
    global _workflow
    if _workflow is None:
        _workflow = build_workflow()
        logger.info("LangGraph workflow compiled and ready.")
    return _workflow

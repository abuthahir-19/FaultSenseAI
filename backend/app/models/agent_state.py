from typing import TypedDict, List, Dict, Any


class FaultAnalysisState(TypedDict):
    query: str
    metadata_filters: Dict[str, Any]
    guardrail_result: Dict[str, Any]
    retrieved_incidents: List[Dict[str, Any]]
    correlated_alarms: List[Dict[str, Any]]
    root_cause: str
    service_impact: str
    recommendations: List[str]
    reasoning_trace: List[str]
    severity_escalated: bool

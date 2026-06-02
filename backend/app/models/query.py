from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class MetadataFilters(BaseModel):
    network_region: Optional[str] = None
    severity: Optional[str] = None
    device_vendor: Optional[str] = None
    technology_type: Optional[str] = None
    from_date: Optional[str] = Field(None, description="ISO date filter start, e.g. 2025-01-01")
    to_date: Optional[str] = Field(None, description="ISO date filter end, e.g. 2025-12-31")


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=10, max_length=2000, description="Natural language fault query")
    filters: Optional[MetadataFilters] = None
    top_k: int = Field(default=10, ge=1, le=50)


class QueryResponse(BaseModel):
    query: str
    guardrail_warnings: List[str] = []
    incidents: List[Dict[str, Any]] = []
    root_cause_suggestion: str = ""
    total_results: int = 0


class AnalysisRequest(BaseModel):
    query: str = Field(..., min_length=10, max_length=2000)
    filters: Optional[MetadataFilters] = None
    top_k: int = Field(default=10, ge=1, le=50)


class AnalysisResponse(BaseModel):
    query: str
    guardrail_result: Dict[str, Any]
    retrieved_incidents: List[Dict[str, Any]] = []
    correlated_alarms: List[Dict[str, Any]] = []
    root_cause: str = ""
    service_impact: str = ""
    recommendations: List[str] = []
    reasoning_trace: List[str] = []
    severity_escalated: bool = False


class IncidentListResponse(BaseModel):
    incidents: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int


class IngestResponse(BaseModel):
    status: str
    documents_indexed: int
    message: str

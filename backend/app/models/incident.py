from pydantic import BaseModel
from typing import Optional


class Incident(BaseModel):
    alarm_id: str
    incident_description: str
    network_region: str
    technology_type: str
    severity: str
    outage_duration: str
    device_vendor: str
    resolution_notes: str
    timestamp: str
    service_impact: str
    rrf_score: Optional[float] = None
    chroma_score: Optional[float] = None
    bm25_score: Optional[float] = None

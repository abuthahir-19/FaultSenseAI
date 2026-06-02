from fastapi import APIRouter, Query
from typing import Optional
from backend.app.models.query import IncidentListResponse
from backend.app.rag.vectorstore import get_chroma_store

router = APIRouter(prefix="/api", tags=["Incidents"])


@router.get("/incidents", response_model=IncidentListResponse)
async def list_incidents(
    region: Optional[str] = Query(None, description="Filter by network_region"),
    severity: Optional[str] = Query(None, description="CRITICAL / HIGH / MEDIUM / LOW"),
    vendor: Optional[str] = Query(None, description="Filter by device_vendor"),
    technology: Optional[str] = Query(None, description="Filter by technology_type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    store = get_chroma_store()
    all_docs = store.get_all_documents(limit=5000)

    filtered = all_docs
    if region:
        filtered = [d for d in filtered if d.get("network_region", "").lower() == region.lower()]
    if severity:
        filtered = [d for d in filtered if d.get("severity", "").upper() == severity.upper()]
    if vendor:
        filtered = [d for d in filtered if d.get("device_vendor", "").lower() == vendor.lower()]
    if technology:
        filtered = [d for d in filtered if d.get("technology_type", "").lower() == technology.lower()]

    filtered.sort(key=lambda d: d.get("timestamp", ""), reverse=True)

    total = len(filtered)
    start = (page - 1) * page_size
    page_data = filtered[start : start + page_size]

    return IncidentListResponse(incidents=page_data, total=total, page=page, page_size=page_size)

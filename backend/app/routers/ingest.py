from fastapi import APIRouter, HTTPException, BackgroundTasks
from backend.app.models.query import IngestResponse
from backend.app.rag.ingestion import IngestionPipeline
from backend.app.config import get_settings
from loguru import logger

router = APIRouter(prefix="/api", tags=["Ingestion"])

# Live progress state — written by the background task, read by GET /api/ingest/status
_status: dict = {
    "running":       False,
    "step":          "",       # human-readable current step name
    "step_index":    0,        # 0-based current step
    "total_steps":   5,        # Loading → Preparing → Embedding → ChromaDB → BM25 → Done
    "docs_done":     0,        # documents processed so far
    "docs_total":    0,        # total documents in this run
    "percent":       0,        # 0-100 overall progress
    "last_count":    0,
    "last_error":    None,
}


def _calc_percent(step_index: int, total_steps: int, docs_done: int, docs_total: int) -> int:
    """
    Blend step-level and within-step (document) progress into a single 0-100 value.
    Embedding (step 2) is the longest step so it gets the widest band (30-70%).
    """
    bands = [(0, 5), (5, 10), (10, 70), (70, 85), (85, 95), (95, 100)]
    if step_index >= len(bands):
        return 100
    lo, hi = bands[step_index]
    if step_index == 2 and docs_total > 0:          # embedding — fine-grained within-step
        frac = docs_done / docs_total
        return int(lo + frac * (hi - lo))
    return lo


@router.post("/ingest", response_model=IngestResponse)
async def ingest_data(background_tasks: BackgroundTasks):
    if _status["running"]:
        raise HTTPException(status_code=409, detail="Ingestion already in progress.")
    # Reset state
    _status.update(running=True, step="Starting", step_index=0,
                   docs_done=0, docs_total=0, percent=0, last_error=None)
    background_tasks.add_task(_run_ingestion)
    return IngestResponse(
        status="started",
        documents_indexed=0,
        message="Ingestion started. Poll GET /api/ingest/status for live progress.",
    )


@router.get("/ingest/status")
async def ingest_status():
    """Live ingestion progress — poll this while running=true."""
    return {
        "running":     _status["running"],
        "step":        _status["step"],
        "step_index":  _status["step_index"],
        "total_steps": _status["total_steps"],
        "docs_done":   _status["docs_done"],
        "docs_total":  _status["docs_total"],
        "percent":     _status["percent"],
        "last_count":  _status["last_count"],
        "last_error":  _status["last_error"],
    }


def _run_ingestion():
    # Plain def (not async) so FastAPI runs this in a thread-pool worker.
    # If it were async def, synchronous OpenAI calls inside embed_texts would
    # block the event loop and prevent the status endpoint from responding.
    def _on_progress(step: str, step_idx: int, total_steps: int,
                     docs_done: int, docs_total: int):
        _status["step"]        = step
        _status["step_index"]  = step_idx
        _status["total_steps"] = total_steps
        _status["docs_done"]   = docs_done
        _status["docs_total"]  = docs_total
        _status["percent"]     = _calc_percent(step_idx, total_steps, docs_done, docs_total)

    try:
        settings = get_settings()
        pipeline = IngestionPipeline(settings)
        count = pipeline.ingest_csv(settings.DATA_PATH, on_progress=_on_progress)
        _status["last_count"] = count
        _status["step"]       = "Complete"
        _status["percent"]    = 100
        logger.info(f"Background ingestion complete: {count} docs.")
    except Exception as e:
        _status["last_error"] = str(e)
        _status["step"]       = "Failed"
        logger.error(f"Background ingestion failed: {e}")
    finally:
        _status["running"] = False

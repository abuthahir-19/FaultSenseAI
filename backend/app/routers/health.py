from fastapi import APIRouter
from backend.app.rag.vectorstore import get_chroma_store
from backend.app.rag.bm25_index import get_bm25_index

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    try:
        store = get_chroma_store()
        bm25 = get_bm25_index()
        return {
            "status": "healthy",
            "service": "TelecomNetworkFaultIntel API",
            "chromadb": "connected",
            "documents_indexed": store.doc_count,
            "bm25_ready": bm25.is_ready,
            "bm25_docs": bm25.doc_count,
        }
    except Exception as e:
        return {"status": "degraded", "error": str(e)}

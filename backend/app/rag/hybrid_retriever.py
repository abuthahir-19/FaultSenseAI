from typing import List, Dict, Any, Optional
from loguru import logger
from backend.app.rag.embeddings import get_embedding_manager
from backend.app.rag.vectorstore import get_chroma_store
from backend.app.rag.bm25_index import get_bm25_index
from backend.app.config import get_settings


def _rrf_score(rank: int, k: int = 60) -> float:
    return 1.0 / (k + rank)


class HybridRetriever:
    def __init__(self):
        self._embedder = get_embedding_manager()
        self._chroma = get_chroma_store()
        self._bm25 = get_bm25_index()
        self._settings = get_settings()

    def search(
        self,
        query: str,
        k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        if not query.strip():
            return []

        # Vector search
        query_embedding = self._embedder.embed_query(query)
        vector_results = self._chroma.similarity_search(
            query_embedding, k=k * 2, filters=filters
        )
        logger.debug(f"Vector search: {len(vector_results)} results")

        # BM25 search
        bm25_results = self._bm25.search(query, k=k * 2)
        bm25_id_to_score = {doc_id: score for doc_id, score in bm25_results}
        logger.debug(f"BM25 search: {len(bm25_results)} results")

        # RRF fusion
        rrf_scores: Dict[str, float] = {}
        id_to_doc: Dict[str, Dict] = {}

        for rank, doc in enumerate(vector_results):
            doc_id = doc["id"]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + _rrf_score(rank, self._settings.RRF_K)
            id_to_doc[doc_id] = doc

        for rank, (doc_id, _) in enumerate(bm25_results):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + _rrf_score(rank, self._settings.RRF_K)
            if doc_id not in id_to_doc:
                # Fetch metadata from chroma
                try:
                    res = self._chroma.collection.get(
                        ids=[doc_id], include=["documents", "metadatas"]
                    )
                    if res["ids"]:
                        meta = res["metadatas"][0] if res["metadatas"] else {}
                        id_to_doc[doc_id] = {
                            **meta,
                            "document": res["documents"][0],
                            "id": doc_id,
                            "chroma_score": 0.0,
                        }
                except Exception as e:
                    logger.debug(f"Could not fetch BM25 doc {doc_id}: {e}")

        sorted_ids = sorted(rrf_scores, key=rrf_scores.__getitem__, reverse=True)[:k]
        fused = []
        for doc_id in sorted_ids:
            if doc_id in id_to_doc:
                doc = id_to_doc[doc_id].copy()
                doc["rrf_score"] = round(rrf_scores[doc_id], 6)
                doc["bm25_score"] = round(bm25_id_to_score.get(doc_id, 0.0), 4)
                fused.append(doc)

        logger.info(f"Hybrid search: {len(fused)} fused results for '{query[:60]}'")
        return fused


_retriever: Optional[HybridRetriever] = None


def get_hybrid_retriever() -> HybridRetriever:
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    return _retriever

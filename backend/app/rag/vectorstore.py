import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
from loguru import logger
from backend.app.config import get_settings


class ChromaDBStore:
    def __init__(self):
        settings = get_settings()
        self._client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            f"ChromaDB ready. Collection '{settings.CHROMA_COLLECTION}' "
            f"has {self._collection.count()} docs."
        )

    @property
    def doc_count(self) -> int:
        return self._collection.count()

    def add_documents(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            self._collection.upsert(
                ids=ids[i : i + batch_size],
                embeddings=embeddings[i : i + batch_size],
                documents=documents[i : i + batch_size],
                metadatas=metadatas[i : i + batch_size],
            )
        logger.info(f"Upserted {len(ids)} documents into ChromaDB.")

    def similarity_search(
        self,
        query_embedding: List[float],
        k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        where = _build_where_clause(filters) if filters else None
        n_results = min(k, max(1, self._collection.count()))
        query_kwargs: Dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            query_kwargs["where"] = where

        results = self._collection.query(**query_kwargs)

        docs = []
        for i, doc_id in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            distance = results["distances"][0][i] if results["distances"] else 1.0
            score = max(0.0, 1.0 - float(distance))
            docs.append(
                {**meta, "document": results["documents"][0][i], "chroma_score": score, "id": doc_id}
            )
        return docs

    def get_all_documents(self, limit: int = 2000) -> List[Dict[str, Any]]:
        results = self._collection.get(limit=limit, include=["documents", "metadatas"])
        docs = []
        for i, doc_id in enumerate(results["ids"]):
            meta = results["metadatas"][i] if results["metadatas"] else {}
            docs.append({**meta, "document": results["documents"][i], "id": doc_id})
        return docs

    @property
    def collection(self):
        return self._collection


def _build_where_clause(filters: Dict[str, Any]) -> Optional[Dict]:
    field_map = {
        "region": "network_region",
        "network_region": "network_region",
        "severity": "severity",
        "vendor": "device_vendor",
        "device_vendor": "device_vendor",
        "technology": "technology_type",
        "technology_type": "technology_type",
    }
    conditions = []
    for key, value in filters.items():
        if key in ("from_date", "to_date"):
            # Timestamp range: stored as string "YYYY-MM-DDTHH:MM:SS"
            # ChromaDB supports $gte/$lte on string fields (lexicographic — works for ISO dates)
            if value and str(value).strip():
                op = "$gte" if key == "from_date" else "$lte"
                conditions.append({"timestamp": {op: str(value)}})
            continue
        chroma_key = field_map.get(key, key)
        if value and str(value).strip():
            conditions.append({chroma_key: {"$eq": str(value)}})
    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


_store: Optional[ChromaDBStore] = None


def get_chroma_store() -> ChromaDBStore:
    global _store
    if _store is None:
        _store = ChromaDBStore()
    return _store

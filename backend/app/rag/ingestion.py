import pandas as pd
from pathlib import Path
from typing import List
from loguru import logger
from backend.app.config import Settings
from backend.app.rag.embeddings import get_embedding_manager
from backend.app.rag.vectorstore import get_chroma_store
from backend.app.rag.bm25_index import get_bm25_index


REQUIRED_COLS = {
    "alarm_id", "incident_description", "network_region",
    "technology_type", "severity", "outage_duration",
    "device_vendor", "resolution_notes", "timestamp", "service_impact",
}


class IngestionPipeline:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._embedder = get_embedding_manager()
        self._store = get_chroma_store()
        self._bm25 = get_bm25_index()

    def ingest_csv(self, path: str, on_progress=None) -> int:
        """
        Ingest CSV into ChromaDB + BM25.
        on_progress(step, step_index, total_steps, docs_done, docs_total) is called
        at each stage so callers can report live progress.
        """
        def _progress(step: str, step_idx: int, docs_done: int = 0, docs_total: int = 0):
            if on_progress:
                on_progress(step, step_idx, 5, docs_done, docs_total)

        csv_path = Path(path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV not found: {path}")

        _progress("Loading CSV", 0)
        logger.info(f"Loading CSV: {path}")
        df = pd.read_csv(csv_path)

        missing = REQUIRED_COLS - set(df.columns)
        if missing:
            raise ValueError(f"CSV missing columns: {missing}")

        df = df.fillna("")
        records = df.to_dict(orient="records")
        total = len(records)

        _progress("Preparing documents", 1, 0, total)
        documents: List[str] = []
        ids: List[str] = []
        metadatas = []

        for row in records:
            doc_text = f"{row['incident_description']} {row['resolution_notes']}"
            documents.append(doc_text)
            ids.append(str(row["alarm_id"]))
            metadatas.append({
                "alarm_id":             str(row["alarm_id"]),
                "network_region":       str(row["network_region"]),
                "technology_type":      str(row["technology_type"]),
                "severity":             str(row["severity"]),
                "outage_duration":      str(row["outage_duration"]),
                "device_vendor":        str(row["device_vendor"]),
                "timestamp":            str(row["timestamp"]),
                "service_impact":       str(row["service_impact"]),
                "incident_description": str(row["incident_description"])[:500],
                "resolution_notes":     str(row["resolution_notes"])[:500],
            })

        logger.info(f"Embedding {total} documents (concurrent, batch_size=512, workers=3)...")
        _progress("Generating embeddings", 2, 0, total)

        def _batch_cb(done: int, _total: int):
            _progress("Generating embeddings", 2, done, _total)

        def _store_cb(batch_idx: int, batch_embeddings: list, start: int, end: int):
            self._store.add_documents_batch(
                ids=ids[start:end],
                embeddings=batch_embeddings,
                documents=documents[start:end],
                metadatas=metadatas[start:end],
            )

        embeddings = self._embedder.embed_texts_concurrent(
            documents, on_batch=_batch_cb, on_store=_store_cb,
            batch_size=512, max_workers=3,
        )

        # ChromaDB upserts completed progressively during embedding; just advance the step indicator
        _progress("Storing in ChromaDB", 3, total, total)
        logger.info("ChromaDB upserts completed progressively during embedding.")

        _progress("Building BM25 index", 4, total, total)
        logger.info("Building BM25 index...")
        self._bm25.build(documents=documents, doc_ids=ids)

        _progress("Complete", 5, total, total)
        logger.success(f"Ingestion complete: {total} documents indexed.")
        return total

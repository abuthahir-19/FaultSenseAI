from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from typing import List, Callable, Optional
from loguru import logger
from backend.app.config import get_settings, get_openai_client


class EmbeddingManager:
    def __init__(self):
        settings = get_settings()
        self._client = get_openai_client()
        self._model = settings.OPENAI_EMBEDDING_MODEL
        logger.info(f"EmbeddingManager initialized with model: {self._model}")

    def embed_texts(self, texts: List[str], on_batch=None) -> List[List[float]]:
        """Embed texts in batches of 100. on_batch(done, total) called after each batch."""
        if not texts:
            return []
        all_embeddings = []
        batch_size = 100
        total = len(texts)
        for i in range(0, total, batch_size):
            batch = texts[i: i + batch_size]
            response = self._client.embeddings.create(model=self._model, input=batch)
            all_embeddings.extend(item.embedding for item in response.data)
            done = min(i + batch_size, total)
            logger.debug(f"Embedded batch {i // batch_size + 1}: {len(batch)} texts")
            if on_batch:
                on_batch(done, total)
        return all_embeddings

    def embed_texts_concurrent(
        self,
        texts: List[str],
        on_batch: Optional[Callable[[int, int], None]] = None,
        on_store: Optional[Callable[[int, List[List[float]], int, int], None]] = None,
        batch_size: int = 512,
        max_workers: int = 3,
    ) -> List[List[float]]:
        """Embed texts using concurrent API calls for faster ingestion.
        on_batch(done, total) — thread-safe progress callback after each batch.
        on_store(batch_idx, embeddings, start, end) — called under a lock for progressive ChromaDB writes.
        """
        if not texts:
            return []

        total = len(texts)
        slices = [
            (idx, i, min(i + batch_size, total))
            for idx, i in enumerate(range(0, total, batch_size))
        ]

        results: dict = {}
        counter_lock = threading.Lock()
        store_lock   = threading.Lock()
        docs_done = 0

        def _embed_batch(batch_idx, start, end):
            batch = texts[start:end]
            resp = self._client.embeddings.create(model=self._model, input=batch)
            return batch_idx, start, end, [item.embedding for item in resp.data]

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {
                pool.submit(_embed_batch, idx, s, e): (idx, s, e)
                for idx, s, e in slices
            }
            try:
                for future in as_completed(futures):
                    batch_idx, start, end, embeddings = future.result()
                    results[batch_idx] = embeddings

                    with counter_lock:
                        docs_done += (end - start)
                        snapshot = docs_done
                    logger.debug(
                        f"Batch {batch_idx + 1}/{len(slices)} embedded ({snapshot}/{total})"
                    )
                    if on_batch:
                        on_batch(snapshot, total)

                    if on_store:
                        with store_lock:
                            on_store(batch_idx, embeddings, start, end)
            except Exception:
                for f in futures:
                    f.cancel()
                raise

        ordered: List[List[float]] = []
        for idx, s, e in slices:
            ordered.extend(results[idx])
        return ordered

    def embed_query(self, query: str) -> List[float]:
        result = self.embed_texts([query])
        return result[0] if result else []


_embedding_manager: EmbeddingManager | None = None


def get_embedding_manager() -> EmbeddingManager:
    global _embedding_manager
    if _embedding_manager is None:
        _embedding_manager = EmbeddingManager()
    return _embedding_manager

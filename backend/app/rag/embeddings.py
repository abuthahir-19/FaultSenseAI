from typing import List
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

    def embed_query(self, query: str) -> List[float]:
        result = self.embed_texts([query])
        return result[0] if result else []


_embedding_manager: EmbeddingManager | None = None


def get_embedding_manager() -> EmbeddingManager:
    global _embedding_manager
    if _embedding_manager is None:
        _embedding_manager = EmbeddingManager()
    return _embedding_manager

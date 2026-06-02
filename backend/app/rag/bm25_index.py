from rank_bm25 import BM25Okapi
from typing import List, Tuple, Optional
from loguru import logger
import re


def _tokenize(text: str) -> List[str]:
    return re.sub(r"[^a-z0-9\s]", " ", text.lower()).split()


class BM25Index:
    def __init__(self):
        self._index: Optional[BM25Okapi] = None
        self._doc_ids: List[str] = []

    def build(self, documents: List[str], doc_ids: List[str]) -> None:
        self._doc_ids = doc_ids
        tokenized = [_tokenize(doc) for doc in documents]
        self._index = BM25Okapi(tokenized)
        logger.info(f"BM25 index built with {len(documents)} documents.")

    def search(self, query: str, k: int = 10) -> List[Tuple[str, float]]:
        if self._index is None:
            logger.warning("BM25 index not built yet. Run ingestion first.")
            return []
        tokens = _tokenize(query)
        scores = self._index.get_scores(tokens)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:k]
        return [(self._doc_ids[i], float(score)) for i, score in ranked if score > 0]

    @property
    def is_ready(self) -> bool:
        return self._index is not None

    @property
    def doc_count(self) -> int:
        return len(self._doc_ids)


_bm25_index: Optional[BM25Index] = None


def get_bm25_index() -> BM25Index:
    global _bm25_index
    if _bm25_index is None:
        _bm25_index = BM25Index()
    return _bm25_index

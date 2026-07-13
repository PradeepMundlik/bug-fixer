import re
from typing import Callable, List

from rank_bm25 import BM25Okapi

# project_id -> (BM25Okapi, corpus_docs)
_cache: dict = {}


def _tokenize(text: str) -> List[str]:
    # Split camelCase/PascalCase so "placeOrder" -> ["place", "order"]
    # and also handles normal words and numbers
    return re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)|\d+", text.lower())


def _build(project_id: str, scroll_fn: Callable) -> tuple:
    docs = scroll_fn(project_id)  # list of {point_id, content, ...payload}
    corpus = [_tokenize(d.get("content", "")) for d in docs]
    return BM25Okapi(corpus), docs


def invalidate(project_id: str) -> None:
    """Drop cached BM25 index for a project (call after new files are indexed)."""
    _cache.pop(project_id, None)


def search_bm25(
    query: str,
    project_id: str,
    top_k: int,
    scroll_fn: Callable,
) -> List[dict]:
    if project_id not in _cache:
        _cache[project_id] = _build(project_id, scroll_fn)

    bm25, docs = _cache[project_id]
    if not docs:
        return []

    scores = bm25.get_scores(_tokenize(query))
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)

    return [
        {"point_id": docs[i]["point_id"], "bm25_score": score, **docs[i]}
        for i, score in ranked[:top_k]
        if score > 0
    ]

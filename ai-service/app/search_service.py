from typing import List, Optional

from app.bm25_index import search_bm25
from app.embedding import embed_batch
from app.qdrant_store import scroll_all_chunks, search_chunks


def _rrf_fuse(vector_hits: list, bm25_hits: list, k: int = 60) -> list:
    """Reciprocal Rank Fusion: merge two ranked lists by summing 1/(rank+1+k)."""
    merged: dict = {}
    for rank, hit in enumerate(vector_hits):
        pid = hit["point_id"]
        merged.setdefault(pid, {**hit, "rrf_score": 0.0})
        merged[pid]["rrf_score"] += 1.0 / (rank + 1 + k)
    for rank, hit in enumerate(bm25_hits):
        pid = hit["point_id"]
        merged.setdefault(pid, {**hit, "rrf_score": 0.0})
        merged[pid]["rrf_score"] += 1.0 / (rank + 1 + k)
    return sorted(merged.values(), key=lambda x: x["rrf_score"], reverse=True)


def hybrid_search(
    project_id: str,
    query: str,
    top_k: int = 5,
    class_name: Optional[str] = None,
    language: Optional[str] = None,
    file_path_prefix: Optional[str] = None,
) -> List[dict]:
    """
    Hybrid search over indexed chunks: vector (embedding) search fused with BM25
    via RRF, then an optional file-path prefix post-filter. Returns fused hit
    dicts (each carrying an ``rrf_score``), already sliced to ``top_k``.
    """
    fetch_k = top_k * 3  # over-fetch so filtering doesn't starve the final list

    vectors = embed_batch([query])
    vector_hits = search_chunks(
        vectors[0], project_id, fetch_k,
        class_name=class_name, language=language,
    )
    # BM25 disabled for now — it wasn't helping with the current chunking strategy.
    # bm25_hits = search_bm25(query, project_id, fetch_k, scroll_fn=scroll_all_chunks)
    bm25_hits: List[dict] = []
    fused = _rrf_fuse(vector_hits, bm25_hits)

    if file_path_prefix:
        fused = [h for h in fused if h.get("file_path", "").startswith(file_path_prefix)]

    return fused[:top_k]

import os
import uuid
from typing import List, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams

from app.chunking import RawChunk
from app.embedding import VECTOR_DIM

COLLECTION_NAME = "code_chunks"
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

_client: Optional[QdrantClient] = None


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    return _client


def ensure_collection() -> None:
    client = get_client()
    existing = {c.name for c in client.get_collections().collections}
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
        )


def upsert_chunks(
    chunks: List[RawChunk],
    vectors: List[List[float]],
    project_id: str,
    file_id: str,
    file_path: str,
    language: str,
) -> List[str]:
    """Upsert chunks with their vectors. Returns list of qdrant_point_ids."""
    client = get_client()
    points: List[PointStruct] = []
    point_ids: List[str] = []

    for chunk, vector in zip(chunks, vectors):
        point_id = str(uuid.uuid4())
        point_ids.append(point_id)
        points.append(PointStruct(
            id=point_id,
            vector=vector,
            payload={
                "project_id": project_id,
                "file_id": file_id,
                "file_path": file_path,
                "language": language,
                "chunk_type": chunk.chunk_type,
                "class_name": chunk.class_name,
                "method_name": chunk.method_name,
                "annotations": chunk.annotations,
                "callees": chunk.callees,
                "signature": chunk.signature,
                "imports": chunk.imports,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "content": chunk.content,
            },
        ))

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    return point_ids


def search_chunks(
    query_vector: List[float],
    project_id: str,
    top_k: int = 5,
    class_name: Optional[str] = None,
    language: Optional[str] = None,
) -> List[dict]:
    must = [FieldCondition(key="project_id", match=MatchValue(value=project_id))]
    if class_name:
        must.append(FieldCondition(key="class_name", match=MatchValue(value=class_name)))
    if language:
        must.append(FieldCondition(key="language", match=MatchValue(value=language)))

    hits = get_client().search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        query_filter=Filter(must=must),
        limit=top_k,
        with_payload=True,
    )
    return [{"point_id": str(hit.id), "score": hit.score, **hit.payload} for hit in hits]


def find_method_chunk(
    project_id: str,
    class_name: Optional[str],
    method_name: str,
) -> Optional[dict]:
    """Fetch a single method chunk by class + method name (used by the metadata tools)."""
    must = [
        FieldCondition(key="project_id", match=MatchValue(value=project_id)),
        FieldCondition(key="method_name", match=MatchValue(value=method_name)),
    ]
    if class_name:
        must.append(FieldCondition(key="class_name", match=MatchValue(value=class_name)))

    batch, _ = get_client().scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=Filter(must=must),
        limit=1,
        with_payload=True,
    )
    if not batch:
        return None
    point = batch[0]
    return {"point_id": str(point.id), **point.payload}


def scroll_all_chunks(project_id: str) -> List[dict]:
    """Fetch every chunk for a project (used to build the BM25 index)."""
    must = [FieldCondition(key="project_id", match=MatchValue(value=project_id))]
    all_points: List[dict] = []
    offset = None

    while True:
        batch, offset = get_client().scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=Filter(must=must),
            limit=250,
            offset=offset,
            with_payload=True,
        )
        all_points.extend({"point_id": str(p.id), **p.payload} for p in batch)
        if offset is None:
            break

    return all_points

import os
import uuid
from typing import List, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

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
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "content": chunk.content,
            },
        ))

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    return point_ids

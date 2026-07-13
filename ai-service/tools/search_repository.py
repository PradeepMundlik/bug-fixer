from typing import List, Optional

from app.search_service import hybrid_search


def search_repository(
    project_id: str,
    query: str,
    top_k: int = 5,
    class_name: Optional[str] = None,
    language: Optional[str] = None,
    file_path_prefix: Optional[str] = None,
) -> List[dict]:
    """Hybrid search over all indexed chunks. Returns top matches with file/class/method."""
    hits = hybrid_search(
        project_id=project_id,
        query=query,
        top_k=top_k,
        class_name=class_name,
        language=language,
        file_path_prefix=file_path_prefix,
    )
    return [
        {
            "file_path": h.get("file_path", ""),
            "class_name": h.get("class_name"),
            "method_name": h.get("method_name"),
            "chunk_type": h.get("chunk_type", ""),
            "start_line": h.get("start_line", 0),
            "end_line": h.get("end_line", 0),
            "score": round(h.get("rrf_score", 0.0), 6),
            "content": h.get("content", ""),
        }
        for h in hits
    ]


SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_repository",
        "description": (
            "Hybrid semantic + keyword search over the indexed codebase. Use this to "
            "find code relevant to a bug report, symptom, or concept when you don't "
            "know the exact class or method name. Returns the top matching chunks with "
            "their file path, class, method, line range, and content."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project's UUID (from the upload API).",
                },
                "query": {
                    "type": "string",
                    "description": "Natural-language or code query describing what to find.",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Maximum number of results to return.",
                    "default": 5,
                },
                "class_name": {
                    "type": "string",
                    "description": "Optional: restrict results to chunks from this class.",
                },
                "language": {
                    "type": "string",
                    "description": "Optional: restrict results to this language (e.g. 'java').",
                },
                "file_path_prefix": {
                    "type": "string",
                    "description": "Optional: restrict results to files whose path starts with this prefix.",
                },
            },
            "required": ["project_id", "query"],
        },
    },
}

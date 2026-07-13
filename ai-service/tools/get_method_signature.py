from typing import Optional

from app.qdrant_store import find_method_chunk


def get_method_signature(
    project_id: str,
    class_name: str,
    method: str,
) -> Optional[dict]:
    """Return the full signature, annotations, and file imports for a specific method."""
    chunk = find_method_chunk(project_id, class_name, method)
    if chunk is None:
        return None
    return {
        "class_name": chunk.get("class_name"),
        "method_name": chunk.get("method_name"),
        "signature": chunk.get("signature", ""),
        "annotations": chunk.get("annotations", []) or [],
        "imports": chunk.get("imports", []) or [],
        "file_path": chunk.get("file_path", ""),
        "start_line": chunk.get("start_line", 0),
        "end_line": chunk.get("end_line", 0),
    }


SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_method_signature",
        "description": (
            "Return the full signature (modifiers, return type, parameters), annotations, "
            "and the declaring file's imports for a specific method. Use this to understand "
            "a method's contract without reading its whole body. Returns null if not found."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project's UUID (from the upload API).",
                },
                "class_name": {
                    "type": "string",
                    "description": "The class that declares the method.",
                },
                "method": {
                    "type": "string",
                    "description": "The method name.",
                },
            },
            "required": ["project_id", "class_name", "method"],
        },
    },
}

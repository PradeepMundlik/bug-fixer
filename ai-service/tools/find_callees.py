from typing import Optional

from app.qdrant_store import find_method_chunk


def find_callees(
    project_id: str,
    method: str,
    class_name: Optional[str] = None,
) -> Optional[dict]:
    """Return the callees (outgoing calls) recorded for a given method chunk."""
    chunk = find_method_chunk(project_id, class_name, method)
    if chunk is None:
        return None
    return {
        "class_name": chunk.get("class_name"),
        "method_name": chunk.get("method_name"),
        "file_path": chunk.get("file_path", ""),
        "callees": chunk.get("callees", []) or [],
    }


SCHEMA = {
    "type": "function",
    "function": {
        "name": "find_callees",
        "description": (
            "Return the list of methods that the given method calls — i.e. its "
            "callees/downstream in the call graph. Use this to see what a method "
            "depends on. Returns null if the method is not found."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project's UUID (from the upload API).",
                },
                "method": {
                    "type": "string",
                    "description": "The method whose callees you want.",
                },
                "class_name": {
                    "type": "string",
                    "description": "Optional: the class declaring the method (disambiguates overloads across classes).",
                },
            },
            "required": ["project_id", "method"],
        },
    },
}

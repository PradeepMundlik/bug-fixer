from typing import List, Optional

from app.qdrant_store import scroll_all_chunks


def _matches(callee: str, method: str, class_name: Optional[str], caller_class: Optional[str]) -> bool:
    """Does this callee string reference `method` (optionally on `class_name`)?"""
    receiver, _, bare = callee.rpartition(".")  # "orderRepo.save" -> ("orderRepo", ".", "save")
    if bare != method:
        return False
    if not class_name:
        return True
    if receiver:
        # Qualified call: receiver is a variable name — match it loosely against the class.
        return class_name.lower() in receiver.lower()
    # Bare call (no receiver) is a same-class call: target lives in the caller's own class.
    return caller_class == class_name


def find_callers(
    project_id: str,
    method: str,
    class_name: Optional[str] = None,
) -> List[dict]:
    """Find methods that call `method` (i.e. have it in their callees list)."""
    callers: List[dict] = []
    for chunk in scroll_all_chunks(project_id):
        if chunk.get("chunk_type") != "method":
            continue
        caller_class = chunk.get("class_name")
        for callee in chunk.get("callees", []) or []:
            if _matches(callee, method, class_name, caller_class):
                callers.append({
                    "class_name": caller_class,
                    "method_name": chunk.get("method_name"),
                    "file_path": chunk.get("file_path", ""),
                    "start_line": chunk.get("start_line", 0),
                    "end_line": chunk.get("end_line", 0),
                    "matched_callee": callee,
                })
                break  # one hit per caller method is enough
    return callers


SCHEMA = {
    "type": "function",
    "function": {
        "name": "find_callers",
        "description": (
            "Find every method that calls the given method — i.e. the callers/upstream "
            "of a method in the call graph. Use this to trace how execution reaches a "
            "suspect method. Returns each caller's class, method, file, and line range."
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
                    "description": "The name of the called (target) method.",
                },
                "class_name": {
                    "type": "string",
                    "description": (
                        "Optional: the class that declares the target method. Narrows "
                        "matches; the receiver in call sites is a variable name, so this "
                        "is a soft hint rather than an exact filter."
                    ),
                },
            },
            "required": ["project_id", "method"],
        },
    },
}

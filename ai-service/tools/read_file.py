from tools._fs import resolve_within_project


def read_file(project_id: str, path: str) -> dict:
    """Read a source file (relative to the project root) and return its raw content."""
    target = resolve_within_project(project_id, path)
    if not target.is_file():
        raise FileNotFoundError(f"not a file: {path}")
    content = target.read_text(encoding="utf-8", errors="replace")
    return {
        "path": path,
        "content": content,
        "line_count": len(content.splitlines()),
    }


SCHEMA = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": (
            "Read the full raw content of a source file, given its path relative to the "
            "project root (the same file paths returned by search_repository). Use this "
            "when you need complete context beyond the indexed chunks."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project's UUID (from the upload API).",
                },
                "path": {
                    "type": "string",
                    "description": "File path relative to the project root, e.g. 'src/main/java/com/example/OrderService.java'.",
                },
            },
            "required": ["project_id", "path"],
        },
    },
}

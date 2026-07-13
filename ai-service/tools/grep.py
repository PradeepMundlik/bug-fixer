import re
from pathlib import Path
from typing import List, Optional

from tools._fs import project_root, resolve_within_project

_MAX_FILE_BYTES = 2_000_000  # skip files larger than ~2 MB


def _iter_files(target: Path):
    if target.is_file():
        yield target
    elif target.is_dir():
        for p in sorted(target.rglob("*")):
            if p.is_file():
                yield p


def grep(
    project_id: str,
    pattern: str,
    path: Optional[str] = None,
    max_results: int = 200,
) -> List[dict]:
    """Regex-search file(s) under the project root for exact strings the embedder may miss."""
    regex = re.compile(pattern)
    root = project_root(project_id)
    target = resolve_within_project(project_id, path) if path else root

    matches: List[dict] = []
    for file in _iter_files(target):
        try:
            if file.stat().st_size > _MAX_FILE_BYTES:
                continue
            text = file.read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeDecodeError):
            continue  # unreadable or binary — skip
        rel = str(file.relative_to(root))
        for lineno, line in enumerate(text.splitlines(), start=1):
            if regex.search(line):
                matches.append({"file_path": rel, "line_number": lineno, "line": line})
                if len(matches) >= max_results:
                    return matches
    return matches


SCHEMA = {
    "type": "function",
    "function": {
        "name": "grep",
        "description": (
            "Regex-search across the project's files (or a single file/subdirectory) for "
            "an exact pattern. Use this to find literal strings, identifiers, or error "
            "messages that semantic search may miss. Returns file/line/text for each match."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project's UUID (from the upload API).",
                },
                "pattern": {
                    "type": "string",
                    "description": "A Python regular expression to search for.",
                },
                "path": {
                    "type": "string",
                    "description": "Optional: a file or directory (relative to project root) to limit the search. Defaults to the whole project.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of matching lines to return.",
                    "default": 200,
                },
            },
            "required": ["project_id", "pattern"],
        },
    },
}

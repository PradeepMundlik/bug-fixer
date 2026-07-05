from typing import List, Optional, Tuple

from app.models import MethodInfo, ParseResponse


class RawChunk:
    """Intermediate chunk before embedding — holds content + metadata."""

    def __init__(
        self,
        chunk_type: str,
        content: str,
        class_name: Optional[str],
        method_name: Optional[str],
        annotations: List[str],
        callees: List[str],
        start_line: int,
        end_line: int,
    ):
        self.chunk_type = chunk_type
        self.content = content
        self.class_name = class_name
        self.method_name = method_name
        self.annotations = annotations
        self.callees = callees
        self.start_line = start_line
        self.end_line = end_line


def produce_chunks(
    parse_result: ParseResponse,
    file_content: str,
    file_path: str,
) -> List[RawChunk]:
    lines = file_content.splitlines()
    chunks: List[RawChunk] = []

    # One chunk per method — signature + body from source lines
    for method in parse_result.methods:
        body = _slice_lines(lines, method.start_line, method.end_line)
        content = _method_content(parse_result, method, file_path, body)
        chunks.append(RawChunk(
            chunk_type="method",
            content=content,
            class_name=parse_result.class_name,
            method_name=method.name,
            annotations=method.annotations,
            callees=method.callees,
            start_line=method.start_line,
            end_line=method.end_line,
        ))

    # One class-level chunk — imports + class declaration (everything outside method bodies)
    if parse_result.class_name:
        class_content = _class_content(parse_result, file_path)
        chunks.append(RawChunk(
            chunk_type="class",
            content=class_content,
            class_name=parse_result.class_name,
            method_name=None,
            annotations=[],
            callees=[],
            start_line=1,
            end_line=len(lines),
        ))

    return chunks


def _slice_lines(lines: List[str], start: int, end: int) -> str:
    # start/end are 1-indexed from tree-sitter
    return "\n".join(lines[start - 1 : end])


def _method_content(
    parse_result: ParseResponse,
    method: MethodInfo,
    file_path: str,
    body: str,
) -> str:
    """
    Embed-friendly content: metadata header + raw source.
    The header gives the model class/file context it needs to answer
    'what does X.Y do?' queries accurately.
    """
    parts = [
        f"[CLASS: {parse_result.class_name}] [METHOD: {method.name}] [FILE: {file_path}]",
    ]
    if method.annotations:
        parts.append(f"ANNOTATIONS: {', '.join(method.annotations)}")
    if parse_result.imports:
        parts.append(f"IMPORTS: {', '.join(parse_result.imports)}")
    if method.callees:
        parts.append(f"CALLEES: {', '.join(method.callees)}")
    parts.append("")
    parts.append(body)
    return "\n".join(parts)


def _class_content(parse_result: ParseResponse, file_path: str) -> str:
    parts = [
        f"[CLASS: {parse_result.class_name}] [FILE: {file_path}]",
        f"METHODS: {', '.join(m.name for m in parse_result.methods)}",
    ]
    if parse_result.imports:
        parts.append(f"IMPORTS: {', '.join(parse_result.imports)}")
    return "\n".join(parts)

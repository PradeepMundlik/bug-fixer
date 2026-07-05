from typing import List, Optional

from pydantic import BaseModel


# ── /parse ────────────────────────────────────────────────────────────────────

class ParseRequest(BaseModel):
    file_content: str
    file_path: str = ""


class Parameter(BaseModel):
    name: str
    type: str


class MethodInfo(BaseModel):
    name: str
    signature: str
    return_type: str
    parameters: List[Parameter]
    annotations: List[str]
    callees: List[str]
    start_line: int
    end_line: int


class CallEdge(BaseModel):
    caller: str
    callees: List[str]


class ParseResponse(BaseModel):
    file_path: str
    class_name: Optional[str]
    imports: List[str]
    methods: List[MethodInfo]
    call_graph: List[CallEdge]


# ── /index ────────────────────────────────────────────────────────────────────

class IndexRequest(BaseModel):
    file_content: str
    file_path: str
    project_id: str
    file_id: str
    language: str = "java"


class ChunkResult(BaseModel):
    chunk_type: str          # "method" | "class"
    method_name: Optional[str]
    class_name: Optional[str]
    content: str
    start_line: int
    end_line: int
    annotations: List[str]
    callees: List[str]
    qdrant_point_id: str


class IndexResponse(BaseModel):
    file_path: str
    project_id: str
    file_id: str
    chunks: List[ChunkResult]

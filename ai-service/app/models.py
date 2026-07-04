from typing import List, Optional

from pydantic import BaseModel


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


class CallEdge(BaseModel):
    caller: str
    callees: List[str]


class ParseResponse(BaseModel):
    file_path: str
    class_name: Optional[str]
    imports: List[str]
    methods: List[MethodInfo]
    call_graph: List[CallEdge]

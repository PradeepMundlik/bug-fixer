import tree_sitter_java as tsjava
from tree_sitter import Language, Parser

from app.models import CallEdge, MethodInfo, Parameter, ParseResponse

JAVA_LANGUAGE = Language(tsjava.language())
_parser = Parser(JAVA_LANGUAGE)

_class_query = JAVA_LANGUAGE.query("(class_declaration name: (identifier) @class.name)")

_import_query = JAVA_LANGUAGE.query("(import_declaration (scoped_identifier) @import)")

_method_query = JAVA_LANGUAGE.query("""
(method_declaration
  type: _ @return_type
  name: (identifier) @name
  parameters: (formal_parameters) @params
  body: (block) @body)
""")

_annotation_query = JAVA_LANGUAGE.query("""
[(marker_annotation name: (identifier) @ann)
 (annotation name: (identifier) @ann)]
""")

_param_query = JAVA_LANGUAGE.query("""
(formal_parameter
  type: _ @type
  name: (identifier) @name)
""")

_call_query = JAVA_LANGUAGE.query("(method_invocation name: (identifier) @callee)")


def parse(file_content: str, file_path: str = "") -> ParseResponse:
    try:
        return _parse(file_content, file_path)
    except Exception:
        return ParseResponse(
            file_path=file_path,
            class_name=None,
            imports=[],
            methods=[],
            call_graph=[],
        )


def _parse(file_content: str, file_path: str) -> ParseResponse:
    source = file_content.encode()
    tree = _parser.parse(source)
    root = tree.root_node

    class_name = _extract_class_name(root)
    imports = _extract_imports(root)
    methods = _extract_methods(root, file_content)
    call_graph = [
        CallEdge(caller=m.name, callees=m.callees)
        for m in methods
        if m.callees
    ]

    return ParseResponse(
        file_path=file_path,
        class_name=class_name,
        imports=imports,
        methods=methods,
        call_graph=call_graph,
    )


def _extract_class_name(root):
    captures = _class_query.captures(root)
    nodes = captures.get("class.name", [])
    return nodes[0].text.decode() if nodes else None


def _extract_imports(root) -> list[str]:
    captures = _import_query.captures(root)
    nodes = captures.get("import", [])
    return [n.text.decode() for n in nodes] if nodes else []


def _extract_methods(root, file_content: str) -> list[MethodInfo]:
    source = file_content.encode()
    methods: list[MethodInfo] = []

    for method_node in _find_method_nodes(root):
        query_captures = _method_query.captures(method_node)
        
        name_nodes = query_captures.get("name", [])
        return_nodes = query_captures.get("return_type", [])
        param_nodes = query_captures.get("params", [])
        body_nodes = query_captures.get("body", [])

        if not name_nodes:
            continue

        name = name_nodes[0].text.decode()
        return_type = return_nodes[0].text.decode() if return_nodes else "void"
        params = _extract_params(param_nodes[0]) if param_nodes else []
        body_node = body_nodes[0] if body_nodes else None

        annotations = _extract_annotations(method_node)
        callees = _extract_callees(body_node, name) if body_node else []
        signature = _build_signature(method_node, source)

        methods.append(MethodInfo(
            name=name,
            signature=signature,
            return_type=return_type,
            parameters=params,
            annotations=annotations,
            callees=callees,
        ))

    return methods


def _find_method_nodes(root) -> list:
    results = []
    cursor = root.walk()

    def visit(node):
        if node.type == "method_declaration":
            results.append(node)
        for child in node.children:
            visit(child)

    visit(root)
    return results


def _extract_params(params_node) -> list[Parameter]:
    captures = _param_query.captures(params_node)
    type_nodes = captures.get("type", [])
    name_nodes = captures.get("name", [])
    return [
        Parameter(type=t.text.decode(), name=n.text.decode())
        for t, n in zip(type_nodes, name_nodes)
    ]


def _extract_annotations(method_node) -> list[str]:
    # Annotations sit in the modifiers node that precedes the method
    modifiers = next(
        (c for c in method_node.children if c.type == "modifiers"),
        None,
    )
    if not modifiers:
        return []
    captures = _annotation_query.captures(modifiers)
    return [f"@{n.text.decode()}" for n in captures.get("ann", [])]


def _extract_callees(body_node, method_name: str) -> list[str]:
    captures = _call_query.captures(body_node)
    seen: set[str] = set()
    callees: list[str] = []
    for node in captures.get("callee", []):
        name = node.text.decode()
        if name != method_name and name not in seen:
            seen.add(name)
            callees.append(name)
    return callees


def _build_signature(method_node, source: bytes) -> str:
    # Slice from method start up to (not including) the body block
    body = next((c for c in method_node.children if c.type == "block"), None)
    end = body.start_byte if body else method_node.end_byte
    return source[method_node.start_byte:end].decode().strip()
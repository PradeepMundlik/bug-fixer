"""Maps tool-name strings to their Python functions for dispatch, and collects
their Grok/OpenAI-compatible JSON schemas for the LLM to consume later."""

from tools import find_callees as _find_callees
from tools import find_callers as _find_callers
from tools import get_method_signature as _get_method_signature
from tools import grep as _grep
from tools import read_file as _read_file
from tools import search_repository as _search_repository

# name -> callable
TOOL_REGISTRY = {
    "search_repository": _search_repository.search_repository,
    "find_callers": _find_callers.find_callers,
    "find_callees": _find_callees.find_callees,
    "get_method_signature": _get_method_signature.get_method_signature,
    "read_file": _read_file.read_file,
    "grep": _grep.grep,
}

# ordered list of function-calling schemas (one per tool)
TOOL_SCHEMAS = [
    _search_repository.SCHEMA,
    _find_callers.SCHEMA,
    _find_callees.SCHEMA,
    _get_method_signature.SCHEMA,
    _read_file.SCHEMA,
    _grep.SCHEMA,
]


def dispatch(name: str, args: dict):
    """Invoke the named tool with the given keyword arguments."""
    if name not in TOOL_REGISTRY:
        raise KeyError(name)
    return TOOL_REGISTRY[name](**args)

from typing import List, Type, TypeVar

import instructor
from openai import OpenAI
from pydantic import BaseModel

from agent.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_MODE

T = TypeVar("T", bound=BaseModel)

_client = None


def get_client() -> instructor.Instructor:
    """Lazily build the instructor-wrapped OpenAI-compatible client (Grok by default)."""
    global _client
    if _client is None:
        base = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
        _client = instructor.from_openai(base, mode=instructor.Mode[LLM_MODE])
    return _client


def structured_completion(
    messages: List[dict],
    response_model: Type[T],
    max_retries: int = 2,
    temperature: float = 0.2,
) -> T:
    """
    Call the LLM and coerce its reply into `response_model`. instructor validates the
    JSON against the Pydantic model and retries (feeding the validation error back to
    the model) up to `max_retries` times before raising.
    """
    return get_client().chat.completions.create(
        model=LLM_MODEL,
        response_model=response_model,
        messages=messages,
        max_retries=max_retries,
        temperature=temperature,
    )

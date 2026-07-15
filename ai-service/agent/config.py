import os

# LLM provider config. Defaults target xAI Grok, but every value is env-overridable
# so the same client works against OpenAI or any OpenAI-compatible endpoint.
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.x.ai/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "grok-2-latest")
LLM_MODE = os.getenv("LLM_MODE", "JSON")  # instructor.Mode name (JSON, TOOLS, MD_JSON, ...)

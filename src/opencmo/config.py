"""ENV-driven configuration system — supports OpenAI, NVIDIA, DeepSeek, and any OpenAI-compatible API."""

import os

from dotenv import load_dotenv

# Load .env EARLY — before any agent module calls get_model() at import time.
load_dotenv()

_MODEL_DEFAULT = "gpt-4o"

# Cached client instance
_custom_client = None


def _get_model_name(agent_name: str) -> str:
    """Resolve model name string from env vars."""
    specific = os.environ.get(f"OPENCMO_MODEL_{agent_name.upper()}")
    if specific:
        return specific
    return os.environ.get("OPENCMO_MODEL_DEFAULT", _MODEL_DEFAULT)


def _get_custom_client():
    """Create or return a cached AsyncOpenAI client for custom base URLs."""
    global _custom_client
    if _custom_client is None:
        from openai import AsyncOpenAI

        _custom_client = AsyncOpenAI(
            base_url=os.environ.get("OPENAI_BASE_URL"),
            api_key=os.environ.get("OPENAI_API_KEY"),
        )
    return _custom_client


def reset_client():
    """Reset the cached client so next call uses current env vars."""
    global _custom_client
    _custom_client = None


def is_custom_provider() -> bool:
    """True if a non-default OPENAI_BASE_URL is configured."""
    return bool(os.environ.get("OPENAI_BASE_URL"))


def get_model(agent_name: str):
    """Return the model for a given agent.

    Resolution order for model name:
        OPENCMO_MODEL_{AGENT} > OPENCMO_MODEL_DEFAULT > 'gpt-4o'

    If OPENAI_BASE_URL is set, returns an OpenAIChatCompletionsModel
    configured with a custom client (works with NVIDIA, DeepSeek, etc.).
    Otherwise returns a plain model name string (uses OpenAI default).
    """
    model_name = _get_model_name(agent_name)

    if is_custom_provider():
        from agents import OpenAIChatCompletionsModel

        return OpenAIChatCompletionsModel(
            model=model_name,
            openai_client=_get_custom_client(),
        )

    return model_name


async def apply_runtime_settings():
    """Load API settings from DB and apply to os.environ + reset client cache."""
    from opencmo import storage

    for key in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENCMO_MODEL_DEFAULT"):
        val = await storage.get_setting(key)
        if val:
            os.environ[key] = val
        # If DB value was cleared but env had it from .env, keep it

    reset_client()

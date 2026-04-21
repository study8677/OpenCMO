"""ENV-driven configuration system — supports OpenAI, NVIDIA, DeepSeek, and any OpenAI-compatible API.

This module provides the get_model() function used by the openai-agents framework.
LLM client creation is delegated to opencmo.llm for ContextVar-based key isolation.
"""

from dotenv import load_dotenv

# Load .env EARLY — before any agent module calls get_model() at import time.
load_dotenv()


def get_model(agent_name: str):
    """Return the model for a given agent.

    Resolution order for model name:
        OPENCMO_MODEL_{AGENT} > OPENCMO_MODEL_DEFAULT > 'gpt-5.4'

    If OPENAI_BASE_URL is set, returns an OpenAIChatCompletionsModel
    configured with a custom client (works with NVIDIA, DeepSeek, etc.).
    Otherwise returns a plain model name string (uses OpenAI default).
    """
    from opencmo import llm

    model_name = llm.get_key(f"OPENCMO_MODEL_{agent_name.upper()}")
    if not model_name:
        model_name = llm.get_key("OPENCMO_MODEL_DEFAULT", "gpt-5.4")

    base_url = llm.normalize_base_url(llm.get_key("OPENAI_BASE_URL"))
    if base_url:
        from agents import OpenAIChatCompletionsModel
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            base_url=base_url,
            api_key=llm.get_key("OPENAI_API_KEY"),
        )
        return OpenAIChatCompletionsModel(
            model=model_name,
            openai_client=client,
        )

    return model_name


def is_custom_provider() -> bool:
    """True if a non-default OPENAI_BASE_URL is configured."""
    from opencmo import llm
    return bool(llm.get_key("OPENAI_BASE_URL"))


def configure_agent_tracing() -> bool:
    """Disable agents tracing when using a custom OpenAI-compatible provider.

    The agents SDK exports traces to OpenAI's backend by default. When the runtime
    API key belongs to a third-party OpenAI-compatible gateway (OpenRouter,
    DeepSeek, NVIDIA, etc.), that export path emits noisy 401 errors. We disable
    tracing globally in those cases because the trace exporter is not used by the
    product at runtime.

    Returns:
        True when tracing was disabled, False otherwise.
    """
    custom_provider = is_custom_provider()
    from agents import set_tracing_disabled

    set_tracing_disabled(custom_provider)
    return custom_provider


async def apply_runtime_settings():
    """Load API settings from DB and apply to os.environ.

    Called once at startup to populate env from DB-stored settings.
    After this, llm.get_key() will find values via os.environ fallback.
    """
    import os

    from opencmo import storage

    for key in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENCMO_MODEL_DEFAULT"):
        val = await storage.get_setting(key)
        if val:
            os.environ[key] = val
        # If DB value was cleared but env had it from .env, keep it

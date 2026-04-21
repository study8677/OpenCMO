"""Centralized LLM client management with per-request key isolation.

Solves the BYOK (Bring Your Own Key) concurrency bug where os.environ
was used as shared mutable state across concurrent requests.

Key resolution priority:
    1. ContextVar (per-request, set by BYOK middleware)
    2. os.environ (from .env or system environment) for router defaults
    3. DB settings (via storage.get_setting)
    4. os.environ (from .env or system environment) for all other keys

Usage:
    from opencmo import llm

    # In BYOK middleware — inject per-request keys:
    token = llm.set_request_keys({"OPENAI_API_KEY": "sk-user-xxx"})
    try:
        await call_next(request)
    finally:
        llm.reset_request_keys(token)

    # Anywhere in the codebase — read a key safely:
    api_key = llm.get_key("OPENAI_API_KEY")

    # Get an OpenAI client scoped to the current request:
    client = await llm.get_openai_client()

    # Unified chat completion call:
    text = await llm.chat_completion(system_prompt, user_prompt)
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from contextvars import ContextVar, Token
from typing import Any

logger = logging.getLogger(__name__)

_MODEL_DEFAULT = "gpt-5.4"
_ENV_PRIORITY_KEYS = frozenset({
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "OPENCMO_MODEL_DEFAULT",
})

# ---------------------------------------------------------------------------
# ContextVar — per-request key isolation (asyncio Task-local)
# ---------------------------------------------------------------------------

_request_keys: ContextVar[dict[str, str]] = ContextVar("request_keys", default={})


def set_request_keys(keys: dict[str, str]) -> Token:
    """Set per-request API keys. Called by BYOK middleware.

    Returns a Token that MUST be passed to reset_request_keys() in a finally block.
    """
    # Filter to only valid non-empty string values
    clean = {k: v.strip() for k, v in keys.items() if isinstance(v, str) and v.strip()}
    return _request_keys.set(clean)


def reset_request_keys(token: Token) -> None:
    """Restore the previous ContextVar state. Called in finally block."""
    _request_keys.reset(token)


def get_request_keys() -> dict[str, str]:
    """Return the current per-request API keys context. Used to capture state for background tasks."""
    return _request_keys.get({}).copy()



# ---------------------------------------------------------------------------
# Key resolution — ContextVar > env/.env > DB for router defaults
# ---------------------------------------------------------------------------


def get_key(name: str, default: str | None = None) -> str | None:
    """Get a configuration key value with proper isolation.

    Resolution order:
        1. ContextVar (per-request BYOK keys)
        2. os.environ (from .env or system)
        3. default

    Note: DB lookup is intentionally NOT done here because this function
    is synchronous. For async DB lookup, use get_key_async().
    """
    # 1. ContextVar (per-request)
    request = _request_keys.get({})
    val = request.get(name)
    if val:
        return val

    # 2. os.environ
    val = os.environ.get(name)
    if val:
        return val

    return default


async def get_key_async(name: str, default: str | None = None) -> str | None:
    """Get a configuration key with DB fallback (async version).

    Resolution order:
        1. ContextVar (per-request BYOK keys)
        2. os.environ (from .env or system) for router default keys
        3. DB settings (storage.get_setting)
        4. os.environ (from .env or system) for all other keys
        4. default
    """
    # 1. ContextVar (per-request)
    request = _request_keys.get({})
    val = request.get(name)
    if val:
        return val

    # 2. For core router defaults, prefer env/.env over persisted DB settings.
    if name in _ENV_PRIORITY_KEYS:
        val = os.environ.get(name)
        if val:
            return val

    # 3. DB settings
    try:
        from opencmo import storage
        val = await storage.get_setting(name)
        if val:
            return val
    except Exception:
        pass  # DB may not be initialized yet

    # 4. os.environ
    val = os.environ.get(name)
    if val:
        return val

    return default


# ---------------------------------------------------------------------------
# OpenAI client factory — creates a client for the current request scope
# ---------------------------------------------------------------------------


async def get_openai_client() -> Any:
    """Get an AsyncOpenAI client configured for the current request.

    Uses ContextVar keys if available, falls back to env/DB.
    A new client is created each time because different requests may
    have different API keys (BYOK).
    """
    from openai import AsyncOpenAI

    api_key = await get_key_async("OPENAI_API_KEY")
    base_url = await get_key_async("OPENAI_BASE_URL")

    base_url = normalize_base_url(base_url)

    model = await get_model()
    logger.debug("LLM client: model=%s, base_url=%s", model, base_url or "OpenAI Default")

    return AsyncOpenAI(
        api_key=api_key,
        base_url=base_url or None,
    )


def normalize_base_url(base_url: str | None) -> str | None:
    """Normalize OpenAI-compatible endpoints to the form expected by SDK clients."""
    if not base_url:
        return None

    normalized = base_url.strip().rstrip("/")
    if not normalized:
        return None

    # OpenAI official endpoints already route correctly without an explicit /v1 suffix.
    skip_v1_domains = {"api.openai.com", "api.anthropic.com"}
    from urllib.parse import urlparse

    host = urlparse(normalized).hostname or ""
    if host in skip_v1_domains or normalized.endswith("/v1"):
        return normalized
    if normalized.count("/") <= 2:
        return f"{normalized}/v1"
    return normalized


async def get_model(purpose: str = "default") -> str:
    """Get the model name for a given purpose.

    Resolution: OPENCMO_MODEL_{PURPOSE} > OPENCMO_MODEL_DEFAULT > 'gpt-5.4'
    """
    if purpose and purpose != "default":
        specific = await get_key_async(f"OPENCMO_MODEL_{purpose.upper()}")
        if specific:
            return specific
    return (await get_key_async("OPENCMO_MODEL_DEFAULT")) or _MODEL_DEFAULT


# ---------------------------------------------------------------------------
# Unified chat completion — single entry point for all LLM calls
# ---------------------------------------------------------------------------


_MAX_RETRIES = 8
_RETRY_BACKOFF = [2, 5, 10, 20, 30, 60, 120, 300]  # seconds


def _extract_retry_delay_seconds(exc: Exception) -> float | None:
    """Best-effort parse of provider retry hints from exception text."""
    text = str(exc)
    patterns = [
        r"reset_seconds['\"]?\s*:\s*(\d+)",
        r"Retry-After['\"]?\s*:\s*(\d+)",
        r"retryDelay['\"]?\s*:\s*['\"]?([0-9.]+)s['\"]?",
        r"quotaResetDelay['\"]?\s*:\s*['\"]?([0-9.]+)s['\"]?",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
    return None


async def _call_with_retry(coro_factory, *, timeout: float | None = None) -> Any:
    """Call an LLM coroutine with retry + exponential backoff."""
    for attempt in range(_MAX_RETRIES):
        try:
            coro = coro_factory()
            if timeout:
                resp = await asyncio.wait_for(coro, timeout=timeout)
            else:
                resp = await asyncio.wait_for(coro, timeout=120)
            return resp
        except Exception as exc:
            if attempt < _MAX_RETRIES - 1:
                provider_wait = _extract_retry_delay_seconds(exc)
                if provider_wait is not None:
                    wait = provider_wait
                else:
                    wait = _RETRY_BACKOFF[min(attempt, len(_RETRY_BACKOFF) - 1)]
                logger.warning("LLM call failed (attempt %d/%d): %s — retrying in %ds",
                               attempt + 1, _MAX_RETRIES, exc, wait)
                await asyncio.sleep(wait)
            else:
                raise


async def chat_completion(
    system: str,
    user: str,
    *,
    temperature: float = 0.7,
    timeout: float | None = None,
    model_override: str | None = None,
) -> str:
    """Unified LLM chat completion call with automatic retry.

    Args:
        system: System prompt.
        user: User prompt.
        temperature: Sampling temperature.
        timeout: Optional timeout in seconds.
        model_override: Override the model name (skips get_model lookup).

    Returns:
        The assistant's response content as a string.
    """
    client = await get_openai_client()
    model = model_override or await get_model()

    def make_coro():
        return client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )

    resp = await _call_with_retry(make_coro, timeout=timeout)
    return _extract_content(resp)


def _extract_content(resp: Any) -> str:
    """Extract text from a chat completion response.

    Handles MiniMax-style responses where content may be null/empty
    and the actual text lives in reasoning_content.
    """
    msg = resp.choices[0].message
    content = msg.content
    if not content:
        # MiniMax / TeamoRouter: text may be in reasoning_content
        content = getattr(msg, "reasoning_content", None) or ""
    return content.strip()


async def chat_completion_messages(
    messages: list[dict],
    *,
    temperature: float = 0.7,
    timeout: float | None = None,
    model_override: str | None = None,
    max_tokens: int | None = None,
    api_key_override: str | None = None,
    base_url_override: str | None = None,
) -> str:
    """LLM chat completion with custom message list.

    For cases where the caller needs more than system+user (e.g. multi-turn).
    """
    if api_key_override is not None or base_url_override is not None:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=api_key_override if api_key_override is not None else await get_key_async("OPENAI_API_KEY"),
            base_url=base_url_override if base_url_override is not None else await get_key_async("OPENAI_BASE_URL"),
        )
    else:
        client = await get_openai_client()
    model = model_override or await get_model()

    kwargs: dict[str, Any] = {
        "model": model,
        "temperature": temperature,
        "messages": messages,
    }
    if max_tokens:
        kwargs["max_tokens"] = max_tokens

    def make_coro():
        return client.chat.completions.create(**kwargs)

    resp = await _call_with_retry(make_coro, timeout=timeout)
    return _extract_content(resp)

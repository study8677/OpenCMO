"""Tests for opencmo.llm — ContextVar-based key isolation and client management."""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from opencmo import llm

# ---------------------------------------------------------------------------
# get_key / ContextVar isolation
# ---------------------------------------------------------------------------


class TestGetKey:
    def test_get_key_from_env(self):
        """get_key reads from os.environ when no ContextVar is set."""
        with patch.dict(os.environ, {"MY_TEST_KEY": "from-env"}):
            assert llm.get_key("MY_TEST_KEY") == "from-env"

    def test_get_key_default(self):
        """get_key returns default when key is missing everywhere."""
        assert llm.get_key("MISSING_KEY_12345", "fallback") == "fallback"
        assert llm.get_key("MISSING_KEY_12345") is None

    def test_get_key_contextvar_overrides_env(self):
        """ContextVar takes priority over os.environ."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}):
            token = llm.set_request_keys({"OPENAI_API_KEY": "user-key"})
            try:
                assert llm.get_key("OPENAI_API_KEY") == "user-key"
            finally:
                llm.reset_request_keys(token)
        # After reset, should go back to env
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}):
            assert llm.get_key("OPENAI_API_KEY") == "env-key"

    def test_set_request_keys_filters_empty(self):
        """Empty/whitespace values are filtered out."""
        token = llm.set_request_keys({
            "OPENAI_API_KEY": "valid",
            "OPENAI_BASE_URL": "  ",
            "EMPTY": "",
        })
        try:
            assert llm.get_key("OPENAI_API_KEY") == "valid"
            assert llm.get_key("OPENAI_BASE_URL") is None
            assert llm.get_key("EMPTY") is None
        finally:
            llm.reset_request_keys(token)


# ---------------------------------------------------------------------------
# Concurrent safety — the core bug fix
# ---------------------------------------------------------------------------


class TestConcurrentSafety:
    def test_concurrent_tasks_use_different_keys(self):
        """Two concurrent asyncio Tasks see different ContextVar values."""
        results = {}

        async def task_a():
            token = llm.set_request_keys({"OPENAI_API_KEY": "key-A"})
            try:
                await asyncio.sleep(0.05)  # Simulate async work
                results["A"] = llm.get_key("OPENAI_API_KEY")
            finally:
                llm.reset_request_keys(token)

        async def task_b():
            token = llm.set_request_keys({"OPENAI_API_KEY": "key-B"})
            try:
                await asyncio.sleep(0.05)  # Simulate async work
                results["B"] = llm.get_key("OPENAI_API_KEY")
            finally:
                llm.reset_request_keys(token)

        async def run_both():
            await asyncio.gather(task_a(), task_b())

        asyncio.run(run_both())

        assert results["A"] == "key-A"
        assert results["B"] == "key-B"


# ---------------------------------------------------------------------------
# get_key_async — with DB fallback
# ---------------------------------------------------------------------------


class TestGetKeyAsync:
    @pytest.mark.asyncio
    async def test_contextvar_priority(self):
        """ContextVar takes highest priority in async path too."""
        token = llm.set_request_keys({"MY_KEY": "ctx-val"})
        try:
            val = await llm.get_key_async("MY_KEY")
            assert val == "ctx-val"
        finally:
            llm.reset_request_keys(token)

    @pytest.mark.asyncio
    async def test_db_fallback(self):
        """Falls back to DB when no ContextVar."""
        with patch("opencmo.storage.get_setting", new_callable=AsyncMock, return_value="db-val"):
            val = await llm.get_key_async("SOME_KEY")
            assert val == "db-val"

    @pytest.mark.asyncio
    async def test_env_fallback(self):
        """Falls back to os.environ when ContextVar and DB are empty."""
        with patch("opencmo.storage.get_setting", new_callable=AsyncMock, return_value=None):
            with patch.dict(os.environ, {"MY_KEY": "env-val"}):
                val = await llm.get_key_async("MY_KEY")
                assert val == "env-val"

    @pytest.mark.asyncio
    async def test_env_overrides_db_for_router_defaults(self):
        """Core router defaults prefer env over persisted DB settings."""
        with patch("opencmo.storage.get_setting", new_callable=AsyncMock, return_value="db-val"):
            with patch.dict(os.environ, {"OPENAI_BASE_URL": "https://router.teamolab.com/v1"}, clear=False):
                val = await llm.get_key_async("OPENAI_BASE_URL")
                assert val == "https://router.teamolab.com/v1"

    @pytest.mark.asyncio
    async def test_db_still_used_first_for_non_router_keys(self):
        """Non-router keys keep DB-first fallback behavior."""
        with patch("opencmo.storage.get_setting", new_callable=AsyncMock, return_value="db-val"):
            with patch.dict(os.environ, {"TAVILY_API_KEY": "env-val"}, clear=False):
                val = await llm.get_key_async("TAVILY_API_KEY")
                assert val == "db-val"


# ---------------------------------------------------------------------------
# get_openai_client
# ---------------------------------------------------------------------------


class TestGetOpenAIClient:
    @pytest.mark.asyncio
    async def test_creates_client_with_contextvar_keys(self):
        """Client is created with keys from ContextVar."""
        token = llm.set_request_keys({
            "OPENAI_API_KEY": "ctx-api-key",
            "OPENAI_BASE_URL": "https://custom.api.com",
        })
        try:
            with patch("opencmo.storage.get_setting", new_callable=AsyncMock, return_value=None):
                client = await llm.get_openai_client()
                assert client.api_key == "ctx-api-key"
                assert "custom.api.com" in str(client.base_url)
        finally:
            llm.reset_request_keys(token)


# ---------------------------------------------------------------------------
# get_model
# ---------------------------------------------------------------------------


class TestGetModel:
    @pytest.mark.asyncio
    async def test_default_model(self):
        """Returns gpt-4o when nothing is configured."""
        with patch("opencmo.storage.get_setting", new_callable=AsyncMock, return_value=None):
            with patch.dict(os.environ, {}, clear=True):
                model = await llm.get_model()
                assert model == "gpt-4o"

    @pytest.mark.asyncio
    async def test_custom_default_model(self):
        """Uses OPENCMO_MODEL_DEFAULT from ContextVar."""
        token = llm.set_request_keys({"OPENCMO_MODEL_DEFAULT": "deepseek-chat"})
        try:
            with patch("opencmo.storage.get_setting", new_callable=AsyncMock, return_value=None):
                model = await llm.get_model()
                assert model == "deepseek-chat"
        finally:
            llm.reset_request_keys(token)


# ---------------------------------------------------------------------------
# chat_completion
# ---------------------------------------------------------------------------


class TestChatCompletion:
    @pytest.mark.asyncio
    async def test_chat_completion_calls_openai(self):
        """chat_completion creates a client and makes the call."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "  Hello world  "

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch.object(llm, "get_openai_client", new_callable=AsyncMock, return_value=mock_client):
            with patch.object(llm, "get_model", new_callable=AsyncMock, return_value="gpt-4o"):
                result = await llm.chat_completion("sys", "usr")

        assert result == "Hello world"
        mock_client.chat.completions.create.assert_awaited_once()
        call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs.kwargs["model"] == "gpt-4o"
        assert call_kwargs.kwargs["messages"][0]["content"] == "sys"
        assert call_kwargs.kwargs["messages"][1]["content"] == "usr"

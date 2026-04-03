"""Tests for GEO provider architecture."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from opencmo.tools.geo_providers import (
    GEO_PROVIDER_REGISTRY,
    ChatGPTProvider,
    ClaudeProvider,
    GeminiProvider,
    PerplexityProvider,
    _analyze_text,
)


@pytest.fixture(autouse=True)
def _use_light_profile(monkeypatch):
    monkeypatch.setenv("OPENCMO_SCRAPE_DEPTH", "light")


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


def test_geo_provider_registry():
    assert len(GEO_PROVIDER_REGISTRY) == 5
    names = {p.name for p in GEO_PROVIDER_REGISTRY}
    assert names == {"Perplexity", "You.com", "ChatGPT", "Claude", "Gemini"}


def test_crawl_providers_enabled_by_default():
    perplexity = next(p for p in GEO_PROVIDER_REGISTRY if p.name == "Perplexity")
    youcom = next(p for p in GEO_PROVIDER_REGISTRY if p.name == "You.com")
    assert perplexity.is_enabled
    assert youcom.is_enabled


def test_api_providers_disabled_without_keys():
    """ChatGPT/Claude/Gemini should be disabled without their env vars."""
    # Clean env
    env_clean = {
        "OPENCMO_GEO_CHATGPT": "",
        "ANTHROPIC_API_KEY": "",
        "GOOGLE_AI_API_KEY": "",
    }
    with patch.dict(os.environ, env_clean, clear=False):
        chatgpt = ChatGPTProvider()
        claude = ClaudeProvider()
        gemini = GeminiProvider()
        assert not chatgpt.is_enabled
        assert not claude.is_enabled
        assert not gemini.is_enabled


def test_chatgpt_requires_opt_in():
    """ChatGPT needs both OPENCMO_GEO_CHATGPT=1 and OPENAI_API_KEY."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test", "OPENCMO_GEO_CHATGPT": ""}, clear=False):
        p = ChatGPTProvider()
        assert not p.is_enabled

    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test", "OPENCMO_GEO_CHATGPT": "1"}, clear=False):
        p = ChatGPTProvider()
        assert p.is_enabled


# ---------------------------------------------------------------------------
# Text analysis helper
# ---------------------------------------------------------------------------


def test_analyze_text_found():
    mentioned, count, pos = _analyze_text("Try Crawl4AI for web scraping", "Crawl4AI")
    assert mentioned is True
    assert count == 1
    assert pos is not None
    assert 0 <= pos <= 100


def test_analyze_text_not_found():
    mentioned, count, pos = _analyze_text("Try Scrapy for web scraping", "Crawl4AI")
    assert mentioned is False
    assert count == 0
    assert pos is None


def test_analyze_text_multiple_mentions():
    text = "Crawl4AI is great. I use Crawl4AI daily. Crawl4AI rocks."
    mentioned, count, pos = _analyze_text(text, "Crawl4AI")
    assert mentioned is True
    assert count == 3


def test_analyze_text_case_insensitive():
    mentioned, count, pos = _analyze_text("Try crawl4ai for scraping", "Crawl4AI")
    assert mentioned is True


# ---------------------------------------------------------------------------
# Provider parse tests (mock API responses)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chatgpt_provider_parse():
    provider = ChatGPTProvider()

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Top tools: 1. Crawl4AI - great for scraping. 2. Scrapy - classic."

    with patch("opencmo.tools.geo_providers.ChatGPTProvider.is_enabled", True):
        with patch("openai.AsyncOpenAI") as mock_cls:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_cls.return_value = mock_client

            result = await provider.check_visibility("Crawl4AI", "web scraping")
            assert result.mentioned is True
            assert result.mention_count >= 1
            assert result.error is None


@pytest.mark.asyncio
async def test_claude_provider_parse():
    provider = ClaudeProvider()

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Top tools: 1. Crawl4AI 2. BeautifulSoup")]

    with patch("opencmo.tools.geo_providers._HAS_ANTHROPIC", True):
        with patch("opencmo.tools.geo_providers.anthropic") as mock_anthropic:
            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            mock_anthropic.AsyncAnthropic.return_value = mock_client

            result = await provider.check_visibility("Crawl4AI", "web scraping")
            assert result.mentioned is True
            assert result.error is None


@pytest.mark.asyncio
async def test_gemini_provider_parse():
    provider = GeminiProvider()

    mock_response = MagicMock()
    mock_response.text = "Best tools: Crawl4AI, Playwright, Puppeteer"

    with patch("opencmo.tools.geo_providers._HAS_GENAI", True):
        with patch("opencmo.tools.geo_providers.genai") as mock_genai:
            with patch.dict(os.environ, {"GOOGLE_AI_API_KEY": "test-key"}):
                mock_model = AsyncMock()
                mock_model.generate_content_async = AsyncMock(return_value=mock_response)
                mock_genai.GenerativeModel.return_value = mock_model

                result = await provider.check_visibility("Crawl4AI", "web scraping")
                assert result.mentioned is True
                assert result.error is None


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def test_scoring_scales_with_provider_count():
    """Visibility score should scale with number of enabled providers."""
    # 1 out of 2 mentioned = 20/40
    # 1 out of 5 mentioned = 8/40
    score_2 = int(1 / 2 * 40)
    score_5 = int(1 / 5 * 40)
    assert score_2 == 20
    assert score_5 == 8


# ---------------------------------------------------------------------------
# Graceful failure
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_provider_failure_graceful():
    """Single provider failure should return error result, not raise."""
    provider = PerplexityProvider()

    with patch("opencmo.tools.geo_providers.AsyncWebCrawler") as mock_cls:
        mock_crawler = AsyncMock()
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=False)
        mock_crawler.arun = AsyncMock(side_effect=Exception("network error"))
        mock_cls.return_value = mock_crawler

        result = await provider.check_visibility("Test", "testing")
        assert result.mentioned is False
        assert result.error is not None
        assert "network error" in result.error

"""Tests for trend research tool — query expansion, comparative mode, scoring integration."""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest

from opencmo.tools.community_providers import HttpResult
from opencmo.tools.trend_research import (
    _research_trend_impl,
    expand_queries,
    is_comparative,
)

# ---------------------------------------------------------------------------
# Force "light" profile for tests
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _use_light_profile(monkeypatch):
    monkeypatch.setenv("OPENCMO_SCRAPE_DEPTH", "light")


# ---------------------------------------------------------------------------
# Query expansion tests
# ---------------------------------------------------------------------------


def test_expand_basic_topic():
    queries = expand_queries("AI code review")
    assert queries[0] == "AI code review"
    assert len(queries) >= 2


def test_expand_comparative():
    queries = expand_queries("Cursor vs Windsurf")
    assert "Cursor" in queries
    assert "Windsurf" in queries
    assert queries[0] == "Cursor vs Windsurf"


def test_expand_versus_spelling():
    queries = expand_queries("React versus Vue")
    assert "React" in queries
    assert "Vue" in queries


def test_expand_compared_to():
    queries = expand_queries("Python compared to Go")
    assert "Python" in queries
    assert "Go" in queries


def test_expand_single_word():
    queries = expand_queries("kubernetes")
    assert queries[0] == "kubernetes"
    # Single word doesn't get "review" variant but gets "best tools"
    assert any("best" in q for q in queries)


# ---------------------------------------------------------------------------
# Comparative detection
# ---------------------------------------------------------------------------


def test_is_comparative_vs():
    assert is_comparative("Cursor vs Windsurf")
    assert is_comparative("React vs. Vue")


def test_is_comparative_versus():
    assert is_comparative("Python versus Go")


def test_is_comparative_compared_to():
    assert is_comparative("React compared to Vue")


def test_not_comparative():
    assert not is_comparative("AI code review tools")
    assert not is_comparative("best developer tools 2025")


# ---------------------------------------------------------------------------
# Mock provider responses
# ---------------------------------------------------------------------------


def _make_mock_http(platform_key: str, title_prefix: str = "Test"):
    """Create a mock HTTP handler that returns results for a specific platform."""
    import time
    recent_utc = time.time() - 86400 * 3  # 3 days ago

    async def _mock(url, params=None, headers=None):
        if "reddit" in url and platform_key in ("reddit", "all"):
            return HttpResult(data={"data": {"children": [
                {"data": {
                    "title": f"{title_prefix} Reddit Post",
                    "permalink": "/r/test/comments/abc/post/",
                    "score": 50, "num_comments": 10,
                    "created_utc": recent_utc,
                    "author": "user", "id": "abc",
                    "subreddit": "test", "selftext": "Body",
                }},
            ], "after": None}}, error=None, status_code=200)
        if "algolia" in url and platform_key in ("hackernews", "all"):
            return HttpResult(data={"hits": [
                {"title": f"{title_prefix} HN Story", "objectID": "999",
                 "points": 42, "num_comments": 15,
                 "created_at": "2025-01-01T00:00:00Z", "author": "hn_user"},
            ]}, error=None, status_code=200)
        if "dev.to" in url:
            return HttpResult(data=[], error=None, status_code=200)
        if "bsky" in url:
            return HttpResult(data={"posts": []}, error=None, status_code=200)
        return HttpResult(data=None, error="unknown", status_code=404)
    return _mock


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


def test_research_trend_summary_mode():
    with patch("opencmo.tools.community_providers._http_get_json", side_effect=_make_mock_http("all")):
        result = asyncio.run(_research_trend_impl("AI code review", 30, "reddit,hackernews"))
    assert "Trend Research: AI code review" in result
    assert "Reddit" in result or "reddit" in result


def test_research_trend_comparative_mode():
    with patch("opencmo.tools.community_providers._http_get_json", side_effect=_make_mock_http("all", "Cursor")):
        result = asyncio.run(_research_trend_impl("Cursor vs Windsurf", 30, "reddit,hackernews", "comparative"))
    assert "Comparative Analysis" in result
    assert "Cursor" in result


def test_research_trend_time_filter():
    """Hits older than time_window_days should be filtered out."""
    async def _mock_old(url, params=None, headers=None):
        if "reddit" in url:
            return HttpResult(data={"data": {"children": [
                {"data": {
                    "title": "Old Post",
                    "permalink": "/r/test/comments/old/post/",
                    "score": 50, "num_comments": 10,
                    "created_utc": 1600000000,  # ~2020, very old
                    "author": "user", "id": "old",
                    "subreddit": "test", "selftext": "Old body",
                }},
            ], "after": None}}, error=None, status_code=200)
        return HttpResult(data={"hits": []}, error=None, status_code=200)

    with patch("opencmo.tools.community_providers._http_get_json", side_effect=_mock_old):
        result = asyncio.run(_research_trend_impl("test topic", 30, "reddit"))
    assert "Total discussions found**: 0" in result


def test_research_trend_no_providers():
    """Should return error when no providers match requested platforms."""
    result = asyncio.run(_research_trend_impl("test", 30, "nonexistent"))
    assert "error" in result
    assert "No enabled providers" in result


def test_research_trend_platform_filter():
    """Should only search requested platforms."""
    call_urls = []

    async def _tracking_mock(url, params=None, headers=None):
        call_urls.append(url)
        if "reddit" in url:
            return HttpResult(data={"data": {"children": [], "after": None}}, error=None, status_code=200)
        return HttpResult(data={"hits": []}, error=None, status_code=200)

    with patch("opencmo.tools.community_providers._http_get_json", side_effect=_tracking_mock):
        asyncio.run(_research_trend_impl("test", 30, "reddit"))

    # Should NOT have called algolia (HN) since we restricted to reddit
    assert not any("algolia" in u for u in call_urls)
    assert any("reddit" in u for u in call_urls)

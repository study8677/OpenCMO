"""Tests for community_providers — structure, parsing, and error handling."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from opencmo.tools.community_providers import (
    PROVIDER_REGISTRY,
    BlogSearchProvider,
    DevtoProvider,
    DiscussionHit,
    HackerNewsProvider,
    HttpResult,
    LinkedInProvider,
    ProductHuntProvider,
    ProviderSearchResult,
    RedditProvider,
    TwitterProvider,
)


# ---------------------------------------------------------------------------
# Provider structure tests
# ---------------------------------------------------------------------------


def test_provider_registry_has_all_platforms():
    names = {p.name for p in PROVIDER_REGISTRY}
    assert names == {"reddit", "hackernews", "devto", "twitter", "linkedin", "producthunt", "blog"}


def test_free_providers_enabled_by_default():
    for p in PROVIDER_REGISTRY:
        if p.name in ("reddit", "hackernews", "devto"):
            assert p.is_enabled, f"{p.name} should be enabled"


def test_stub_providers_disabled():
    for p in PROVIDER_REGISTRY:
        if p.name in ("twitter", "linkedin", "producthunt", "blog"):
            assert not p.is_enabled, f"{p.name} should be disabled (stub)"
            assert p.status == "stub"


def test_blog_provider_no_auth_but_stub():
    blog = BlogSearchProvider()
    assert blog.requires_auth is False
    assert blog.status == "stub"
    assert not blog.is_enabled


# ---------------------------------------------------------------------------
# Reddit parse tests
# ---------------------------------------------------------------------------


def _make_reddit_search_json(count: int = 2) -> dict:
    children = []
    for i in range(count):
        children.append({
            "data": {
                "title": f"Post {i}",
                "permalink": f"/r/test/comments/abc{i}/post_{i}/",
                "score": 10 + i,
                "num_comments": 5 + i,
                "created_utc": 1700000000 + i * 86400,
                "author": f"user{i}",
                "id": f"abc{i}",
                "subreddit": "test",
                "selftext": f"Body text for post {i}",
            }
        })
    return {"data": {"children": children}}


def test_reddit_provider_parse_search():
    data = _make_reddit_search_json(3)
    hits = RedditProvider.parse_search_response(data, "brand_search")
    assert len(hits) == 3
    h = hits[0]
    assert h.platform == "reddit"
    assert h.title == "Post 0"
    assert h.detail_id == "abc0"
    assert h.extra_param_1 == "test"
    assert h.extra_param_2 == ""
    assert h.source == "brand_search"
    assert h.raw_score == 10
    assert h.engagement_score == min(100, 10 * 2)


def test_reddit_provider_parse_detail():
    post_listing = {
        "data": {
            "children": [{
                "data": {
                    "title": "My Post",
                    "selftext": "Full body here",
                    "permalink": "/r/test/comments/abc0/my_post/",
                }
            }]
        }
    }
    comment_listing = {
        "data": {
            "children": [
                {"kind": "t1", "data": {"author": "commenter1", "body": "Nice post!", "score": 3}},
                {"kind": "t1", "data": {"author": "commenter2", "body": "Thanks!", "score": 1}},
                {"kind": "t3", "data": {"author": "bot", "body": "ignored"}},  # not t1
            ]
        }
    }
    hit = DiscussionHit(
        platform="reddit", title="My Post", url="https://reddit.com/r/test",
        engagement_score=20, raw_score=10, comments_count=2, age_days=1,
        author="op", detail_id="abc0", extra_param_1="test", extra_param_2="",
        preview="", source="brand_search",
    )
    detail = RedditProvider.parse_detail_response([post_listing, comment_listing], hit)
    assert detail is not None
    assert detail.title == "My Post"
    assert detail.full_content == "Full body here"
    assert len(detail.comments) == 2  # t3 filtered out
    assert detail.comments[0]["author"] == "commenter1"


# ---------------------------------------------------------------------------
# HN parse tests
# ---------------------------------------------------------------------------


def _make_hn_search_json(count: int = 2) -> dict:
    return {
        "hits": [
            {
                "title": f"HN Story {i}",
                "objectID": str(1000 + i),
                "points": 20 + i * 10,
                "num_comments": 8 + i,
                "created_at": "2024-01-01T00:00:00.000Z",
                "author": f"hn_user{i}",
                "story_text": f"Story text {i}",
            }
            for i in range(count)
        ]
    }


def test_hn_provider_parse_search():
    data = _make_hn_search_json(2)
    hits = HackerNewsProvider.parse_search_response(data, "brand_search")
    assert len(hits) == 2
    h = hits[0]
    assert h.platform == "hackernews"
    assert h.detail_id == "1000"
    assert h.raw_score == 20
    assert h.engagement_score == min(100, int(20 * 1.5))


def test_hn_provider_parse_comments():
    data = {
        "hits": [
            {"author": "c1", "comment_text": "Great stuff", "points": 5},
            {"author": "c2", "comment_text": "Interesting", "points": 2},
            {"author": "c3", "comment_text": "", "points": 0},  # empty → skipped
        ]
    }
    comments = HackerNewsProvider.parse_comments_response(data)
    assert len(comments) == 2
    assert comments[0]["author"] == "c1"
    assert comments[0]["text"] == "Great stuff"


# ---------------------------------------------------------------------------
# Dev.to parse tests
# ---------------------------------------------------------------------------


def test_devto_provider_tag_fallback():
    """When all tag searches return empty, provider adds a suggested_query."""

    async def _mock_get_json(url, params=None, headers=None):
        return HttpResult(data=[], error=None, status_code=200)

    with patch("opencmo.tools.community_providers._http_get_json", side_effect=_mock_get_json):
        provider = DevtoProvider()
        result = asyncio.run(provider.search("MyBrand", "web scraping"))
        assert len(result.hits) == 0
        assert len(result.suggested_queries) == 1
        sq = result.suggested_queries[0]
        assert sq.platform == "devto"
        assert "site:dev.to" in sq.query
        assert sq.reason == "tag search returned empty"


# ---------------------------------------------------------------------------
# Engagement score mapping
# ---------------------------------------------------------------------------


def test_engagement_score_mapping():
    # Reddit: min(100, score * 2)
    reddit_data = {"data": {"children": [{"data": {
        "title": "T", "permalink": "/r/t/comments/x/t/", "score": 50,
        "num_comments": 0, "created_utc": 0, "author": "a", "id": "x",
        "subreddit": "t", "selftext": "",
    }}]}}
    r_hits = RedditProvider.parse_search_response(reddit_data, "brand_search")
    assert r_hits[0].engagement_score == 100  # 50 * 2 = 100

    reddit_data2 = {"data": {"children": [{"data": {
        "title": "T", "permalink": "/r/t/comments/y/t/", "score": 60,
        "num_comments": 0, "created_utc": 0, "author": "a", "id": "y",
        "subreddit": "t", "selftext": "",
    }}]}}
    r_hits2 = RedditProvider.parse_search_response(reddit_data2, "brand_search")
    assert r_hits2[0].engagement_score == 100  # capped at 100

    # HN: min(100, points * 1.5)
    hn_data = {"hits": [{"title": "T", "objectID": "1", "points": 67, "num_comments": 0,
                         "created_at": "", "author": "a"}]}
    h_hits = HackerNewsProvider.parse_search_response(hn_data, "brand_search")
    assert h_hits[0].engagement_score == 100  # floor(67 * 1.5) = 100

    hn_data2 = {"hits": [{"title": "T", "objectID": "2", "points": 10, "num_comments": 0,
                          "created_at": "", "author": "a"}]}
    h_hits2 = HackerNewsProvider.parse_search_response(hn_data2, "brand_search")
    assert h_hits2[0].engagement_score == 15  # floor(10 * 1.5) = 15

    # Dev.to: min(100, reactions * 3)
    devto_data = [{"title": "T", "url": "https://dev.to/t", "positive_reactions_count": 34,
                   "comments_count": 0, "published_at": "", "user": {"username": "a"}, "id": 1,
                   "description": ""}]
    d_hits = DevtoProvider.parse_search_response(devto_data, "brand_search")
    assert d_hits[0].engagement_score == 100  # 34 * 3 = 102 → capped 100


# ---------------------------------------------------------------------------
# Mock HTTP error paths
# ---------------------------------------------------------------------------


async def _mock_http_timeout(url, params=None, headers=None):
    return HttpResult(data=None, error="timeout", status_code=None)


async def _mock_http_429(url, params=None, headers=None):
    return HttpResult(data=None, error="rate_limited", status_code=429)


async def _mock_http_empty(url, params=None, headers=None):
    # Reddit returns empty children, HN returns empty hits
    if "reddit" in url:
        return HttpResult(data={"data": {"children": []}}, error=None, status_code=200)
    if "algolia" in url:
        return HttpResult(data={"hits": []}, error=None, status_code=200)
    return HttpResult(data=[], error=None, status_code=200)


async def _mock_http_missing_fields(url, params=None, headers=None):
    if "reddit" in url:
        return HttpResult(data={"data": {"children": [
            {"data": {"title": "Partial", "id": "p1"}},  # missing many fields
        ]}}, error=None, status_code=200)
    if "algolia" in url:
        return HttpResult(data={"hits": [
            {"title": "Partial HN", "objectID": "h1"},  # missing points, etc.
        ]}, error=None, status_code=200)
    return HttpResult(data=[], error=None, status_code=200)


def test_provider_timeout():
    with patch("opencmo.tools.community_providers._http_get_json", side_effect=_mock_http_timeout):
        provider = RedditProvider()
        result = asyncio.run(provider.search("brand", "cat"))
        assert len(result.hits) == 0
        assert len(result.errors) == 2  # brand + category both timed out


def test_provider_429():
    with patch("opencmo.tools.community_providers._http_get_json", side_effect=_mock_http_429):
        provider = RedditProvider()
        result = asyncio.run(provider.search("brand", "cat"))
        assert len(result.hits) == 0
        assert any("rate_limited" in e for e in result.errors)


def test_provider_empty_result():
    async def _run():
        with patch("opencmo.tools.community_providers._http_get_json", side_effect=_mock_http_empty):
            provider = RedditProvider()
            r1 = await provider.search("brand", "cat")
            hn_provider = HackerNewsProvider()
            r2 = await hn_provider.search("brand", "cat")
            return r1, r2

    r1, r2 = asyncio.run(_run())
    assert r1.hits == []
    assert r2.hits == []


def test_provider_missing_fields():
    async def _run():
        with patch("opencmo.tools.community_providers._http_get_json", side_effect=_mock_http_missing_fields):
            provider = RedditProvider()
            r1 = await provider.search("brand", "cat")
            hn_provider = HackerNewsProvider()
            r2 = await hn_provider.search("brand", "cat")
            return r1, r2

    r1, r2 = asyncio.run(_run())
    assert len(r1.hits) >= 1
    h = r1.hits[0]
    assert h.title == "Partial"
    assert h.raw_score == 0
    assert h.author == ""
    assert len(r2.hits) >= 1
    hh = r2.hits[0]
    assert hh.title == "Partial HN"
    assert hh.raw_score == 0


# ---------------------------------------------------------------------------
# scan_community partial failure
# ---------------------------------------------------------------------------


async def _mock_http_partial(url, params=None, headers=None):
    """Reddit fails, HN succeeds, Dev.to succeeds empty."""
    if "reddit" in url:
        return HttpResult(data=None, error="rate_limited", status_code=429)
    if "algolia" in url:
        return HttpResult(data={"hits": [
            {"title": "HN Post", "objectID": "999", "points": 42, "num_comments": 10,
             "created_at": "", "author": "hn_author"},
        ]}, error=None, status_code=200)
    if "dev.to" in url:
        return HttpResult(data=[], error=None, status_code=200)
    return HttpResult(data=None, error="timeout", status_code=None)


def test_scan_partial_failure():
    """Reddit fails + HN succeeds → envelope has HN hits + Reddit error."""
    import json

    from opencmo.tools.community import _scan_community_impl

    with patch("opencmo.tools.community_providers._http_get_json", side_effect=_mock_http_partial):
        raw = asyncio.run(_scan_community_impl("TestBrand", "testing"))
        envelope = json.loads(raw)

    assert "hits" in envelope
    assert "provider_errors" in envelope
    assert "disabled_providers" in envelope
    assert "suggested_queries" in envelope

    # HN hits should be present
    hn_hits = [h for h in envelope["hits"] if h["platform"] == "hackernews"]
    assert len(hn_hits) >= 1

    # Reddit errors should be recorded
    reddit_errors = [e for e in envelope["provider_errors"] if e["provider"] == "reddit"]
    assert len(reddit_errors) >= 1

    # Stub providers should be in disabled_providers
    disabled_names = {d["name"] for d in envelope["disabled_providers"]}
    assert "twitter" in disabled_names
    assert "linkedin" in disabled_names

"""Tests for community_providers — structure, parsing, and error handling."""

from __future__ import annotations

import asyncio
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from opencmo.tools.community_providers import (
    PROVIDER_REGISTRY,
    BilibiliProvider,
    BlogSearchProvider,
    BlueskyProvider,
    DevtoProvider,
    DiscussionHit,
    DouyinProvider,
    HackerNewsProvider,
    HttpResult,
    ProviderSearchResult,
    RedditProvider,
    TwitterProvider,
    V2EXProvider,
    WeChatProvider,
    WeiboProvider,
    XiaoHongShuProvider,
    XueQiuProvider,
    YouTubeProvider,
)
from opencmo.tools.community_scoring import (
    compute_composite_score,
    convergence_boost,
    detect_convergence_clusters,
    recency_score,
    rescore_hits,
    text_relevance,
    trigram_jaccard,
    velocity_score,
)

# ---------------------------------------------------------------------------
# Force "light" profile for tests (fast, predictable)
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _use_light_profile(monkeypatch):
    monkeypatch.setenv("OPENCMO_SCRAPE_DEPTH", "light")


# ---------------------------------------------------------------------------
# Provider structure tests
# ---------------------------------------------------------------------------


def test_provider_registry_has_all_platforms():
    names = {p.name for p in PROVIDER_REGISTRY}
    assert names == {
        "reddit", "hackernews", "devto", "youtube", "bluesky", "twitter",
        "linkedin", "producthunt", "blog",
        "v2ex", "weibo", "bilibili", "xueqiu",
        "xiaohongshu", "wechat", "douyin",
    }


def test_free_providers_enabled_by_default():
    for p in PROVIDER_REGISTRY:
        if p.name in ("reddit", "hackernews", "devto", "bluesky"):
            assert p.is_enabled, f"{p.name} should be enabled"


def test_chinese_free_providers_enabled_by_default():
    for p in PROVIDER_REGISTRY:
        if p.name in ("v2ex", "weibo", "bilibili"):
            assert p.is_enabled, f"{p.name} should be enabled (no auth required)"


def test_stub_providers_disabled():
    for p in PROVIDER_REGISTRY:
        if p.name in ("linkedin", "producthunt", "blog"):
            assert not p.is_enabled, f"{p.name} should be disabled (stub)"
            assert p.status == "stub"


def test_chinese_stub_providers_disabled():
    for p in PROVIDER_REGISTRY:
        if p.name in ("xiaohongshu", "wechat", "douyin"):
            assert not p.is_enabled, f"{p.name} should be disabled (stub)"
            assert p.status == "stub"


def test_xueqiu_disabled_without_cookie():
    provider = XueQiuProvider()
    assert not provider.is_enabled


def test_twitter_disabled_without_keys():
    """Twitter should be disabled when neither TWITTER_BEARER_TOKEN nor TAVILY_API_KEY is set."""
    provider = TwitterProvider()
    assert not provider.is_enabled


def test_youtube_disabled_without_keys():
    """YouTube should be disabled without YOUTUBE_API_KEY or TAVILY_API_KEY."""
    provider = YouTubeProvider()
    assert not provider.is_enabled


def test_blog_provider_no_auth_but_stub():
    blog = BlogSearchProvider()
    assert blog.requires_auth is False
    assert blog.status == "stub"
    assert not blog.is_enabled


# ---------------------------------------------------------------------------
# Reddit parse tests
# ---------------------------------------------------------------------------


def _make_reddit_search_json(count: int = 2, after: str | None = None) -> dict:
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
    return {"data": {"children": children, "after": after}}


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


def test_reddit_after_token_extraction():
    data = _make_reddit_search_json(2, after="t3_xyz")
    assert RedditProvider._get_after_token(data) == "t3_xyz"

    data_no_after = _make_reddit_search_json(2, after=None)
    assert RedditProvider._get_after_token(data_no_after) is None


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
# Bluesky parse tests
# ---------------------------------------------------------------------------


def _make_bluesky_search_json(count: int = 2) -> dict:
    posts = []
    for i in range(count):
        posts.append({
            "uri": f"at://did:plc:abc{i}/app.bsky.feed.post/rkey{i}",
            "author": {"handle": f"user{i}.bsky.social", "did": f"did:plc:abc{i}"},
            "record": {
                "text": f"Post about topic {i}\nMore details here",
                "createdAt": "2025-01-01T00:00:00.000Z",
            },
            "likeCount": 10 + i,
            "repostCount": 5 + i,
            "replyCount": 3 + i,
        })
    return {"posts": posts}


def test_bluesky_provider_parse_search():
    data = _make_bluesky_search_json(2)
    hits = BlueskyProvider.parse_search_response(data, "brand_search")
    assert len(hits) == 2
    h = hits[0]
    assert h.platform == "bluesky"
    assert h.title == "Post about topic 0"  # first line only
    assert h.author == "user0.bsky.social"
    assert h.detail_id == "at://did:plc:abc0/app.bsky.feed.post/rkey0"
    assert h.extra_param_1 == "user0.bsky.social"
    assert h.extra_param_2 == "did:plc:abc0"
    assert h.raw_score == 10 + 5 + 3  # likes + reposts + replies
    assert "bsky.app/profile/user0.bsky.social/post/rkey0" in h.url


def test_bluesky_provider_parse_thread():
    thread_data = {
        "thread": {
            "post": {
                "record": {"text": "Main post content", "createdAt": "2025-01-01T00:00:00Z"},
                "author": {"handle": "op.bsky.social"},
                "likeCount": 20,
            },
            "replies": [
                {
                    "post": {
                        "record": {"text": "Great post!"},
                        "author": {"handle": "replier.bsky.social"},
                        "likeCount": 5,
                    },
                },
                {
                    "post": {
                        "record": {"text": ""},  # empty → skipped
                        "author": {"handle": "empty.bsky.social"},
                        "likeCount": 0,
                    },
                },
            ],
        }
    }
    hit = DiscussionHit(
        platform="bluesky", title="Main post content",
        url="https://bsky.app/profile/op.bsky.social/post/rkey1",
        engagement_score=20, raw_score=20, comments_count=2, age_days=1,
        author="op.bsky.social", detail_id="at://did:plc:op/app.bsky.feed.post/rkey1",
        extra_param_1="op.bsky.social", extra_param_2="did:plc:op",
        preview="", source="brand_search",
    )
    detail = BlueskyProvider.parse_thread_response(thread_data, hit)
    assert detail is not None
    assert detail.full_content == "Main post content"
    assert len(detail.comments) == 1  # empty reply skipped
    assert detail.comments[0]["author"] == "replier.bsky.social"


def test_bluesky_provider_search_mock():
    async def _mock_bsky(url, params=None, headers=None):
        if "searchPosts" in url:
            return HttpResult(data=_make_bluesky_search_json(3), error=None, status_code=200)
        return HttpResult(data=None, error="not_found", status_code=404)

    with patch("opencmo.tools.community_providers._http_get_json", side_effect=_mock_bsky):
        provider = BlueskyProvider()
        result = asyncio.run(provider.search("TestBrand", "devtools"))
        # 3 posts from brand_search + 3 from category_search = 6 total
        # But different URIs so all unique
        assert len(result.hits) == 3  # same data returned for both queries, deduped by URI
        assert all(h.platform == "bluesky" for h in result.hits)


# ---------------------------------------------------------------------------
# YouTube parse tests
# ---------------------------------------------------------------------------


def test_youtube_parse_search_and_stats():
    search_items = [
        {
            "id": {"videoId": "vid1"},
            "snippet": {
                "title": "AI Review Tools Tutorial",
                "publishedAt": "2025-01-01T00:00:00Z",
                "channelTitle": "TechChannel",
                "channelId": "UCabc",
                "description": "A deep dive into AI code review.",
            },
        },
    ]
    stats_map = {
        "vid1": {"viewCount": "5000", "likeCount": "100", "commentCount": "20"},
    }
    hits = YouTubeProvider.parse_search_and_stats(search_items, stats_map, "brand_search")
    assert len(hits) == 1
    h = hits[0]
    assert h.platform == "youtube"
    assert h.detail_id == "vid1"
    assert h.raw_score == 120  # 100 + 20
    assert h.comments_count == 20
    assert h.author == "TechChannel"
    assert "youtube.com/watch?v=vid1" in h.url


def test_youtube_parse_comments():
    data = {
        "items": [
            {
                "snippet": {
                    "topLevelComment": {
                        "snippet": {
                            "textDisplay": "Great tutorial!",
                            "authorDisplayName": "Viewer1",
                            "likeCount": 5,
                        }
                    }
                }
            },
            {
                "snippet": {
                    "topLevelComment": {
                        "snippet": {
                            "textDisplay": "",  # empty → skipped
                            "authorDisplayName": "Empty",
                            "likeCount": 0,
                        }
                    }
                }
            },
        ]
    }
    comments = YouTubeProvider.parse_comments_response(data)
    assert len(comments) == 1
    assert comments[0]["author"] == "Viewer1"
    assert comments[0]["score"] == 5


def test_youtube_tavily_parse():
    results = [
        {
            "url": "https://www.youtube.com/watch?v=abc123",
            "title": "Best AI Tools 2025",
            "content": "A review of the best AI tools...",
            "score": 0.75,
        },
    ]
    hits = YouTubeProvider.parse_tavily_results(results, "brand_search")
    assert len(hits) == 1
    assert hits[0].detail_id == "abc123"
    assert hits[0].platform == "youtube"
    assert hits[0].source_kind == "external_search"
    assert hits[0].engagement_score is None


# ---------------------------------------------------------------------------
# Twitter parse tests
# ---------------------------------------------------------------------------


def test_twitter_tavily_parse():
    results = [
        {
            "url": "https://x.com/johndoe/status/123456789",
            "title": "AI code review is changing everything",
            "content": "AI code review is changing everything. Here's my take on the latest tools...",
            "score": 0.85,
        },
        {
            "url": "https://twitter.com/janedoe/status/987654321",
            "title": "",
            "content": "",  # empty → should be skipped
            "score": 0.1,
        },
    ]
    hits = TwitterProvider.parse_tavily_results(results, "brand_search")
    assert len(hits) == 1
    h = hits[0]
    assert h.platform == "twitter"
    assert h.author == "johndoe"
    assert h.detail_id == "123456789"
    assert "x.com/johndoe/status/123456789" in h.url
    assert h.source_kind == "external_search"
    assert h.engagement_score is None


def test_twitter_provider_tavily_search_mock(monkeypatch):
    """Twitter provider should use Tavily fallback when only TAVILY_API_KEY is set."""
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    mock_tavily_client = AsyncMock()
    mock_tavily_client.search = AsyncMock(return_value={
        "results": [
            {
                "url": "https://x.com/testuser/status/111",
                "title": "Testing Twitter search",
                "content": "Some tweet content about our brand",
                "score": 0.9,
            },
        ],
    })

    import tavily as tavily_mod
    with patch("opencmo.tools.community_providers.TwitterProvider._has_bearer_token", return_value=False):
        with patch.object(tavily_mod, "AsyncTavilyClient", return_value=mock_tavily_client):
            provider = TwitterProvider()
            assert provider.is_enabled
            result = asyncio.run(provider.search("TestBrand", "devtools"))
            assert len(result.hits) >= 1
            assert result.hits[0].platform == "twitter"


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
        return HttpResult(data={"data": {"children": [], "after": None}}, error=None, status_code=200)
    if "algolia" in url:
        return HttpResult(data={"hits": []}, error=None, status_code=200)
    return HttpResult(data=[], error=None, status_code=200)


async def _mock_http_missing_fields(url, params=None, headers=None):
    if "reddit" in url:
        return HttpResult(data={"data": {"children": [
            {"data": {"title": "Partial", "id": "p1"}},  # missing many fields
        ], "after": None}}, error=None, status_code=200)
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
        assert len(result.errors) >= 2  # brand + category both timed out


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
# Reddit pagination test
# ---------------------------------------------------------------------------


def test_reddit_pagination():
    """Verify multi-page fetching and deduplication."""
    call_count = 0

    async def _mock_paginated(url, params=None, headers=None):
        nonlocal call_count
        call_count += 1
        if "reddit.com/search" in url:
            after = params.get("after") if params else None
            if after is None:
                return HttpResult(
                    data=_make_reddit_search_json(2, after="page2_token"),
                    error=None, status_code=200,
                )
            elif after == "page2_token":
                return HttpResult(
                    data=_make_reddit_search_json(2, after=None),
                    error=None, status_code=200,
                )
        return HttpResult(data={"data": {"children": [], "after": None}}, error=None, status_code=200)

    async def _run():
        with patch("opencmo.tools.community_providers._http_get_json", side_effect=_mock_paginated):
            provider = RedditProvider()
            result = await provider.search("brand", "cat")
            return result

    result = asyncio.run(_run())
    # Should have hits from brand search (2 unique ids) + category search
    assert len(result.hits) >= 2
    assert len(result.errors) == 0


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

    # Stub/disabled providers should be in disabled_providers
    disabled_names = {d["name"] for d in envelope["disabled_providers"]}
    assert "linkedin" in disabled_names


# ---------------------------------------------------------------------------
# Scrape config test
# ---------------------------------------------------------------------------


def test_scrape_profiles():
    from opencmo.scrape_config import DEEP, LIGHT, get_scrape_profile

    # Default is "deep" but we set "light" in fixture
    profile = get_scrape_profile()
    assert profile == LIGHT

    # Check deep profile has much higher limits
    assert DEEP.reddit_brand_pages > LIGHT.reddit_brand_pages
    assert DEEP.hn_brand_pages > LIGHT.hn_brand_pages
    assert DEEP.output_budget_chars > LIGHT.output_budget_chars
    assert DEEP.serp_num_results > LIGHT.serp_num_results


def test_scrape_profile_env_override(monkeypatch):
    from opencmo.scrape_config import DEEP, get_scrape_profile

    monkeypatch.setenv("OPENCMO_SCRAPE_DEPTH", "deep")
    profile = get_scrape_profile()
    assert profile == DEEP


# ---------------------------------------------------------------------------
# Multi-signal scoring tests
# ---------------------------------------------------------------------------


def _make_hit(
    platform: str = "reddit",
    title: str = "Test Post",
    raw_score: int = 50,
    comments_count: int = 10,
    age_days: int = 5,
    detail_id: str = "x1",
    preview: str = "",
) -> DiscussionHit:
    return DiscussionHit(
        platform=platform, title=title, url=f"https://{platform}.com/{detail_id}",
        engagement_score=0, raw_score=raw_score, comments_count=comments_count,
        age_days=age_days, author="user", detail_id=detail_id,
        extra_param_1="", extra_param_2="", preview=preview, source="test",
    )


def test_velocity_score_fresh_post():
    # A fresh post (1 day) with high engagement should score high
    score = velocity_score(100, 50, 1)
    assert score > 60


def test_velocity_score_old_post():
    # Same engagement but very old should score lower
    fresh = velocity_score(100, 50, 1)
    old = velocity_score(100, 50, 365)
    assert fresh > old


def test_recency_score_today():
    score = recency_score(0)
    assert score >= 99.0  # basically 100


def test_recency_score_halflife():
    # At the halflife, score should be ~50
    score = recency_score(23, halflife_days=23.0)
    assert 45 <= score <= 55


def test_recency_score_very_old():
    score = recency_score(365)
    assert score < 1.0


def test_text_relevance_exact_match():
    score = text_relevance("AI code review", "AI code review tools")
    assert score > 0.5


def test_text_relevance_no_match():
    score = text_relevance("blockchain mining", "recipe for chocolate cake")
    assert score < 0.1


def test_text_relevance_synonym_expansion():
    # "seo" should match "search engine optimization" via synonyms
    score_with = text_relevance("seo tools", "best search engine optimization tools")
    score_without = text_relevance("seo tools", "best unrelated topic here")
    assert score_with > score_without


def test_trigram_jaccard_identical():
    sim = trigram_jaccard("hello world", "hello world")
    assert sim == 1.0


def test_trigram_jaccard_different():
    sim = trigram_jaccard("hello world", "completely different text")
    assert sim < 0.3


def test_trigram_jaccard_similar():
    sim = trigram_jaccard("AI code review tool launches", "AI code review tool launch")
    assert sim > 0.7


def test_convergence_clusters_cross_platform():
    hits = [
        _make_hit(platform="reddit", title="AI code review tool launches today", detail_id="r1"),
        _make_hit(platform="hackernews", title="AI code review tool launch", detail_id="h1"),
        _make_hit(platform="devto", title="Something completely different", detail_id="d1"),
    ]
    clusters = detect_convergence_clusters(hits, threshold=0.5)
    # Reddit and HN should be in the same cluster
    assert clusters[0] == clusters[1]
    # Dev.to should be in a different cluster
    assert clusters[2] != clusters[0]


def test_convergence_clusters_same_platform_not_clustered():
    hits = [
        _make_hit(platform="reddit", title="AI code review", detail_id="r1"),
        _make_hit(platform="reddit", title="AI code review tool", detail_id="r2"),
    ]
    clusters = detect_convergence_clusters(hits, threshold=0.5)
    # Same platform hits should NOT be clustered together even if similar
    assert clusters[0] != clusters[1]


def test_convergence_boost_multi_platform():
    clusters = {0: 0, 1: 0, 2: 1}  # hits 0 and 1 in cluster 0
    assert convergence_boost(clusters, 0) == 10.0  # 2-hit cluster: 10 * (2-1)
    assert convergence_boost(clusters, 2) == 0.0   # single-hit cluster


def test_composite_score_in_range():
    hit = _make_hit(raw_score=50, comments_count=10, age_days=5)
    score = compute_composite_score(hit, "test query")
    assert 0 <= score <= 100


def test_rescore_hits_mutates_engagement_score():
    hits = [
        _make_hit(platform="reddit", title="AI tools review", raw_score=50, age_days=2, detail_id="r1"),
        _make_hit(platform="hackernews", title="AI tools review launch", raw_score=100, age_days=1, detail_id="h1"),
    ]
    rescore_hits(hits, "AI tools")
    # Scores should be set to something reasonable (not 0)
    assert all(h.engagement_score > 0 for h in hits)
    # HN hit with higher raw_score and fresher age should score higher
    assert hits[1].engagement_score >= hits[0].engagement_score


def test_rescore_hits_empty_list():
    result = rescore_hits([], "anything")
    assert result == []


# ---------------------------------------------------------------------------
# V2EX parse tests
# ---------------------------------------------------------------------------


def _make_v2ex_topics_json(count: int = 2) -> list:
    return [
        {
            "id": 1000 + i,
            "title": f"V2EX Topic {i}",
            "content_rendered": f"<p>Body text for topic {i}</p>",
            "replies": 5 + i,
            "created": 1700000000 + i * 86400,
            "member": {"username": f"v2user{i}"},
            "node": {"name": "python"},
        }
        for i in range(count)
    ]


def test_v2ex_provider_parse_search():
    data = _make_v2ex_topics_json(3)
    hits = V2EXProvider.parse_topics_response(data, "hot_topics")
    assert len(hits) == 3
    h = hits[0]
    assert h.platform == "v2ex"
    assert h.title == "V2EX Topic 0"
    assert h.detail_id == "1000"
    assert h.extra_param_1 == "python"
    assert h.source == "hot_topics"
    assert h.raw_score == 5
    assert h.comments_count == 5
    assert "Body text for topic 0" in h.preview  # HTML stripped


def test_v2ex_provider_parse_replies():
    replies_data = [
        {"member": {"username": "replier1"}, "content_rendered": "<b>Nice!</b>", "created": 1700000000},
        {"member": {"username": "replier2"}, "content_rendered": "Thanks", "created": 1700000100},
    ]
    hit = DiscussionHit(
        platform="v2ex", title="Test", url="https://www.v2ex.com/t/1000",
        engagement_score=0, raw_score=2, comments_count=2, age_days=1,
        author="op", detail_id="1000", extra_param_1="python", extra_param_2="",
        preview="", source="test",
    )
    detail = V2EXProvider.parse_replies_response(replies_data, hit)
    assert detail.platform == "v2ex"
    assert len(detail.comments) == 2
    assert detail.comments[0]["author"] == "replier1"
    assert detail.comments[0]["body"] == "Nice!"  # HTML stripped


def test_v2ex_search_mock():
    """V2EX search filters hot topics by brand/category keywords."""

    async def _mock_v2ex(url, params=None, headers=None):
        if "hot.json" in url:
            return HttpResult(
                data=[
                    {"id": 1, "title": "TestBrand is great", "content_rendered": "Using TestBrand",
                     "replies": 10, "created": 1700000000, "member": {"username": "u1"}, "node": {"name": "python"}},
                    {"id": 2, "title": "Unrelated topic", "content_rendered": "Something else",
                     "replies": 5, "created": 1700000000, "member": {"username": "u2"}, "node": {"name": "python"}},
                ],
                error=None, status_code=200,
            )
        if "show.json" in url:
            return HttpResult(data=[], error=None, status_code=200)
        return HttpResult(data=[], error=None, status_code=200)

    with patch("opencmo.tools.community_providers._http_get_json", side_effect=_mock_v2ex):
        provider = V2EXProvider()
        result = asyncio.run(provider.search("TestBrand", "devtools"))
        # Only the hit containing "TestBrand" should match
        assert len(result.hits) >= 1
        assert result.hits[0].title == "TestBrand is great"
        # Should always have suggested queries (V2EX has no search API)
        assert len(result.suggested_queries) >= 1
        assert "site:v2ex.com" in result.suggested_queries[0].query


# ---------------------------------------------------------------------------
# Weibo parse tests
# ---------------------------------------------------------------------------


def _make_weibo_cards(count: int = 2) -> list:
    return [
        {
            "mblog": {
                "mid": str(5000 + i),
                "id": str(5000 + i),
                "text": f"<a>微博内容 {i}</a> some text",
                "reposts_count": 3 + i,
                "comments_count": 10 + i,
                "attitudes_count": 20 + i,
                "created_at": "Mon Jan 15 12:00:00 +0800 2024",
                "user": {"screen_name": f"weibo_user{i}"},
            }
        }
        for i in range(count)
    ]


def test_weibo_provider_parse_search():
    cards = _make_weibo_cards(3)
    hits = WeiboProvider.parse_search_cards(cards, "brand")
    assert len(hits) == 3
    h = hits[0]
    assert h.platform == "weibo"
    assert h.detail_id == "5000"
    assert h.author == "weibo_user0"
    assert h.comments_count == 10
    assert h.raw_score == 3 + 10 + 20  # reposts + comments + attitudes
    assert "<a>" not in h.preview  # HTML stripped


def test_weibo_provider_parse_comments():
    comments_data = [
        {"user": {"screen_name": "c1"}, "text": "<b>好评</b>", "created_at": "Mon Jan 15 13:00:00 +0800 2024"},
        {"user": {"screen_name": "c2"}, "text": "不错", "created_at": "Mon Jan 15 14:00:00 +0800 2024"},
    ]
    hit = DiscussionHit(
        platform="weibo", title="Test", url="https://m.weibo.cn/detail/5000",
        engagement_score=0, raw_score=30, comments_count=2, age_days=1,
        author="op", detail_id="5000", extra_param_1="", extra_param_2="",
        preview="", source="test",
    )
    detail = WeiboProvider.parse_comments_response(comments_data, hit)
    assert len(detail.comments) == 2
    assert detail.comments[0]["body"] == "好评"  # HTML stripped


# ---------------------------------------------------------------------------
# Bilibili parse tests
# ---------------------------------------------------------------------------


def _make_bilibili_search_json(count: int = 2) -> dict:
    videos = [
        {
            "title": f"<em class=\"keyword\">Bilibili</em> Video {i}",
            "bvid": f"BV1abc{i}",
            "aid": 10000 + i,
            "play": 1000 + i * 100,
            "review": 50 + i,
            "like": 200 + i,
            "danmaku": 30 + i,
            "pubdate": 1700000000 + i * 86400,
            "author": f"bili_up{i}",
            "description": f"Video description {i}",
        }
        for i in range(count)
    ]
    return {"data": {"result": [{"result_type": "video", "data": videos}]}}


def test_bilibili_provider_parse_search():
    data = _make_bilibili_search_json(3)
    hits = BilibiliProvider.parse_search_response(data, "brand")
    assert len(hits) == 3
    h = hits[0]
    assert h.platform == "bilibili"
    assert h.title == "Bilibili Video 0"  # <em> tags stripped
    assert h.detail_id == "BV1abc0"
    assert h.extra_param_1 == "10000"  # aid stored for comments
    assert h.author == "bili_up0"
    assert h.raw_score == 1000 + 200  # play + like
    assert h.comments_count == 50


def test_bilibili_provider_parse_comments():
    data = {
        "data": {
            "replies": [
                {"member": {"uname": "viewer1"}, "content": {"message": "很棒！"}, "like": 10},
                {"member": {"uname": "viewer2"}, "content": {"message": "感谢分享"}, "like": 5},
            ]
        }
    }
    hit = DiscussionHit(
        platform="bilibili", title="Test Video", url="https://www.bilibili.com/video/BV1abc0",
        engagement_score=0, raw_score=1000, comments_count=50, age_days=1,
        author="up", detail_id="BV1abc0", extra_param_1="10000", extra_param_2="",
        preview="", source="test",
    )
    detail = BilibiliProvider.parse_comments_response(data, hit)
    assert len(detail.comments) == 2
    assert detail.comments[0]["author"] == "viewer1"
    assert detail.comments[0]["body"] == "很棒！"


# ---------------------------------------------------------------------------
# XueQiu parse tests
# ---------------------------------------------------------------------------


def _make_xueqiu_search_json(count: int = 2) -> dict:
    return {
        "list": [
            {
                "id": 200000 + i,
                "title": f"XueQiu Post {i}",
                "text": f"<p>Stock discussion {i}</p>",
                "reply_count": 8 + i,
                "retweet_count": 3 + i,
                "like_count": 15 + i,
                "created_at": 1700000000000 + i * 86400000,  # milliseconds
                "user": {"id": 9000 + i, "screen_name": f"investor{i}"},
            }
            for i in range(count)
        ]
    }


def test_xueqiu_provider_parse_search():
    data = _make_xueqiu_search_json(3)
    hits = XueQiuProvider.parse_search_response(data, "brand")
    assert len(hits) == 3
    h = hits[0]
    assert h.platform == "xueqiu"
    assert h.title == "XueQiu Post 0"
    assert h.detail_id == "200000"
    assert h.author == "investor0"
    assert h.comments_count == 8
    assert h.raw_score == 8 + 3 + 15  # reply + retweet + like
    assert "<p>" not in h.preview  # HTML stripped


# ---------------------------------------------------------------------------
# Stub providers tests — suggested queries
# ---------------------------------------------------------------------------


def test_xiaohongshu_stub_returns_suggested_queries():
    provider = XiaoHongShuProvider()
    result = asyncio.run(provider.search("TestBrand", "devtools"))
    assert len(result.hits) == 0
    assert len(result.suggested_queries) >= 1
    assert result.suggested_queries[0].platform == "xiaohongshu"
    assert "site:xiaohongshu.com" in result.suggested_queries[0].query


def test_wechat_stub_returns_suggested_queries():
    provider = WeChatProvider()
    result = asyncio.run(provider.search("TestBrand", "devtools"))
    assert len(result.hits) == 0
    assert len(result.suggested_queries) >= 1
    assert result.suggested_queries[0].platform == "wechat"
    assert "site:mp.weixin.qq.com" in result.suggested_queries[0].query


def test_douyin_stub_returns_suggested_queries():
    provider = DouyinProvider()
    result = asyncio.run(provider.search("TestBrand", "devtools"))
    assert len(result.hits) == 0
    assert len(result.suggested_queries) >= 1
    assert result.suggested_queries[0].platform == "douyin"
    assert "site:douyin.com" in result.suggested_queries[0].query


def test_build_query_plan_uses_keywords_competitors_and_domains():
    from opencmo.tools.community_query_planner import build_query_plan

    plan = build_query_plan(
        brand_name="OpenCMO",
        category="ai marketing",
        tracked_keywords=["ai cmo", "open source marketing agent"],
        competitor_names=["HubSpot"],
        competitor_keywords=["marketing automation"],
        canonical_url="https://opencmo.dev",
        locale="en",
    )

    reddit_queries = plan.provider_queries["reddit"]
    query_texts = {q.query for q in reddit_queries}
    intent_types = {q.intent_type for q in reddit_queries}

    assert '"OpenCMO"' in query_texts
    assert any("opencmo.dev" in query for query in query_texts)
    assert any("ai cmo" in query.lower() for query in query_texts)
    assert any("HubSpot" in query for query in query_texts)
    assert "direct_mention" in intent_types
    assert "opportunity" in intent_types


def test_scan_community_sorts_direct_mentions_before_platform_groups():
    import json

    from opencmo.tools.community import _scan_community_impl
    from opencmo.tools.community_providers import CommunityProvider

    class _OpportunityProvider(CommunityProvider):
        name = "reddit"
        status = "enabled"
        requires_auth = False
        auth_env_vars = []
        capabilities = {"search"}
        max_search_calls = 1
        recommended_max_details = 0

        async def search(self, brand_name: str, category: str, query_plan=None):
            return ProviderSearchResult(
                hits=[
                    DiscussionHit(
                        platform="reddit",
                        title="Best AI marketing tools for indie hackers",
                        url="https://reddit.test/1",
                        engagement_score=99,
                        raw_score=90,
                        comments_count=30,
                        age_days=1,
                        author="user1",
                        detail_id="rd1",
                        extra_param_1="saas",
                        extra_param_2="",
                        preview="Looking for alternatives and recommendations",
                        source="opportunity_search",
                        intent_type="opportunity",
                        match_reason="Matched a problem-first opportunity query.",
                        matched_query="best ai marketing tools",
                        matched_terms=["ai marketing"],
                        confidence=0.55,
                        source_kind="post",
                    )
                ]
            )

    class _DirectMentionProvider(CommunityProvider):
        name = "hackernews"
        status = "enabled"
        requires_auth = False
        auth_env_vars = []
        capabilities = {"search"}
        max_search_calls = 1
        recommended_max_details = 0

        async def search(self, brand_name: str, category: str, query_plan=None):
            return ProviderSearchResult(
                hits=[
                    DiscussionHit(
                        platform="hackernews",
                        title="OpenCMO launched today",
                        url="https://hn.test/1",
                        engagement_score=40,
                        raw_score=12,
                        comments_count=8,
                        age_days=2,
                        author="founder",
                        detail_id="hn1",
                        extra_param_1="",
                        extra_param_2="",
                        preview="OpenCMO helps founders monitor SEO, GEO and community signals",
                        source="brand_search",
                        intent_type="direct_mention",
                        match_reason="Matched the exact brand name in the title.",
                        matched_query='"OpenCMO"',
                        matched_terms=["OpenCMO"],
                        confidence=0.94,
                        source_kind="post",
                    )
                ]
            )

    with patch(
        "opencmo.tools.community.PROVIDER_REGISTRY",
        [_OpportunityProvider(), _DirectMentionProvider()],
    ):
        raw = asyncio.run(_scan_community_impl("OpenCMO", "ai marketing"))

    envelope = json.loads(raw)
    assert envelope["hits"][0]["platform"] == "hackernews"
    assert envelope["hits"][0]["intent_type"] == "direct_mention"
    assert envelope["hits"][1]["platform"] == "reddit"


def test_scan_community_uses_external_fallback_for_stub_platforms(monkeypatch):
    import json

    from opencmo.tools.community import _scan_community_impl

    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    mock_tavily_client = AsyncMock()
    mock_tavily_client.search = AsyncMock(return_value={
        "results": [
            {
                "url": "https://www.xiaohongshu.com/explore/abc123",
                "title": "OpenCMO 使用体验",
                "content": "这是一个关于 OpenCMO 的测评笔记。",
                "score": 0.88,
            }
        ]
    })

    with patch.dict(
        sys.modules,
        {"tavily": SimpleNamespace(AsyncTavilyClient=lambda api_key: mock_tavily_client)},
    ):
        with patch("opencmo.tools.community.PROVIDER_REGISTRY", [XiaoHongShuProvider()]):
            raw = asyncio.run(_scan_community_impl("OpenCMO", "marketing", locale="zh"))

    envelope = json.loads(raw)
    assert envelope["hits"]
    assert envelope["hits"][0]["platform"] == "xiaohongshu"
    assert envelope["hits"][0]["source_kind"] == "external_search"
    assert envelope["hits"][0]["intent_type"] in {"direct_mention", "opportunity"}

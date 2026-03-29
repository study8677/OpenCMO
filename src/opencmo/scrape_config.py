"""Scrape depth configuration — controls how many results each provider fetches."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ScrapeProfile:
    """Per-platform scrape parameters."""

    # Reddit
    reddit_brand_pages: int
    reddit_brand_per_page: int
    reddit_category_pages: int
    reddit_category_per_page: int
    reddit_extra_queries: int          # additional combo queries (brand+category, "brand review", etc.)
    reddit_extra_per_page: int
    reddit_comments_per_post: int
    reddit_time_filter: str            # "year" | "all"
    reddit_subreddit_search: bool      # search relevant subreddits

    # Hacker News
    hn_brand_pages: int
    hn_brand_per_page: int
    hn_category_pages: int
    hn_category_per_page: int
    hn_include_date_sort: bool         # also search by date (not just relevance)
    hn_comments_per_post: int

    # Dev.to
    devto_brand_pages: int
    devto_brand_per_page: int
    devto_category_pages: int
    devto_category_per_page: int
    devto_comments_per_post: int
    devto_multi_tag: bool              # try all category words as tags

    # YouTube
    youtube_max_results: int           # max results per search query
    youtube_comments_per_post: int     # max comment threads per video in detail fetch

    # Twitter/X
    twitter_max_results: int           # max results per query (Bearer Token search)

    # Bluesky
    bluesky_max_results: int           # max results per query
    bluesky_comments_per_post: int     # max comments per post in detail fetch

    # V2EX
    v2ex_max_results: int              # max topics to fetch per node/hot query
    v2ex_comments_per_post: int        # max replies per topic in detail fetch

    # Weibo
    weibo_max_results: int             # max results per search query
    weibo_comments_per_post: int       # max comments per post in detail fetch

    # Bilibili
    bilibili_max_results: int          # max results per search query
    bilibili_comments_per_post: int    # max comments per video in detail fetch

    # XueQiu
    xueqiu_max_results: int            # max results per search query

    # GEO
    geo_query_templates: int           # number of query templates per provider
    geo_content_snippet_chars: int

    # SERP
    serp_num_results: int

    # Scoring
    scoring_recency_halflife_days: float  # recency decay half-life (default 23.0)
    scoring_convergence_threshold: float  # trigram Jaccard threshold for convergence clusters

    # General
    request_delay_seconds: float       # delay between requests to avoid rate limits
    http_timeout_seconds: int
    max_retries_on_429: int
    output_budget_chars: int           # JSON output budget for community scan


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------

LIGHT = ScrapeProfile(
    reddit_brand_pages=1, reddit_brand_per_page=15,
    reddit_category_pages=1, reddit_category_per_page=5,
    reddit_extra_queries=0, reddit_extra_per_page=0,
    reddit_comments_per_post=10, reddit_time_filter="year",
    reddit_subreddit_search=False,

    hn_brand_pages=1, hn_brand_per_page=10,
    hn_category_pages=1, hn_category_per_page=5,
    hn_include_date_sort=False, hn_comments_per_post=15,

    devto_brand_pages=1, devto_brand_per_page=10,
    devto_category_pages=1, devto_category_per_page=10,
    devto_comments_per_post=10, devto_multi_tag=False,

    youtube_max_results=5, youtube_comments_per_post=5,

    twitter_max_results=10,

    bluesky_max_results=10, bluesky_comments_per_post=5,

    v2ex_max_results=10, v2ex_comments_per_post=5,
    weibo_max_results=10, weibo_comments_per_post=5,
    bilibili_max_results=5, bilibili_comments_per_post=5,
    xueqiu_max_results=10,

    geo_query_templates=1, geo_content_snippet_chars=2000,

    serp_num_results=20,

    scoring_recency_halflife_days=23.0, scoring_convergence_threshold=0.5,

    request_delay_seconds=0.0, http_timeout_seconds=10,
    max_retries_on_429=1, output_budget_chars=8000,
)

NORMAL = ScrapeProfile(
    reddit_brand_pages=2, reddit_brand_per_page=25,
    reddit_category_pages=1, reddit_category_per_page=25,
    reddit_extra_queries=2, reddit_extra_per_page=25,
    reddit_comments_per_post=20, reddit_time_filter="all",
    reddit_subreddit_search=True,

    hn_brand_pages=2, hn_brand_per_page=50,
    hn_category_pages=1, hn_category_per_page=50,
    hn_include_date_sort=True, hn_comments_per_post=20,

    devto_brand_pages=2, devto_brand_per_page=30,
    devto_category_pages=1, devto_category_per_page=30,
    devto_comments_per_post=15, devto_multi_tag=True,

    youtube_max_results=15, youtube_comments_per_post=10,

    twitter_max_results=25,

    bluesky_max_results=25, bluesky_comments_per_post=10,

    v2ex_max_results=25, v2ex_comments_per_post=15,
    weibo_max_results=25, weibo_comments_per_post=10,
    bilibili_max_results=15, bilibili_comments_per_post=10,
    xueqiu_max_results=25,

    geo_query_templates=3, geo_content_snippet_chars=4000,

    serp_num_results=50,

    scoring_recency_halflife_days=23.0, scoring_convergence_threshold=0.5,

    request_delay_seconds=0.3, http_timeout_seconds=15,
    max_retries_on_429=2, output_budget_chars=30000,
)

DEEP = ScrapeProfile(
    reddit_brand_pages=4, reddit_brand_per_page=100,
    reddit_category_pages=3, reddit_category_per_page=100,
    reddit_extra_queries=4, reddit_extra_per_page=100,
    reddit_comments_per_post=30, reddit_time_filter="all",
    reddit_subreddit_search=True,

    hn_brand_pages=4, hn_brand_per_page=50,
    hn_category_pages=2, hn_category_per_page=50,
    hn_include_date_sort=True, hn_comments_per_post=30,

    devto_brand_pages=4, devto_brand_per_page=30,
    devto_category_pages=2, devto_category_per_page=30,
    devto_comments_per_post=20, devto_multi_tag=True,

    youtube_max_results=25, youtube_comments_per_post=20,

    twitter_max_results=50,

    bluesky_max_results=50, bluesky_comments_per_post=15,

    v2ex_max_results=50, v2ex_comments_per_post=25,
    weibo_max_results=50, weibo_comments_per_post=20,
    bilibili_max_results=30, bilibili_comments_per_post=20,
    xueqiu_max_results=50,

    geo_query_templates=5, geo_content_snippet_chars=5000,

    serp_num_results=100,

    scoring_recency_halflife_days=23.0, scoring_convergence_threshold=0.4,

    request_delay_seconds=0.5, http_timeout_seconds=20,
    max_retries_on_429=3, output_budget_chars=80000,
)

_PROFILES = {"light": LIGHT, "normal": NORMAL, "deep": DEEP}


def get_scrape_profile() -> ScrapeProfile:
    """Return the active scrape profile based on env var OPENCMO_SCRAPE_DEPTH."""
    depth = os.environ.get("OPENCMO_SCRAPE_DEPTH", "deep").lower()
    return _PROFILES.get(depth, DEEP)

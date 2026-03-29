"""Multi-signal scoring module for cross-platform comparable engagement scores.

Ported from last30days-skill concepts: engagement velocity normalization,
text relevance scoring, temporal recency decay, and cross-platform convergence
detection via trigram Jaccard similarity.
"""

from __future__ import annotations

import math
import re
import string
from collections import defaultdict

from opencmo.tools.community_providers import DiscussionHit


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Static per-platform authority weights (0-100).
# Reflects signal quality for marketing intelligence.
SOURCE_AUTHORITY: dict[str, int] = {
    "hackernews": 80,
    "youtube": 75,
    "reddit": 60,
    "devto": 55,
    "bluesky": 45,
    "twitter": 50,
    # Chinese platforms
    "xueqiu": 70,
    "v2ex": 65,
    "bilibili": 60,
    "wechat": 60,
    "xiaohongshu": 55,
    "weibo": 50,
    "douyin": 50,
}

# Composite score weights
W_VELOCITY = 0.35
W_TEXT_RELEVANCE = 0.25
W_RECENCY = 0.20
W_CONVERGENCE = 0.10
W_AUTHORITY = 0.10

# English stop words for text normalization
_STOP_WORDS = frozenset(
    "a an the is are was were be been being have has had do does did will "
    "would shall should may might can could and but or nor for yet so at by "
    "to from in on of it its i me my we our you your he his she her they "
    "their this that these those with as".split()
)

# Synonym map for common marketing/tech terms
_SYNONYMS: dict[str, str] = {
    "seo": "search engine optimization",
    "search engine optimization": "seo",
    "ai": "artificial intelligence",
    "artificial intelligence": "ai",
    "ml": "machine learning",
    "machine learning": "ml",
    "llm": "large language model",
    "large language model": "llm",
    "saas": "software as a service",
    "api": "application programming interface",
    "ui": "user interface",
    "ux": "user experience",
    "devops": "development operations",
    "ci/cd": "continuous integration continuous deployment",
    "cms": "content management system",
    "crm": "customer relationship management",
}


# ---------------------------------------------------------------------------
# Text normalization and similarity
# ---------------------------------------------------------------------------


def _normalize_text(text: str) -> list[str]:
    """Lowercase, remove punctuation, remove stop words, return token list."""
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    tokens = text.split()
    return [t for t in tokens if t not in _STOP_WORDS and len(t) > 1]


def _expand_with_synonyms(tokens: list[str]) -> set[str]:
    """Expand token set with known synonyms."""
    expanded = set(tokens)
    for token in tokens:
        syn = _SYNONYMS.get(token)
        if syn:
            expanded.update(syn.split())
    return expanded


def _trigrams(text: str) -> set[str]:
    """Generate character trigrams from text."""
    text = re.sub(r"\s+", " ", text.lower().strip())
    if len(text) < 3:
        return {text} if text else set()
    return {text[i : i + 3] for i in range(len(text) - 2)}


def text_relevance(query: str, title: str, preview: str = "") -> float:
    """Bidirectional token-overlap Jaccard between query and hit text.

    Returns a score in [0.0, 1.0].
    """
    q_tokens = _normalize_text(query)
    t_tokens = _normalize_text(f"{title} {preview}")

    if not q_tokens or not t_tokens:
        return 0.0

    q_set = _expand_with_synonyms(q_tokens)
    t_set = _expand_with_synonyms(t_tokens)

    # Forward: how much of query appears in text
    forward = len(q_set & t_set) / len(q_set) if q_set else 0.0
    # Reverse: how much of text is explained by query
    reverse = len(q_set & t_set) / len(t_set) if t_set else 0.0

    return 0.6 * forward + 0.4 * reverse


def trigram_jaccard(a: str, b: str) -> float:
    """Hybrid trigram-token Jaccard similarity between two strings.

    Returns a score in [0.0, 1.0].
    """
    tri_a = _trigrams(a)
    tri_b = _trigrams(b)
    if not tri_a or not tri_b:
        return 0.0
    intersection = len(tri_a & tri_b)
    union = len(tri_a | tri_b)
    return intersection / union if union else 0.0


# ---------------------------------------------------------------------------
# Scoring components
# ---------------------------------------------------------------------------


def velocity_score(raw_score: int, comments_count: int, age_days: int) -> float:
    """Engagement velocity: raw engagement per day, normalized to ~[0, 100].

    Uses a log-based normalization since raw velocities can vary enormously.
    """
    age_hours = max(1, age_days * 24)
    raw_engagement = raw_score + comments_count * 2
    velocity = raw_engagement / age_hours
    # Log normalization: most velocities are < 1.0 per hour,
    # but viral posts can be 10+/hr. Map via log to ~0-100.
    return min(100.0, max(0.0, (math.log1p(velocity * 100) / math.log1p(100)) * 100))


def recency_score(age_days: int, halflife_days: float = 23.0) -> float:
    """Exponential temporal recency decay.

    Returns a score in [0, 100]. Posts from today ≈ 100, 23-day-old posts ≈ 50.
    """
    decay_rate = math.log(2) / halflife_days
    return min(100.0, math.exp(-decay_rate * age_days) * 100.0)


# ---------------------------------------------------------------------------
# Convergence detection
# ---------------------------------------------------------------------------


def detect_convergence_clusters(
    hits: list[DiscussionHit],
    threshold: float = 0.5,
) -> dict[int, int]:
    """Detect cross-platform duplicate stories via trigram Jaccard.

    Returns a dict mapping hit index → cluster_id.
    Hits within the same platform are not clustered together.
    """
    n = len(hits)
    clusters: dict[int, int] = {}  # hit_index -> cluster_id
    next_cluster = 0

    # Precompute normalized titles
    titles = [h.title.lower().strip() for h in hits]

    for i in range(n):
        if i in clusters:
            continue
        # Start a new cluster with this hit
        cluster_id = next_cluster
        next_cluster += 1
        clusters[i] = cluster_id
        cluster_platforms = {hits[i].platform}

        for j in range(i + 1, n):
            if j in clusters:
                continue
            # Only cluster across different platforms
            if hits[j].platform in cluster_platforms and hits[j].platform == hits[i].platform:
                continue
            sim = trigram_jaccard(titles[i], titles[j])
            if sim >= threshold:
                clusters[j] = cluster_id
                cluster_platforms.add(hits[j].platform)

    return clusters


def convergence_boost(clusters: dict[int, int], hit_index: int) -> float:
    """Score boost for hits that appear across multiple platforms.

    Returns 0 for single-hit clusters, 10 * (cluster_size - 1) otherwise, capped at 30.
    """
    if hit_index not in clusters:
        return 0.0
    cluster_id = clusters[hit_index]
    cluster_size = sum(1 for cid in clusters.values() if cid == cluster_id)
    if cluster_size <= 1:
        return 0.0
    return min(30.0, 10.0 * (cluster_size - 1))


# ---------------------------------------------------------------------------
# Composite scoring
# ---------------------------------------------------------------------------


def compute_composite_score(
    hit: DiscussionHit,
    query: str,
    cluster_boost: float = 0.0,
    halflife_days: float = 23.0,
) -> int:
    """Compute a cross-platform comparable engagement score in [0, 100].

    Combines: velocity (35%), text relevance (25%), recency (20%),
    convergence (10%), source authority (10%).
    """
    v = velocity_score(hit.raw_score, hit.comments_count, hit.age_days)
    tr = text_relevance(query, hit.title, hit.preview) * 100.0
    rc = recency_score(hit.age_days, halflife_days)
    authority = SOURCE_AUTHORITY.get(hit.platform, 50)

    composite = (
        W_VELOCITY * v
        + W_TEXT_RELEVANCE * tr
        + W_RECENCY * rc
        + W_CONVERGENCE * cluster_boost
        + W_AUTHORITY * authority
    )
    return min(100, max(0, int(composite)))


# ---------------------------------------------------------------------------
# Public API: rescore all hits
# ---------------------------------------------------------------------------


def rescore_hits(
    hits: list[DiscussionHit],
    query: str,
    halflife_days: float = 23.0,
    convergence_threshold: float = 0.5,
) -> list[DiscussionHit]:
    """Rescore all hits with the multi-signal composite scoring system.

    Mutates each hit's engagement_score in place and returns the list.
    The original raw_score remains unchanged for reference.
    """
    if not hits:
        return hits

    # Detect cross-platform convergence clusters
    clusters = detect_convergence_clusters(hits, threshold=convergence_threshold)

    # Rescore each hit
    for i, hit in enumerate(hits):
        boost = convergence_boost(clusters, i)
        hit.engagement_score = compute_composite_score(
            hit, query, cluster_boost=boost, halflife_days=halflife_days,
        )

    return hits

"""Tests for the Proactive Insight Engine — detectors, dedup, storage CRUD, and API."""

import asyncio
import os
from unittest.mock import patch, AsyncMock

import pytest

from opencmo import storage
from opencmo.insights import (
    Insight,
    _detect_serp_drops,
    _detect_geo_decline,
    _detect_community_buzz,
    _detect_seo_regress,
    _detect_competitor_gaps,
    detect_insights,
)

# FastAPI is an optional dependency
pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from opencmo.web import chat_sessions, task_registry
from opencmo.web.app import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _use_light_profile(monkeypatch):
    monkeypatch.setenv("OPENCMO_SCRAPE_DEPTH", "light")


@pytest.fixture
def db(tmp_path):
    """Patch storage to use an isolated SQLite database for each test."""
    db_path = tmp_path / "test.db"
    with patch.object(storage, "_DB_PATH", db_path), \
         patch.object(storage, "_SCHEMA_READY_FOR", None):
        yield db_path


@pytest.fixture
def client(db):
    """FastAPI TestClient with isolated DB."""
    asyncio.run(chat_sessions.clear_all())
    task_registry.clear_all()
    with TestClient(app) as test_client:
        yield test_client


def _seed_project(brand="TestBrand", url="https://test.com"):
    return asyncio.run(storage.ensure_project(brand, url, "testing"))


# ---------------------------------------------------------------------------
# Helper: seed SERP snapshots directly via SQL
# ---------------------------------------------------------------------------


async def _seed_serp_snapshots(project_id, keyword, positions):
    """Insert SERP snapshots for a keyword. positions is ordered oldest-first."""
    db = await storage.get_db()
    try:
        for i, pos in enumerate(positions):
            await db.execute(
                "INSERT INTO serp_snapshots (project_id, keyword, position, provider, checked_at) "
                "VALUES (?, ?, ?, 'test', datetime('now', ?))",
                (project_id, keyword, pos, f"-{len(positions) - 1 - i} hours"),
            )
        await db.commit()
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Helper: seed competitors and competitor keywords
# ---------------------------------------------------------------------------


async def _seed_competitors(project_id, competitors):
    """competitors is a list of (name, [keywords])."""
    db = await storage.get_db()
    try:
        for name, keywords in competitors:
            cursor = await db.execute(
                "INSERT INTO competitors (project_id, name) VALUES (?, ?)",
                (project_id, name),
            )
            comp_id = cursor.lastrowid
            for kw in keywords:
                await db.execute(
                    "INSERT INTO competitor_keywords (competitor_id, keyword) VALUES (?, ?)",
                    (comp_id, kw),
                )
        await db.commit()
    finally:
        await db.close()


async def _seed_tracked_keywords(project_id, keywords):
    db = await storage.get_db()
    try:
        for kw in keywords:
            await db.execute(
                "INSERT OR IGNORE INTO tracked_keywords (project_id, keyword) VALUES (?, ?)",
                (project_id, kw),
            )
        await db.commit()
    finally:
        await db.close()


# ===========================================================================
# 1. Detector tests
# ===========================================================================


class TestDetectSerpDrops:
    """_detect_serp_drops: keyword rank drop detection."""

    def test_large_drop_detected(self, db):
        """A drop of 5+ positions produces an insight."""
        pid = _seed_project()
        # Position went from 3 to 10 (drop of 7)
        asyncio.run(_seed_serp_snapshots(pid, "ai tools", [3, 10]))
        insights = asyncio.run(_detect_serp_drops(pid))
        assert len(insights) == 1
        assert insights[0].insight_type == "serp_drop"
        assert "ai tools" in insights[0].title
        assert "7" in insights[0].title

    def test_small_drop_ignored(self, db):
        """A drop of less than 5 positions produces no insight."""
        pid = _seed_project()
        # Position went from 5 to 8 (drop of 3)
        asyncio.run(_seed_serp_snapshots(pid, "seo tool", [5, 8]))
        insights = asyncio.run(_detect_serp_drops(pid))
        assert len(insights) == 0

    def test_improvement_ignored(self, db):
        """An improvement in position (lower number) produces no insight."""
        pid = _seed_project()
        # Position went from 10 to 3 (improvement)
        asyncio.run(_seed_serp_snapshots(pid, "best tool", [10, 3]))
        insights = asyncio.run(_detect_serp_drops(pid))
        assert len(insights) == 0

    def test_no_data_returns_empty(self, db):
        """No SERP data returns empty list."""
        pid = _seed_project()
        insights = asyncio.run(_detect_serp_drops(pid))
        assert insights == []

    def test_single_snapshot_ignored(self, db):
        """A keyword with only one snapshot cannot compute a delta."""
        pid = _seed_project()
        asyncio.run(_seed_serp_snapshots(pid, "only one", [5]))
        insights = asyncio.run(_detect_serp_drops(pid))
        assert insights == []

    def test_multiple_keywords(self, db):
        """Multiple keywords each checked independently."""
        pid = _seed_project()
        asyncio.run(_seed_serp_snapshots(pid, "kw_drop", [2, 15]))     # drop 13
        asyncio.run(_seed_serp_snapshots(pid, "kw_stable", [5, 6]))    # drop 1
        asyncio.run(_seed_serp_snapshots(pid, "kw_big_drop", [1, 20])) # drop 19
        insights = asyncio.run(_detect_serp_drops(pid))
        types = {i.title for i in insights}
        assert len(insights) == 2
        assert any("kw_drop" in t for t in types)
        assert any("kw_big_drop" in t for t in types)


class TestDetectGeoDecline:
    """_detect_geo_decline: GEO score drop detection."""

    def test_large_decline_detected(self, db):
        """A GEO score drop of 10+ points produces an insight."""
        pid = _seed_project()
        with patch.object(storage, "get_latest_scans", new_callable=AsyncMock) as mock_latest, \
             patch.object(storage, "get_previous_scans", new_callable=AsyncMock) as mock_prev:
            mock_latest.return_value = {"geo": {"score": 60, "scanned_at": "2025-01-02"}}
            mock_prev.return_value = {"geo": {"score": 80, "scanned_at": "2025-01-01"}}
            insights = asyncio.run(_detect_geo_decline(pid))
        assert len(insights) == 1
        assert insights[0].insight_type == "geo_decline"
        assert "20" in insights[0].title

    def test_small_decline_ignored(self, db):
        """A GEO score drop of less than 10 points produces no insight."""
        pid = _seed_project()
        with patch.object(storage, "get_latest_scans", new_callable=AsyncMock) as mock_latest, \
             patch.object(storage, "get_previous_scans", new_callable=AsyncMock) as mock_prev:
            mock_latest.return_value = {"geo": {"score": 72, "scanned_at": "2025-01-02"}}
            mock_prev.return_value = {"geo": {"score": 78, "scanned_at": "2025-01-01"}}
            insights = asyncio.run(_detect_geo_decline(pid))
        assert len(insights) == 0

    def test_improvement_ignored(self, db):
        """A GEO score improvement produces no insight."""
        pid = _seed_project()
        with patch.object(storage, "get_latest_scans", new_callable=AsyncMock) as mock_latest, \
             patch.object(storage, "get_previous_scans", new_callable=AsyncMock) as mock_prev:
            mock_latest.return_value = {"geo": {"score": 85, "scanned_at": "2025-01-02"}}
            mock_prev.return_value = {"geo": {"score": 70, "scanned_at": "2025-01-01"}}
            insights = asyncio.run(_detect_geo_decline(pid))
        assert len(insights) == 0

    def test_no_previous_data(self, db):
        """No previous scan returns empty list."""
        pid = _seed_project()
        with patch.object(storage, "get_latest_scans", new_callable=AsyncMock) as mock_latest, \
             patch.object(storage, "get_previous_scans", new_callable=AsyncMock) as mock_prev:
            mock_latest.return_value = {"geo": {"score": 70, "scanned_at": "2025-01-02"}}
            mock_prev.return_value = None
            insights = asyncio.run(_detect_geo_decline(pid))
        assert len(insights) == 0

    def test_no_geo_in_latest(self, db):
        """Missing GEO data in latest scan returns empty list."""
        pid = _seed_project()
        with patch.object(storage, "get_latest_scans", new_callable=AsyncMock) as mock_latest, \
             patch.object(storage, "get_previous_scans", new_callable=AsyncMock) as mock_prev:
            mock_latest.return_value = {"geo": None}
            mock_prev.return_value = {"geo": {"score": 80, "scanned_at": "2025-01-01"}}
            insights = asyncio.run(_detect_geo_decline(pid))
        assert len(insights) == 0


class TestDetectCommunityBuzz:
    """_detect_community_buzz: high-engagement discussion detection."""

    def test_high_engagement_detected(self, db):
        """Discussions with engagement score > 50 produce insights."""
        pid = _seed_project()
        discussions = [
            {
                "title": "OpenCMO is amazing for indie hackers and startups",
                "platform": "reddit",
                "engagement_score": 75,
                "comments_count": 30,
                "url": "https://reddit.com/r/test/1",
            },
        ]
        with patch.object(storage, "get_tracked_discussions", new_callable=AsyncMock) as mock_disc:
            mock_disc.return_value = discussions
            insights = asyncio.run(_detect_community_buzz(pid))
        assert len(insights) == 1
        assert insights[0].insight_type == "community_buzz"
        assert "reddit" in insights[0].title

    def test_low_engagement_ignored(self, db):
        """Discussions with engagement score <= 50 produce no insights."""
        pid = _seed_project()
        discussions = [
            {
                "title": "Some normal post",
                "platform": "hackernews",
                "engagement_score": 30,
                "comments_count": 5,
                "url": "https://news.ycombinator.com/item?id=1",
            },
        ]
        with patch.object(storage, "get_tracked_discussions", new_callable=AsyncMock) as mock_disc:
            mock_disc.return_value = discussions
            insights = asyncio.run(_detect_community_buzz(pid))
        assert len(insights) == 0

    def test_capped_at_three(self, db):
        """At most 3 community buzz insights are returned."""
        pid = _seed_project()
        discussions = [
            {
                "title": f"Hot post {i}",
                "platform": "reddit",
                "engagement_score": 60 + i,
                "comments_count": 10 + i,
                "url": f"https://reddit.com/r/test/{i}",
            }
            for i in range(5)
        ]
        with patch.object(storage, "get_tracked_discussions", new_callable=AsyncMock) as mock_disc:
            mock_disc.return_value = discussions
            insights = asyncio.run(_detect_community_buzz(pid))
        assert len(insights) == 3

    def test_null_engagement_ignored(self, db):
        """Discussions with null engagement_score are treated as 0."""
        pid = _seed_project()
        discussions = [
            {
                "title": "No score discussion",
                "platform": "devto",
                "engagement_score": None,
                "comments_count": 0,
                "url": "https://dev.to/test",
            },
        ]
        with patch.object(storage, "get_tracked_discussions", new_callable=AsyncMock) as mock_disc:
            mock_disc.return_value = discussions
            insights = asyncio.run(_detect_community_buzz(pid))
        assert len(insights) == 0


class TestDetectSeoRegress:
    """_detect_seo_regress: SEO performance score regression detection."""

    def test_large_regression_detected(self, db):
        """SEO score drop > 0.1 produces an insight."""
        pid = _seed_project()
        with patch.object(storage, "get_latest_scans", new_callable=AsyncMock) as mock_latest, \
             patch.object(storage, "get_previous_scans", new_callable=AsyncMock) as mock_prev:
            mock_latest.return_value = {"seo": {"score": 0.5, "scanned_at": "2025-01-02"}}
            mock_prev.return_value = {"seo": {"score": 0.8, "scanned_at": "2025-01-01"}}
            insights = asyncio.run(_detect_seo_regress(pid))
        assert len(insights) == 1
        assert insights[0].insight_type == "seo_regress"

    def test_small_regression_ignored(self, db):
        """SEO score drop of <= 0.1 produces no insight (must be > 0.1)."""
        pid = _seed_project()
        with patch.object(storage, "get_latest_scans", new_callable=AsyncMock) as mock_latest, \
             patch.object(storage, "get_previous_scans", new_callable=AsyncMock) as mock_prev:
            # Use 0.75 and 0.8 so drop = 0.05, clearly under the 0.1 threshold
            mock_latest.return_value = {"seo": {"score": 0.75, "scanned_at": "2025-01-02"}}
            mock_prev.return_value = {"seo": {"score": 0.8, "scanned_at": "2025-01-01"}}
            insights = asyncio.run(_detect_seo_regress(pid))
        assert len(insights) == 0

    def test_improvement_ignored(self, db):
        """SEO score improvement produces no insight."""
        pid = _seed_project()
        with patch.object(storage, "get_latest_scans", new_callable=AsyncMock) as mock_latest, \
             patch.object(storage, "get_previous_scans", new_callable=AsyncMock) as mock_prev:
            mock_latest.return_value = {"seo": {"score": 0.9, "scanned_at": "2025-01-02"}}
            mock_prev.return_value = {"seo": {"score": 0.7, "scanned_at": "2025-01-01"}}
            insights = asyncio.run(_detect_seo_regress(pid))
        assert len(insights) == 0

    def test_no_previous_seo_data(self, db):
        """No previous SEO scan returns empty list."""
        pid = _seed_project()
        with patch.object(storage, "get_latest_scans", new_callable=AsyncMock) as mock_latest, \
             patch.object(storage, "get_previous_scans", new_callable=AsyncMock) as mock_prev:
            mock_latest.return_value = {"seo": {"score": 0.7, "scanned_at": "2025-01-02"}}
            mock_prev.return_value = None
            insights = asyncio.run(_detect_seo_regress(pid))
        assert len(insights) == 0

    def test_null_scores(self, db):
        """Null scores in latest or previous scan return empty list."""
        pid = _seed_project()
        with patch.object(storage, "get_latest_scans", new_callable=AsyncMock) as mock_latest, \
             patch.object(storage, "get_previous_scans", new_callable=AsyncMock) as mock_prev:
            mock_latest.return_value = {"seo": {"score": None, "scanned_at": "2025-01-02"}}
            mock_prev.return_value = {"seo": {"score": 0.7, "scanned_at": "2025-01-01"}}
            insights = asyncio.run(_detect_seo_regress(pid))
        assert len(insights) == 0


class TestDetectCompetitorGaps:
    """_detect_competitor_gaps: competitor keyword gap detection."""

    def test_gaps_detected(self, db):
        """3+ competitor keywords not tracked by the brand produce an insight."""
        pid = _seed_project()
        asyncio.run(_seed_tracked_keywords(pid, ["my keyword"]))
        asyncio.run(_seed_competitors(pid, [
            ("Rival A", ["gap1", "gap2", "gap3"]),
            ("Rival B", ["gap1", "gap4"]),
        ]))
        insights = asyncio.run(_detect_competitor_gaps(pid))
        assert len(insights) == 1
        assert insights[0].insight_type == "competitor_gap"
        assert "keyword gaps" in insights[0].title

    def test_fewer_than_three_gaps_ignored(self, db):
        """Fewer than 3 gap keywords produce no insight."""
        pid = _seed_project()
        asyncio.run(_seed_tracked_keywords(pid, ["already tracked"]))
        asyncio.run(_seed_competitors(pid, [
            ("Rival A", ["gap1", "gap2"]),
        ]))
        insights = asyncio.run(_detect_competitor_gaps(pid))
        assert len(insights) == 0

    def test_no_gaps_when_all_tracked(self, db):
        """No gaps when brand tracks all competitor keywords."""
        pid = _seed_project()
        asyncio.run(_seed_tracked_keywords(pid, ["keyword1", "keyword2"]))
        asyncio.run(_seed_competitors(pid, [
            ("Rival A", ["keyword1", "keyword2"]),
        ]))
        insights = asyncio.run(_detect_competitor_gaps(pid))
        assert len(insights) == 0

    def test_no_competitors(self, db):
        """No competitors returns empty list."""
        pid = _seed_project()
        insights = asyncio.run(_detect_competitor_gaps(pid))
        assert insights == []


# ===========================================================================
# 2. Severity classification
# ===========================================================================


class TestSeverityClassification:
    """Verify critical vs warning thresholds for each detector."""

    def test_serp_drop_critical_at_10_plus(self, db):
        """SERP drop >= 10 is critical."""
        pid = _seed_project()
        asyncio.run(_seed_serp_snapshots(pid, "critical kw", [1, 11]))
        insights = asyncio.run(_detect_serp_drops(pid))
        assert len(insights) == 1
        assert insights[0].severity == "critical"

    def test_serp_drop_warning_under_10(self, db):
        """SERP drop of 5-9 is warning."""
        pid = _seed_project()
        asyncio.run(_seed_serp_snapshots(pid, "warning kw", [3, 8]))
        insights = asyncio.run(_detect_serp_drops(pid))
        assert len(insights) == 1
        assert insights[0].severity == "warning"

    def test_geo_decline_critical_at_20_plus(self, db):
        """GEO drop >= 20 is critical."""
        pid = _seed_project()
        with patch.object(storage, "get_latest_scans", new_callable=AsyncMock) as mock_latest, \
             patch.object(storage, "get_previous_scans", new_callable=AsyncMock) as mock_prev:
            mock_latest.return_value = {"geo": {"score": 50, "scanned_at": "2025-01-02"}}
            mock_prev.return_value = {"geo": {"score": 80, "scanned_at": "2025-01-01"}}
            insights = asyncio.run(_detect_geo_decline(pid))
        assert len(insights) == 1
        assert insights[0].severity == "critical"

    def test_geo_decline_warning_10_to_19(self, db):
        """GEO drop of 10-19 is warning."""
        pid = _seed_project()
        with patch.object(storage, "get_latest_scans", new_callable=AsyncMock) as mock_latest, \
             patch.object(storage, "get_previous_scans", new_callable=AsyncMock) as mock_prev:
            mock_latest.return_value = {"geo": {"score": 65, "scanned_at": "2025-01-02"}}
            mock_prev.return_value = {"geo": {"score": 80, "scanned_at": "2025-01-01"}}
            insights = asyncio.run(_detect_geo_decline(pid))
        assert len(insights) == 1
        assert insights[0].severity == "warning"

    def test_community_buzz_warning_above_80(self, db):
        """Community buzz with engagement > 80 is warning."""
        pid = _seed_project()
        discussions = [
            {"title": "Viral post", "platform": "reddit",
             "engagement_score": 95, "comments_count": 100,
             "url": "https://reddit.com/r/test/viral"},
        ]
        with patch.object(storage, "get_tracked_discussions", new_callable=AsyncMock) as mock_disc:
            mock_disc.return_value = discussions
            insights = asyncio.run(_detect_community_buzz(pid))
        assert len(insights) == 1
        assert insights[0].severity == "warning"

    def test_community_buzz_info_51_to_80(self, db):
        """Community buzz with engagement 51-80 is info."""
        pid = _seed_project()
        discussions = [
            {"title": "Moderate post", "platform": "hackernews",
             "engagement_score": 60, "comments_count": 15,
             "url": "https://news.ycombinator.com/item?id=2"},
        ]
        with patch.object(storage, "get_tracked_discussions", new_callable=AsyncMock) as mock_disc:
            mock_disc.return_value = discussions
            insights = asyncio.run(_detect_community_buzz(pid))
        assert len(insights) == 1
        assert insights[0].severity == "info"

    def test_seo_regress_critical_above_0_3(self, db):
        """SEO drop > 0.3 is critical."""
        pid = _seed_project()
        with patch.object(storage, "get_latest_scans", new_callable=AsyncMock) as mock_latest, \
             patch.object(storage, "get_previous_scans", new_callable=AsyncMock) as mock_prev:
            mock_latest.return_value = {"seo": {"score": 0.3, "scanned_at": "2025-01-02"}}
            mock_prev.return_value = {"seo": {"score": 0.9, "scanned_at": "2025-01-01"}}
            insights = asyncio.run(_detect_seo_regress(pid))
        assert len(insights) == 1
        assert insights[0].severity == "critical"

    def test_seo_regress_warning_0_1_to_0_3(self, db):
        """SEO drop of 0.1-0.3 is warning."""
        pid = _seed_project()
        with patch.object(storage, "get_latest_scans", new_callable=AsyncMock) as mock_latest, \
             patch.object(storage, "get_previous_scans", new_callable=AsyncMock) as mock_prev:
            mock_latest.return_value = {"seo": {"score": 0.6, "scanned_at": "2025-01-02"}}
            mock_prev.return_value = {"seo": {"score": 0.8, "scanned_at": "2025-01-01"}}
            insights = asyncio.run(_detect_seo_regress(pid))
        assert len(insights) == 1
        assert insights[0].severity == "warning"

    def test_competitor_gap_always_warning(self, db):
        """Competitor gaps are always severity=warning."""
        pid = _seed_project()
        asyncio.run(_seed_tracked_keywords(pid, ["mine"]))
        asyncio.run(_seed_competitors(pid, [
            ("Rival", ["g1", "g2", "g3", "g4"]),
        ]))
        insights = asyncio.run(_detect_competitor_gaps(pid))
        assert len(insights) == 1
        assert insights[0].severity == "warning"


# ===========================================================================
# 3. Dedup logic
# ===========================================================================


class TestDedup:
    """is_insight_duplicate returns True for same type+title within 24h."""

    def test_duplicate_detected(self, db):
        """An insight with the same type and title saved recently is a duplicate."""
        pid = _seed_project()
        asyncio.run(storage.save_insight(
            pid, "serp_drop", "warning",
            "Keyword 'ai' dropped 5 positions",
            "Test summary", "navigate", "{}",
        ))
        is_dup = asyncio.run(storage.is_insight_duplicate(
            pid, "serp_drop", "Keyword 'ai' dropped 5 positions",
        ))
        assert is_dup is True

    def test_different_type_not_duplicate(self, db):
        """Same title but different insight_type is not a duplicate."""
        pid = _seed_project()
        asyncio.run(storage.save_insight(
            pid, "serp_drop", "warning",
            "Same title", "Summary", "navigate", "{}",
        ))
        is_dup = asyncio.run(storage.is_insight_duplicate(
            pid, "geo_decline", "Same title",
        ))
        assert is_dup is False

    def test_different_title_not_duplicate(self, db):
        """Same type but different title is not a duplicate."""
        pid = _seed_project()
        asyncio.run(storage.save_insight(
            pid, "serp_drop", "warning",
            "Title A", "Summary", "navigate", "{}",
        ))
        is_dup = asyncio.run(storage.is_insight_duplicate(
            pid, "serp_drop", "Title B",
        ))
        assert is_dup is False

    def test_different_project_not_duplicate(self, db):
        """Same type and title but different project is not a duplicate."""
        pid1 = _seed_project("Brand1", "https://brand1.com")
        pid2 = _seed_project("Brand2", "https://brand2.com")
        asyncio.run(storage.save_insight(
            pid1, "serp_drop", "warning",
            "Same insight", "Summary", "navigate", "{}",
        ))
        is_dup = asyncio.run(storage.is_insight_duplicate(
            pid2, "serp_drop", "Same insight",
        ))
        assert is_dup is False

    def test_detect_insights_skips_duplicates(self, db):
        """detect_insights() does not re-save insights that already exist."""
        pid = _seed_project()
        # Seed data that will trigger a SERP drop insight
        asyncio.run(_seed_serp_snapshots(pid, "dup_kw", [2, 12]))

        # First run: insight should be saved
        with patch.object(storage, "get_latest_scans", new_callable=AsyncMock) as mock_latest, \
             patch.object(storage, "get_previous_scans", new_callable=AsyncMock) as mock_prev, \
             patch.object(storage, "get_tracked_discussions", new_callable=AsyncMock) as mock_disc:
            mock_latest.return_value = {"seo": None, "geo": None, "community": None, "serp": []}
            mock_prev.return_value = None
            mock_disc.return_value = []
            saved1 = asyncio.run(detect_insights(pid))

        assert len(saved1) == 1  # The SERP drop

        # Second run: same insight should be deduped
        with patch.object(storage, "get_latest_scans", new_callable=AsyncMock) as mock_latest, \
             patch.object(storage, "get_previous_scans", new_callable=AsyncMock) as mock_prev, \
             patch.object(storage, "get_tracked_discussions", new_callable=AsyncMock) as mock_disc:
            mock_latest.return_value = {"seo": None, "geo": None, "community": None, "serp": []}
            mock_prev.return_value = None
            mock_disc.return_value = []
            saved2 = asyncio.run(detect_insights(pid))

        assert len(saved2) == 0  # Deduped


# ===========================================================================
# 4. Storage CRUD
# ===========================================================================


class TestStorageCRUD:
    """save_insight, list_insights, mark_insight_read, get_insights_summary."""

    def test_save_and_list(self, db):
        """Saved insights appear in list_insights."""
        pid = _seed_project()
        iid = asyncio.run(storage.save_insight(
            pid, "serp_drop", "warning",
            "Test title", "Test summary", "navigate", '{"route": "/serp"}',
        ))
        assert iid > 0

        items = asyncio.run(storage.list_insights())
        assert len(items) == 1
        assert items[0]["id"] == iid
        assert items[0]["title"] == "Test title"
        assert items[0]["read"] is False

    def test_list_with_project_filter(self, db):
        """list_insights filters by project_id."""
        pid1 = _seed_project("Brand1", "https://b1.com")
        pid2 = _seed_project("Brand2", "https://b2.com")
        asyncio.run(storage.save_insight(pid1, "serp_drop", "warning", "P1 insight", "s", "navigate", "{}"))
        asyncio.run(storage.save_insight(pid2, "geo_decline", "critical", "P2 insight", "s", "navigate", "{}"))

        p1_items = asyncio.run(storage.list_insights(project_id=pid1))
        assert len(p1_items) == 1
        assert p1_items[0]["project_id"] == pid1

        p2_items = asyncio.run(storage.list_insights(project_id=pid2))
        assert len(p2_items) == 1
        assert p2_items[0]["project_id"] == pid2

    def test_list_unread_filter(self, db):
        """list_insights with unread_only=True excludes read insights."""
        pid = _seed_project()
        iid1 = asyncio.run(storage.save_insight(pid, "serp_drop", "warning", "Unread", "s", "navigate", "{}"))
        iid2 = asyncio.run(storage.save_insight(pid, "geo_decline", "warning", "Will be read", "s", "navigate", "{}"))
        asyncio.run(storage.mark_insight_read(iid2))

        unread = asyncio.run(storage.list_insights(unread_only=True))
        assert len(unread) == 1
        assert unread[0]["id"] == iid1

        all_items = asyncio.run(storage.list_insights(unread_only=False))
        assert len(all_items) == 2

    def test_mark_insight_read(self, db):
        """mark_insight_read flips the read flag."""
        pid = _seed_project()
        iid = asyncio.run(storage.save_insight(pid, "serp_drop", "warning", "Read me", "s", "navigate", "{}"))

        ok = asyncio.run(storage.mark_insight_read(iid))
        assert ok is True

        items = asyncio.run(storage.list_insights())
        assert items[0]["read"] is True

    def test_mark_already_read_returns_false(self, db):
        """Marking an already-read insight returns False."""
        pid = _seed_project()
        iid = asyncio.run(storage.save_insight(pid, "serp_drop", "warning", "Already read", "s", "navigate", "{}"))
        asyncio.run(storage.mark_insight_read(iid))

        ok = asyncio.run(storage.mark_insight_read(iid))
        assert ok is False

    def test_mark_nonexistent_returns_false(self, db):
        """Marking a nonexistent insight returns False."""
        _seed_project()  # ensure DB schema is created
        ok = asyncio.run(storage.mark_insight_read(99999))
        assert ok is False

    def test_get_insights_summary_global(self, db):
        """get_insights_summary returns correct unread count and recent items."""
        pid = _seed_project()
        asyncio.run(storage.save_insight(pid, "serp_drop", "warning", "I1", "s", "navigate", "{}"))
        asyncio.run(storage.save_insight(pid, "geo_decline", "critical", "I2", "s", "navigate", "{}"))
        asyncio.run(storage.save_insight(pid, "seo_regress", "warning", "I3", "s", "navigate", "{}"))
        iid4 = asyncio.run(storage.save_insight(pid, "community_buzz", "info", "I4", "s", "navigate", "{}"))
        asyncio.run(storage.mark_insight_read(iid4))

        summary = asyncio.run(storage.get_insights_summary())
        assert summary["unread_count"] == 3  # 4 total - 1 read
        assert len(summary["recent"]) == 3   # capped at 3

    def test_get_insights_summary_with_project(self, db):
        """get_insights_summary filters by project_id."""
        pid1 = _seed_project("Brand1", "https://b1.com")
        pid2 = _seed_project("Brand2", "https://b2.com")
        asyncio.run(storage.save_insight(pid1, "serp_drop", "warning", "P1", "s", "navigate", "{}"))
        asyncio.run(storage.save_insight(pid2, "geo_decline", "critical", "P2", "s", "navigate", "{}"))

        s1 = asyncio.run(storage.get_insights_summary(project_id=pid1))
        assert s1["unread_count"] == 1
        assert s1["recent"][0]["title"] == "P1"

        s2 = asyncio.run(storage.get_insights_summary(project_id=pid2))
        assert s2["unread_count"] == 1
        assert s2["recent"][0]["title"] == "P2"

    def test_list_respects_limit(self, db):
        """list_insights respects the limit parameter."""
        pid = _seed_project()
        for i in range(5):
            asyncio.run(storage.save_insight(pid, "serp_drop", "warning", f"I{i}", "s", "navigate", "{}"))

        items = asyncio.run(storage.list_insights(limit=3))
        assert len(items) == 3

    def test_list_ordered_newest_first(self, db):
        """list_insights returns items ordered by created_at DESC, id DESC."""
        pid = _seed_project()
        # Insert with explicit timestamps to guarantee ordering
        async def _insert_with_timestamp():
            db_conn = await storage.get_db()
            try:
                await db_conn.execute(
                    "INSERT INTO insights (project_id, insight_type, severity, title, summary, "
                    "action_type, action_params, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (pid, "serp_drop", "warning", "Older", "s", "navigate", "{}", "2025-01-01 00:00:00"),
                )
                await db_conn.execute(
                    "INSERT INTO insights (project_id, insight_type, severity, title, summary, "
                    "action_type, action_params, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (pid, "geo_decline", "critical", "Newer", "s", "navigate", "{}", "2025-01-02 00:00:00"),
                )
                await db_conn.commit()
            finally:
                await db_conn.close()
        asyncio.run(_insert_with_timestamp())

        items = asyncio.run(storage.list_insights())
        assert items[0]["title"] == "Newer"
        assert items[1]["title"] == "Older"


# ===========================================================================
# 5. API endpoint tests
# ===========================================================================


class TestInsightsAPI:
    """FastAPI endpoint tests for insights."""

    def test_get_insights_summary_empty(self, client):
        """GET /api/v1/insights/summary returns zero count when no insights exist."""
        resp = client.get("/api/v1/insights/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["unread_count"] == 0
        assert data["recent"] == []

    def test_get_insights_summary_with_data(self, client):
        """GET /api/v1/insights/summary returns correct unread count."""
        pid = _seed_project()
        asyncio.run(storage.save_insight(pid, "serp_drop", "warning", "Drop 1", "s", "navigate", "{}"))
        asyncio.run(storage.save_insight(pid, "geo_decline", "critical", "Decline 1", "s", "navigate", "{}"))

        resp = client.get("/api/v1/insights/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["unread_count"] == 2
        assert len(data["recent"]) == 2

    def test_get_insights_summary_with_project_filter(self, client):
        """GET /api/v1/insights/summary?project_id=N filters correctly."""
        pid1 = _seed_project("Brand1", "https://b1.com")
        pid2 = _seed_project("Brand2", "https://b2.com")
        asyncio.run(storage.save_insight(pid1, "serp_drop", "warning", "P1 insight", "s", "navigate", "{}"))
        asyncio.run(storage.save_insight(pid2, "geo_decline", "critical", "P2 insight", "s", "navigate", "{}"))

        resp = client.get(f"/api/v1/insights/summary?project_id={pid1}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["unread_count"] == 1

    def test_get_insights_list(self, client):
        """GET /api/v1/insights returns all insights."""
        pid = _seed_project()
        asyncio.run(storage.save_insight(pid, "serp_drop", "warning", "Insight A", "s", "navigate", "{}"))
        asyncio.run(storage.save_insight(pid, "geo_decline", "critical", "Insight B", "s", "navigate", "{}"))

        resp = client.get("/api/v1/insights")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_get_insights_with_project_filter(self, client):
        """GET /api/v1/insights?project_id=N filters by project."""
        pid1 = _seed_project("Brand1", "https://b1.com")
        pid2 = _seed_project("Brand2", "https://b2.com")
        asyncio.run(storage.save_insight(pid1, "serp_drop", "warning", "P1", "s", "navigate", "{}"))
        asyncio.run(storage.save_insight(pid2, "geo_decline", "critical", "P2", "s", "navigate", "{}"))

        resp = client.get(f"/api/v1/insights?project_id={pid1}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["project_id"] == pid1

    def test_get_insights_unread_filter(self, client):
        """GET /api/v1/insights?unread=true filters to unread only."""
        pid = _seed_project()
        iid1 = asyncio.run(storage.save_insight(pid, "serp_drop", "warning", "Unread", "s", "navigate", "{}"))
        iid2 = asyncio.run(storage.save_insight(pid, "geo_decline", "critical", "Read", "s", "navigate", "{}"))
        asyncio.run(storage.mark_insight_read(iid2))

        resp = client.get("/api/v1/insights?unread=true")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == iid1

    def test_post_insight_read(self, client):
        """POST /api/v1/insights/{id}/read marks an insight as read."""
        pid = _seed_project()
        iid = asyncio.run(storage.save_insight(pid, "serp_drop", "warning", "Mark me", "s", "navigate", "{}"))

        resp = client.post(f"/api/v1/insights/{iid}/read")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

        # Verify it is now read
        items = asyncio.run(storage.list_insights(unread_only=True))
        assert len(items) == 0

    def test_post_insight_read_not_found(self, client):
        """POST /api/v1/insights/{id}/read returns 404 for nonexistent insight."""
        _seed_project()  # ensure DB is initialized
        resp = client.post("/api/v1/insights/99999/read")
        assert resp.status_code == 404

    def test_post_insight_read_already_read(self, client):
        """POST /api/v1/insights/{id}/read returns 404 if already read."""
        pid = _seed_project()
        iid = asyncio.run(storage.save_insight(pid, "serp_drop", "warning", "Already read", "s", "navigate", "{}"))
        asyncio.run(storage.mark_insight_read(iid))

        resp = client.post(f"/api/v1/insights/{iid}/read")
        assert resp.status_code == 404
        assert "already read" in resp.json()["error"].lower()

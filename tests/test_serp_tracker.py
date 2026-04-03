"""Tests for SERP tracker — provider, storage, trends."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    """Use a temporary DB for tests."""
    from opencmo import storage
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(storage, "_DB_PATH", db_path)
    return db_path


# ---------------------------------------------------------------------------
# Provider tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_serp_provider_crawl_failure():
    """Crawl failure returns position=None + error string, doesn't raise."""
    from opencmo.tools.serp_tracker import CrawlSerpProvider

    provider = CrawlSerpProvider()
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))
        mock_client_cls.return_value = mock_client

        result = await provider.check_ranking("test query", "example.com")

    assert result.position is None
    assert result.error is not None
    assert "Connection refused" in result.error
    assert result.provider == "crawl"


@pytest.mark.asyncio
async def test_serp_provider_success_found():
    """Provider finds target domain in results."""
    from opencmo.tools.serp_tracker import CrawlSerpProvider

    provider = CrawlSerpProvider()
    fake_html = '''
    <a href="/url?q=https://other.com/page1">Other</a>
    <a href="/url?q=https://example.com/article">Target</a>
    <a href="/url?q=https://another.com/page">Another</a>
    '''
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_resp = MagicMock()
        mock_resp.text = fake_html
        mock_resp.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        result = await provider.check_ranking("test", "example.com")

    assert result.position == 2
    assert result.url_found == "https://example.com/article"
    assert result.error is None


@pytest.mark.asyncio
async def test_serp_provider_success_not_found():
    """Provider correctly reports not-found (no matching domain)."""
    from opencmo.tools.serp_tracker import CrawlSerpProvider

    provider = CrawlSerpProvider()
    fake_html = '<a href="/url?q=https://other.com/page">Other</a>'
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_resp = MagicMock()
        mock_resp.text = fake_html
        mock_resp.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        result = await provider.check_ranking("test", "example.com")

    assert result.position is None
    assert result.url_found is None
    assert result.error is None


# ---------------------------------------------------------------------------
# Storage tests (tracked_keywords + serp_snapshots)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tracked_keywords_crud(tmp_db):
    """Add, list, remove tracked keywords."""
    from opencmo import storage

    pid = await storage.ensure_project("Test", "https://example.com", "saas")

    kw_id = await storage.add_tracked_keyword(pid, "python web scraping")
    assert kw_id > 0

    keywords = await storage.list_tracked_keywords(pid)
    assert len(keywords) == 1
    assert keywords[0]["keyword"] == "python web scraping"

    # Duplicate should be ignored
    await storage.add_tracked_keyword(pid, "python web scraping")
    keywords = await storage.list_tracked_keywords(pid)
    assert len(keywords) == 1

    ok = await storage.remove_tracked_keyword(kw_id)
    assert ok
    keywords = await storage.list_tracked_keywords(pid)
    assert len(keywords) == 0


@pytest.mark.asyncio
async def test_serp_snapshot_crud(tmp_db):
    """Save and query SERP snapshots with provider + error columns."""
    from opencmo import storage

    pid = await storage.ensure_project("Test", "https://example.com", "saas")
    await storage.add_tracked_keyword(pid, "test keyword")

    snap_id = await storage.save_serp_snapshot(
        pid, "test keyword", 5, "https://example.com/page", "crawl", None
    )
    assert snap_id > 0

    history = await storage.get_serp_history(pid, "test keyword", limit=10)
    assert len(history) == 1
    assert history[0]["position"] == 5
    assert history[0]["provider"] == "crawl"
    assert history[0]["error"] is None


@pytest.mark.asyncio
async def test_serp_snapshot_error_vs_not_ranked(tmp_db):
    """Distinguish error (error IS NOT NULL) from not-ranked (position IS NULL, error IS NULL)."""
    from opencmo import storage

    pid = await storage.ensure_project("Test", "https://example.com", "saas")

    # Error case
    await storage.save_serp_snapshot(pid, "kw1", None, None, "crawl", "Connection refused")
    # Not ranked case
    await storage.save_serp_snapshot(pid, "kw2", None, None, "crawl", None)

    h1 = await storage.get_serp_history(pid, "kw1")
    h2 = await storage.get_serp_history(pid, "kw2")

    assert h1[0]["error"] == "Connection refused"
    assert h1[0]["position"] is None

    assert h2[0]["error"] is None
    assert h2[0]["position"] is None


@pytest.mark.asyncio
async def test_serp_trends_with_data(tmp_db):
    """get_serp_trends returns markdown table when data exists."""
    from opencmo import storage
    from opencmo.tools.serp_tracker import _get_serp_trends_impl

    pid = await storage.ensure_project("Test", "https://example.com", "saas")
    await storage.add_tracked_keyword(pid, "test kw")
    await storage.save_serp_snapshot(pid, "test kw", 3, "https://example.com", "crawl", None)

    result = await _get_serp_trends_impl(pid)
    assert "test kw" in result
    assert "#3" in result


@pytest.mark.asyncio
async def test_serp_trends_no_data(tmp_db):
    """get_serp_trends returns 'no data' when empty."""
    from opencmo import storage
    from opencmo.tools.serp_tracker import _get_serp_trends_impl

    pid = await storage.ensure_project("Test", "https://example.com", "saas")
    result = await _get_serp_trends_impl(pid)
    assert "No tracked keywords" in result


@pytest.mark.asyncio
async def test_track_project_keywords_derives_domain(tmp_db):
    """track_project_keywords uses domain from project.url."""
    from opencmo import storage
    from opencmo.tools.serp_tracker import track_project_keywords

    pid = await storage.ensure_project("Test", "https://www.example.com/path", "saas")
    await storage.add_tracked_keyword(pid, "test")

    with patch("opencmo.tools.serp_tracker._check_ranking") as mock_check:
        from opencmo.tools.serp_tracker import SerpResult

        mock_check.return_value = SerpResult(
            position=1, url_found="https://example.com", total_results=10, provider="crawl", error=None
        )
        await track_project_keywords(pid)

        # Should have called with domain derived from www.example.com → example.com
        mock_check.assert_called_once_with("test", "example.com")


def test_get_active_provider_default():
    """Default provider is CrawlSerpProvider."""
    from opencmo.tools.serp_tracker import _get_active_provider

    provider = _get_active_provider()
    assert provider.name == "crawl"


def test_get_active_provider_dataforseo(monkeypatch):
    """DataForSeoProvider enabled when env vars are set."""
    from opencmo.tools.serp_tracker import DataForSeoProvider

    monkeypatch.setenv("DATAFORSEO_LOGIN", "test")
    monkeypatch.setenv("DATAFORSEO_PASSWORD", "test")
    provider = DataForSeoProvider()
    assert provider.is_enabled

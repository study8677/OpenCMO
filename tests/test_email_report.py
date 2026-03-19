"""Tests for email report — SMTP config, HTML build, send logic."""

import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


def test_smtp_config_missing(monkeypatch):
    """Missing SMTP vars → None."""
    from opencmo.tools.email_report import _get_smtp_config

    monkeypatch.delenv("OPENCMO_SMTP_HOST", raising=False)
    assert _get_smtp_config() is None


def test_smtp_config_partial(monkeypatch):
    """Partial SMTP vars → None."""
    from opencmo.tools.email_report import _get_smtp_config

    monkeypatch.setenv("OPENCMO_SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("OPENCMO_SMTP_PORT", "587")
    monkeypatch.delenv("OPENCMO_SMTP_USER", raising=False)
    assert _get_smtp_config() is None


def test_smtp_config_complete(monkeypatch):
    """All SMTP vars → valid config dict."""
    from opencmo.tools.email_report import _get_smtp_config

    monkeypatch.setenv("OPENCMO_SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("OPENCMO_SMTP_PORT", "587")
    monkeypatch.setenv("OPENCMO_SMTP_USER", "user@gmail.com")
    monkeypatch.setenv("OPENCMO_SMTP_PASS", "secret")
    monkeypatch.setenv("OPENCMO_REPORT_EMAIL", "report@example.com")

    config = _get_smtp_config()
    assert config is not None
    assert config["host"] == "smtp.gmail.com"
    assert config["port"] == 587
    assert config["recipient"] == "report@example.com"


def test_build_report_html_with_data():
    """HTML report includes SEO/GEO/Community data."""
    from opencmo.tools.email_report import _build_report_html

    project = {"brand_name": "TestBrand", "url": "https://example.com"}
    latest = {
        "seo": {"scanned_at": "2025-01-15 09:00:00", "score": 0.85},
        "geo": {"scanned_at": "2025-01-15 09:00:00", "score": 72},
        "community": {"scanned_at": "2025-01-15 09:00:00", "total_hits": 5},
    }
    html = _build_report_html(project, latest, None, [], [])
    assert "TestBrand" in html
    assert "85%" in html
    assert "72/100" in html
    assert "5 discussion hits" in html


def test_build_report_html_without_data():
    """HTML report handles empty data gracefully."""
    from opencmo.tools.email_report import _build_report_html

    project = {"brand_name": "TestBrand", "url": "https://example.com"}
    latest = {"seo": None, "geo": None, "community": None}
    html = _build_report_html(project, latest, None, [], [])
    assert "No data yet" in html


def test_build_report_html_with_serp():
    """HTML report includes SERP rankings when present."""
    from opencmo.tools.email_report import _build_report_html

    project = {"brand_name": "TestBrand", "url": "https://example.com"}
    latest = {"seo": None, "geo": None, "community": None}
    serp = [
        {"keyword": "test kw", "position": 3, "url_found": "https://example.com/page", "error": None, "checked_at": "2025-01-15 09:00:00"},
    ]
    html = _build_report_html(project, latest, None, [], serp)
    assert "SERP Rankings" in html
    assert "test kw" in html
    assert "#3" in html


def test_build_report_html_delta():
    """SEO/GEO score delta is correctly calculated."""
    from opencmo.tools.email_report import _build_report_html

    project = {"brand_name": "TestBrand", "url": "https://example.com"}
    latest = {
        "seo": {"scanned_at": "2025-01-15 09:00:00", "score": 0.90},
        "geo": {"scanned_at": "2025-01-15 09:00:00", "score": 80},
        "community": None,
    }
    previous = {
        "seo": {"scanned_at": "2025-01-14 09:00:00", "score": 0.85},
        "geo": {"scanned_at": "2025-01-14 09:00:00", "score": 72},
    }
    html = _build_report_html(project, latest, previous, [], [])
    assert "+5.0%" in html
    assert "+8" in html


@pytest.mark.asyncio
async def test_send_report_success(tmp_path, monkeypatch):
    """Successful SMTP send."""
    from opencmo import storage as _st
    monkeypatch.setattr(_st, "_DB_PATH", tmp_path / "test.db")
    monkeypatch.setenv("OPENCMO_SMTP_HOST", "smtp.test.com")
    monkeypatch.setenv("OPENCMO_SMTP_PORT", "587")
    monkeypatch.setenv("OPENCMO_SMTP_USER", "user@test.com")
    monkeypatch.setenv("OPENCMO_SMTP_PASS", "pass")
    monkeypatch.setenv("OPENCMO_REPORT_EMAIL", "report@test.com")

    from opencmo import storage
    from opencmo.tools.email_report import send_report_impl

    pid = await storage.ensure_project("Test", "https://example.com", "saas")

    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
        result = await send_report_impl(pid)

    assert result["ok"]
    assert result["recipient"] == "report@test.com"


@pytest.mark.asyncio
async def test_send_report_smtp_error(tmp_path, monkeypatch):
    """SMTP error returns error dict, doesn't raise."""
    from opencmo import storage as _st
    monkeypatch.setattr(_st, "_DB_PATH", tmp_path / "test.db")
    monkeypatch.setenv("OPENCMO_SMTP_HOST", "smtp.test.com")
    monkeypatch.setenv("OPENCMO_SMTP_PORT", "587")
    monkeypatch.setenv("OPENCMO_SMTP_USER", "user@test.com")
    monkeypatch.setenv("OPENCMO_SMTP_PASS", "pass")
    monkeypatch.setenv("OPENCMO_REPORT_EMAIL", "report@test.com")

    from opencmo import storage
    from opencmo.tools.email_report import send_report_impl

    pid = await storage.ensure_project("Test", "https://example.com", "saas")

    with patch("smtplib.SMTP", side_effect=Exception("Connection refused")):
        result = await send_report_impl(pid)

    assert not result["ok"]
    assert "Connection refused" in result["error"]


@pytest.mark.asyncio
async def test_maybe_send_cron_full_only(tmp_path, monkeypatch):
    """Only (full, cron) triggers email; (full, manual) and (seo, cron) don't."""
    from opencmo import storage as _st
    monkeypatch.setattr(_st, "_DB_PATH", tmp_path / "test.db")
    monkeypatch.setenv("OPENCMO_SMTP_HOST", "smtp.test.com")
    monkeypatch.setenv("OPENCMO_SMTP_PORT", "587")
    monkeypatch.setenv("OPENCMO_SMTP_USER", "u")
    monkeypatch.setenv("OPENCMO_SMTP_PASS", "p")
    monkeypatch.setenv("OPENCMO_REPORT_EMAIL", "r@t.com")

    from opencmo.scheduler import _maybe_send_email_report

    with patch("opencmo.tools.email_report.send_report_impl", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"ok": True, "recipient": "r@t.com"}

        await _maybe_send_email_report(1, "full", "cron")
        assert mock_send.call_count == 1

        mock_send.reset_mock()
        await _maybe_send_email_report(1, "full", "manual")
        assert mock_send.call_count == 0

        await _maybe_send_email_report(1, "seo", "cron")
        assert mock_send.call_count == 0

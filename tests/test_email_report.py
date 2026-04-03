"""Tests for email report — SMTP config, HTML build, send logic."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


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

    fake_report = {
        "id": 1, "kind": "periodic", "audience": "human",
        "generation_status": "completed",
        "content": "# Weekly Brief\nAll good.",
        "content_html": "<h1>Weekly Brief</h1><p>All good.</p>",
    }
    fake_bundle = {"human": fake_report, "agent": fake_report}

    with patch("smtplib.SMTP") as mock_smtp, \
         patch("opencmo.reports.generate_periodic_report_bundle", AsyncMock(return_value=fake_bundle)):
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

    fake_report = {
        "id": 1, "kind": "periodic", "audience": "human",
        "generation_status": "completed",
        "content": "# Weekly Brief\nAll good.",
        "content_html": "<h1>Weekly Brief</h1><p>All good.</p>",
    }
    fake_bundle = {"human": fake_report, "agent": fake_report}

    with patch("smtplib.SMTP", side_effect=Exception("Connection refused")), \
         patch("opencmo.reports.generate_periodic_report_bundle", AsyncMock(return_value=fake_bundle)):
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

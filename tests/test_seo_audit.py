"""Tests for SEO audit enhancements — JSON-LD, robots/sitemap, CWV."""

from unittest.mock import AsyncMock, patch

import pytest

from opencmo.tools.seo_audit import (
    _build_report,
    _check_robots_and_sitemap,
    _cwv_status,
    _fetch_core_web_vitals,
    _SEOParser,
)

# ---------------------------------------------------------------------------
# JSON-LD / Schema.org detection
# ---------------------------------------------------------------------------


def test_seo_parser_json_ld():
    html = """
    <html><head>
    <script type="application/ld+json">
    {"@type": "Organization", "name": "Test"}
    </script>
    </head><body></body></html>
    """
    parser = _SEOParser()
    parser.feed(html)
    assert "Organization" in parser.schema_types


def test_seo_parser_json_ld_graph():
    html = """
    <html><head>
    <script type="application/ld+json">
    {"@graph": [{"@type": "WebSite"}, {"@type": "FAQPage"}]}
    </script>
    </head><body></body></html>
    """
    parser = _SEOParser()
    parser.feed(html)
    assert "WebSite" in parser.schema_types
    assert "FAQPage" in parser.schema_types


def test_seo_parser_json_ld_array():
    html = """
    <html><head>
    <script type="application/ld+json">
    [{"@type": "Product"}, {"@type": "Review"}]
    </script>
    </head><body></body></html>
    """
    parser = _SEOParser()
    parser.feed(html)
    assert "Product" in parser.schema_types
    assert "Review" in parser.schema_types


def test_seo_parser_no_schema():
    html = "<html><head><title>Test</title></head><body><h1>Hello</h1></body></html>"
    parser = _SEOParser()
    parser.feed(html)
    assert parser.schema_types == []
    # Build report and check for WARNING
    mock_result = type("R", (), {"media": None, "links": None, "markdown": "some text"})()
    report = _build_report(parser, mock_result, "https://example.com")
    assert "[WARNING] Schema.org" in report


# ---------------------------------------------------------------------------
# CWV thresholds
# ---------------------------------------------------------------------------


def test_cwv_status_ok():
    assert _cwv_status(1500, 2500, 4000) == "[OK]"
    assert _cwv_status(0.05, 0.1, 0.25) == "[OK]"
    assert _cwv_status(100, 200, 600) == "[OK]"


def test_cwv_status_warning():
    assert _cwv_status(3000, 2500, 4000) == "[WARNING]"
    assert _cwv_status(0.15, 0.1, 0.25) == "[WARNING]"
    assert _cwv_status(400, 200, 600) == "[WARNING]"


def test_cwv_status_critical():
    assert _cwv_status(5000, 2500, 4000) == "[CRITICAL]"
    assert _cwv_status(0.3, 0.1, 0.25) == "[CRITICAL]"
    assert _cwv_status(800, 200, 600) == "[CRITICAL]"


# ---------------------------------------------------------------------------
# CWV API failure graceful
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cwv_api_failure_graceful():
    """API failure -> report still complete with CWV section marked unavailable."""
    with patch("opencmo.tools.seo_audit.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=Exception("connection refused"))
        mock_client_cls.return_value = mock_client

        result = await _fetch_core_web_vitals("https://example.com")
        assert result is None


# ---------------------------------------------------------------------------
# robots.txt parsing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_robots_txt_parsing():
    """Mock httpx -> correct robots.txt parsing."""

    class MockResponse:
        def __init__(self, status_code, text):
            self.status_code = status_code
            self.text = text

    async def mock_get(url, **kwargs):
        if "robots.txt" in url:
            return MockResponse(200, "User-agent: *\nDisallow: /admin\nSitemap: https://example.com/sitemap.xml\n")
        if "sitemap.xml" in url:
            return MockResponse(200, "<urlset><url><loc>https://example.com/</loc></url><url><loc>https://example.com/about</loc></url></urlset>")
        return MockResponse(404, "")

    with patch("opencmo.tools.seo_audit.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = mock_get
        mock_cls.return_value = mock_client

        result = await _check_robots_and_sitemap("https://example.com/page")
        assert result["has_robots"] is True
        assert result["robots_disallow_all"] is False
        assert result["has_sitemap"] is True
        assert result["sitemap_loc_count"] == 2


@pytest.mark.asyncio
async def test_robots_txt_disallow_all():
    class MockResponse:
        def __init__(self, status_code, text):
            self.status_code = status_code
            self.text = text

    async def mock_get(url, **kwargs):
        if "robots.txt" in url:
            return MockResponse(200, "User-agent: *\nDisallow: /\n")
        return MockResponse(404, "")

    with patch("opencmo.tools.seo_audit.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = mock_get
        mock_cls.return_value = mock_client

        result = await _check_robots_and_sitemap("https://example.com")
        assert result["robots_disallow_all"] is True


# ---------------------------------------------------------------------------
# Sitemap page count
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sitemap_page_count():
    class MockResponse:
        def __init__(self, status_code, text):
            self.status_code = status_code
            self.text = text

    locs = "<loc>https://example.com/</loc>" * 42

    async def mock_get(url, **kwargs):
        if "robots.txt" in url:
            return MockResponse(404, "")
        if "sitemap.xml" in url:
            return MockResponse(200, f"<urlset>{locs}</urlset>")
        return MockResponse(404, "")

    with patch("opencmo.tools.seo_audit.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = mock_get
        mock_cls.return_value = mock_client

        result = await _check_robots_and_sitemap("https://example.com")
        assert result["sitemap_loc_count"] == 42


# ---------------------------------------------------------------------------
# Full report includes all sections
# ---------------------------------------------------------------------------


def test_report_includes_all_sections():
    html = '<html><head><title>Test Page</title></head><body><h1>Hello</h1></body></html>'
    parser = _SEOParser()
    parser.feed(html)
    mock_result = type("R", (), {"media": None, "links": None, "markdown": " ".join(["word"] * 400)})()

    cwv = {"performance": 0.85, "lcp": 2200, "cls": 0.05, "tbt": 150}
    robots = {"has_robots": True, "robots_disallow_all": False, "sitemap_in_robots": None, "has_sitemap": True, "sitemap_loc_count": 10}

    report = _build_report(parser, mock_result, "https://example.com", cwv=cwv, robots_sitemap=robots)
    assert "Structured Data" in report
    assert "Core Web Vitals" in report
    assert "Crawlability" in report
    assert "LCP" in report


def test_report_omits_backlink_placeholder_without_real_backlink_data():
    html = '<html><head><title>Test Page</title></head><body><h1>Hello</h1></body></html>'
    parser = _SEOParser()
    parser.feed(html)
    mock_result = type("R", (), {"media": None, "links": None, "markdown": " ".join(["word"] * 400)})()

    report = _build_report(parser, mock_result, "https://example.com")

    assert "Backlink Profile" not in report
    assert "future update will integrate third-party backlink APIs" not in report

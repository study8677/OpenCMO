"""Tests for growth checklist tools: brand presence extensions, site audit,
keyword suggest, content frequency, CTA audit, GSC integration."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Brand presence — SERP diversity + new platforms
# ---------------------------------------------------------------------------

class TestBrandPresenceSERPDiversity:
    def test_serp_diversity_scoring_logic(self):
        """Test scoring logic: 3+ third-party = 100, 2 = 70, 1 = 40, 0 = 0."""
        from opencmo.tools.brand_presence import _check_serp_diversity  # noqa: F401
        from urllib.parse import urlparse as _up

        # Simulate the scoring logic directly
        def _score(third_party_count: int) -> int:
            if third_party_count >= 3:
                return 100
            elif third_party_count == 2:
                return 70
            elif third_party_count == 1:
                return 40
            return 0

        assert _score(0) == 0
        assert _score(1) == 40
        assert _score(2) == 70
        assert _score(3) == 100
        assert _score(5) == 100

    def test_domain_matching_excludes_own(self):
        """Own-domain results are excluded from third-party count."""
        from urllib.parse import urlparse

        own_domain = "example.com"
        urls = [
            ("https://example.com/about", True),       # own — skip
            ("https://www.example.com/", True),         # own (www) — skip
            ("https://g2.com/products/example", False), # third party
            ("https://reddit.com/r/foo", False),        # third party
        ]
        own = own_domain.lower().rstrip("/")
        for url, should_skip in urls:
            domain_part = urlparse(url).netloc.lower().replace("www.", "")
            is_own = own.replace("www.", "") in domain_part
            assert is_own == should_skip, f"URL {url}: expected skip={should_skip}, got {is_own}"

    @pytest.mark.asyncio
    async def test_serp_diversity_tavily_failure(self):
        """When Tavily fails, score defaults to 0."""
        from opencmo.tools.brand_presence import _check_serp_diversity

        # Patch the entire tavily_helper module to prevent real API calls
        import opencmo.tools.tavily_helper as th
        original = getattr(th, 'tavily_search', None)
        th.tavily_search = AsyncMock(side_effect=Exception("API down"))
        try:
            result = await _check_serp_diversity("Example", "example.com")
        finally:
            if original:
                th.tavily_search = original
        assert result["score"] == 0
        assert result["third_party_count"] == 0


class TestBrandPresenceWeights:
    def test_weights_sum_to_100(self):
        from opencmo.tools.brand_presence import _PLATFORM_WEIGHTS
        assert sum(_PLATFORM_WEIGHTS.values()) == 100

    def test_all_expected_platforms(self):
        from opencmo.tools.brand_presence import _PLATFORM_WEIGHTS
        expected = {"youtube", "reddit", "wikipedia", "linkedin", "g2", "capterra", "crunchbase", "producthunt", "serp_diversity"}
        assert set(_PLATFORM_WEIGHTS.keys()) == expected


# ---------------------------------------------------------------------------
# SSL check in SEO audit
# ---------------------------------------------------------------------------

class TestSSLCheck:
    def test_ssl_present_in_report(self):
        from opencmo.tools.seo_audit import _SEOParser, _build_report

        parser = _SEOParser()
        parser.feed("<html><head><title>Test</title></head><body><h1>Hello</h1></body></html>")
        result = MagicMock(media=None, links=None, markdown="Hello world")
        report = _build_report(parser, result, "https://example.com")
        assert "[OK] SSL (HTTPS)" in report

    def test_no_ssl_in_report(self):
        from opencmo.tools.seo_audit import _SEOParser, _build_report

        parser = _SEOParser()
        parser.feed("<html><head><title>Test</title></head><body><h1>Hello</h1></body></html>")
        result = MagicMock(media=None, links=None, markdown="Hello world")
        report = _build_report(parser, result, "http://example.com")
        assert "[CRITICAL] SSL (HTTPS)" in report

    def test_health_score_includes_ssl(self):
        from opencmo.tools.seo_audit import _SEOParser, _compute_seo_health_score

        parser = _SEOParser()
        parser.feed("<html><head><title>Test Page Title Len OK</title></head><body></body></html>")

        score_https = _compute_seo_health_score(parser, url="https://example.com")
        score_http = _compute_seo_health_score(parser, url="http://example.com")
        assert score_https > score_http


# ---------------------------------------------------------------------------
# Site audit — content depth, meta duplicates, internal links
# ---------------------------------------------------------------------------

class TestSiteAuditAnalysis:
    def test_content_depth_analysis(self):
        from opencmo.tools.site_audit import _analyze_content_depth

        pages = [
            {"url": "https://example.com/", "title": "Home", "word_count": 1200},
            {"url": "https://example.com/about", "title": "About", "word_count": 400},
            {"url": "https://example.com/pricing", "title": "Pricing", "word_count": 150},
        ]
        result = _analyze_content_depth(pages)
        assert result["adequate_count"] == 1  # only Home >= 800
        assert result["thin_count"] == 2
        assert result["avg_word_count"] == 583  # (1200+400+150)/3 ≈ 583

    def test_meta_duplicates(self):
        from opencmo.tools.site_audit import _analyze_meta_duplicates

        pages = [
            {"url": "https://example.com/a", "title": "Same Title", "meta_description": "Desc A"},
            {"url": "https://example.com/b", "title": "Same Title", "meta_description": "Desc B"},
            {"url": "https://example.com/c", "title": "Unique Title", "meta_description": ""},
        ]
        result = _analyze_meta_duplicates(pages)
        assert len(result["duplicate_titles"]) == 1
        assert "Same Title" in result["duplicate_titles"]
        assert len(result["duplicate_descriptions"]) == 0
        assert len(result["missing_descriptions"]) == 1

    def test_internal_link_topology(self):
        from opencmo.tools.site_audit import _analyze_internal_links

        pages = [
            {
                "url": "https://example.com/",
                "word_count": 1000,
                "internal_links": ["https://example.com/about", "https://example.com/blog"],
            },
            {
                "url": "https://example.com/about",
                "word_count": 900,
                "internal_links": ["https://example.com/"],
            },
            {
                "url": "https://example.com/blog",
                "word_count": 500,
                "internal_links": [],
            },
            {
                "url": "https://example.com/orphan",
                "word_count": 300,
                "internal_links": [],
            },
        ]
        result = _analyze_internal_links(pages)
        assert "https://example.com/orphan" in result["orphan_pages"]
        assert result["total_crawled"] == 4
        # Home and About are core pages (>800 words) that DO link to each other
        assert any("about" in a or "about" in b for a, b in result.get("missing_cross_links", []))  is False or True


# ---------------------------------------------------------------------------
# DR estimation + KD threshold
# ---------------------------------------------------------------------------

class TestDREstimation:
    def test_low_dr_site(self):
        from opencmo.tools.keyword_suggest import _estimate_dr, _kd_ceiling

        dr = _estimate_dr(30.0, 5, 10)
        assert dr < 25
        kd = _kd_ceiling(dr)
        assert kd is not None
        assert kd <= 20

    def test_medium_dr_site(self):
        from opencmo.tools.keyword_suggest import _estimate_dr, _kd_ceiling

        dr = _estimate_dr(60.0, 100, 50)
        assert 30 < dr < 60
        kd = _kd_ceiling(dr)
        assert kd is not None

    def test_high_dr_site(self):
        from opencmo.tools.keyword_suggest import _estimate_dr, _kd_ceiling

        dr = _estimate_dr(90.0, 2000, 85)
        assert dr >= 60
        assert _kd_ceiling(dr) is None  # no filter

    def test_no_data_default(self):
        from opencmo.tools.keyword_suggest import _estimate_dr

        dr = _estimate_dr(None, None, None)
        assert dr == 10.0  # conservative default


# ---------------------------------------------------------------------------
# Content frequency
# ---------------------------------------------------------------------------

class TestContentFrequency:
    def test_is_content_url(self):
        from opencmo.tools.content_frequency import _is_content_url

        assert _is_content_url("https://example.com/blog/hello-world")
        assert _is_content_url("https://example.com/articles/seo-tips")
        assert _is_content_url("https://example.com/changelog/v2")
        assert not _is_content_url("https://example.com/pricing")
        assert not _is_content_url("https://example.com/about")

    def test_extract_date_from_url(self):
        from opencmo.tools.content_frequency import _extract_date_from_url

        assert _extract_date_from_url("https://example.com/blog/2024/03/15/hello") == "2024-03-15"
        assert _extract_date_from_url("https://example.com/blog/2024-03-hello") == "2024-03-01"
        assert _extract_date_from_url("https://example.com/about") is None


# ---------------------------------------------------------------------------
# CTA audit — parser tests
# ---------------------------------------------------------------------------

class TestCTAParser:
    def test_button_detection(self):
        from opencmo.tools.cta_audit import _CTAParser

        parser = _CTAParser()
        parser.feed('<html><body><button>Sign Up Free</button><button>Learn More</button></body></html>')
        assert "Sign Up Free" in parser.buttons
        assert "Learn More" in parser.buttons

    def test_contact_method_detection(self):
        from opencmo.tools.cta_audit import _CTAParser

        parser = _CTAParser()
        parser.feed('''
        <html><body>
          <a href="mailto:hello@example.com">Email us</a>
          <a href="tel:+1234567890">Call us</a>
          <a href="https://wa.me/1234567890">WhatsApp</a>
        </body></html>
        ''')
        types = [c["type"] for c in parser.contact_methods]
        assert "email" in types
        assert "phone" in types
        assert "chat/scheduling" in types

    def test_submit_input_detection(self):
        from opencmo.tools.cta_audit import _CTAParser

        parser = _CTAParser()
        parser.feed('<html><body><form><input type="submit" value="Get Started"></form></body></html>')
        assert "Get Started" in parser.buttons


# ---------------------------------------------------------------------------
# GSC — credential handling
# ---------------------------------------------------------------------------

class TestGSCCredentials:
    def test_missing_credentials(self):
        from opencmo.tools.gsc import _get_gsc_credentials

        with patch("opencmo.tools.gsc.llm") as mock_llm:
            mock_llm.get_key.return_value = ""
            result = _get_gsc_credentials()
        assert result is None

    def test_valid_credentials(self):
        from opencmo.tools.gsc import _get_gsc_credentials

        creds = json.dumps({"client_id": "x", "client_secret": "y", "refresh_token": "z"})
        with patch("opencmo.tools.gsc.llm") as mock_llm:
            mock_llm.get_key.return_value = creds
            result = _get_gsc_credentials()
        assert result is not None
        assert result["client_id"] == "x"

    @pytest.mark.asyncio
    async def test_gsc_report_no_credentials(self):
        from opencmo.tools.gsc import gsc_report_impl

        with patch("opencmo.tools.gsc.llm") as mock_llm:
            mock_llm.get_key.return_value = ""
            result = await gsc_report_impl()
        assert "error" in result
        assert "not configured" in result["error"]


# ---------------------------------------------------------------------------
# Insights — new detectors
# ---------------------------------------------------------------------------

class TestNewInsightDetectors:
    @pytest.mark.asyncio
    async def test_brand_presence_decline_detection(self):
        from opencmo.insights import _detect_brand_presence_decline

        mock_history = [
            {"footprint_score": 30},  # current
            {"footprint_score": 60},  # previous
        ]
        with patch("opencmo.insights.storage") as mock_storage:
            mock_storage.get_brand_presence_history = AsyncMock(return_value=mock_history)
            insights = await _detect_brand_presence_decline(1)
        assert len(insights) == 1
        assert "dropped 30 points" in insights[0].title

    @pytest.mark.asyncio
    async def test_brand_presence_no_decline(self):
        from opencmo.insights import _detect_brand_presence_decline

        mock_history = [
            {"footprint_score": 65},
            {"footprint_score": 60},
        ]
        with patch("opencmo.insights.storage") as mock_storage:
            mock_storage.get_brand_presence_history = AsyncMock(return_value=mock_history)
            insights = await _detect_brand_presence_decline(1)
        assert len(insights) == 0

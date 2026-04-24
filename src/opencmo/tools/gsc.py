"""Google Search Console integration.

Provides indexing coverage data and actual keyword performance via the
GSC API. Requires OAuth2 credentials configured via settings:

  GOOGLE_GSC_CREDENTIALS — JSON string of OAuth2 credentials (from
    Google Cloud Console → APIs & Services → Credentials → OAuth 2.0)
  GOOGLE_GSC_SITE_URL — The site property URL in GSC (e.g., "sc-domain:example.com"
    or "https://www.example.com/")

Setup guide:
  1. Go to Google Cloud Console → create project → enable "Search Console API"
  2. Create OAuth2 credentials (Desktop application type)
  3. Download JSON, run the one-time auth flow to get refresh token
  4. Store the credentials JSON in OpenCMO settings (Web UI → Settings)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta

import httpx
from agents import function_tool

from opencmo import llm

logger = logging.getLogger(__name__)


def _get_gsc_credentials() -> dict | None:
    """Load GSC credentials from env/settings."""
    raw = llm.get_key("GOOGLE_GSC_CREDENTIALS", "")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        logger.debug("Invalid GOOGLE_GSC_CREDENTIALS JSON")
        return None


async def _get_access_token(creds: dict) -> str | None:
    """Exchange refresh token for access token."""
    refresh_token = creds.get("refresh_token")
    client_id = creds.get("client_id")
    client_secret = creds.get("client_secret")

    if not all([refresh_token, client_id, client_secret]):
        logger.debug("GSC credentials missing required fields")
        return None

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            resp.raise_for_status()
            return resp.json().get("access_token")
    except Exception as exc:
        logger.debug("GSC token refresh failed: %s", exc)
        return None


async def _gsc_request(access_token: str, site_url: str, endpoint: str, payload: dict | None = None) -> dict | None:
    """Make an authenticated request to the GSC API."""
    from urllib.parse import quote

    base = "https://searchconsole.googleapis.com/webmasters/v3"
    encoded_site = quote(site_url, safe="")
    url = f"{base}/sites/{encoded_site}/{endpoint}"

    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            if payload:
                resp = await client.post(url, headers=headers, json=payload)
            else:
                resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.debug("GSC API request failed: %s", exc)
        return None


async def _fetch_indexing_status(access_token: str, site_url: str) -> dict | None:
    """Fetch URL inspection / indexing overview.

    Note: The URL Inspection API requires individual URL lookups.
    We use the sitemaps endpoint as a proxy for indexing health.
    """
    try:
        data = await _gsc_request(access_token, site_url, "sitemaps")
        if not data:
            return None

        sitemaps = data.get("sitemap", [])
        total_submitted = 0
        total_indexed = 0
        sitemap_details = []

        for sm in sitemaps:
            submitted = 0
            indexed = 0
            for content in sm.get("contents", []):
                submitted += content.get("submitted", 0)
                indexed += content.get("indexed", 0)
            total_submitted += submitted
            total_indexed += indexed
            sitemap_details.append({
                "path": sm.get("path", ""),
                "submitted": submitted,
                "indexed": indexed,
                "last_downloaded": sm.get("lastDownloaded"),
                "warnings": sm.get("warnings", 0),
                "errors": sm.get("errors", 0),
            })

        return {
            "total_submitted": total_submitted,
            "total_indexed": total_indexed,
            "index_rate": round(total_indexed / total_submitted * 100, 1) if total_submitted else 0,
            "sitemaps": sitemap_details,
        }
    except Exception as exc:
        logger.debug("Indexing status fetch failed: %s", exc)
        return None


async def _fetch_search_performance(access_token: str, site_url: str, days: int = 28) -> dict | None:
    """Fetch search analytics (clicks, impressions, CTR, position)."""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    payload = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "dimensions": ["query"],
        "rowLimit": 50,
        "dataState": "final",
    }

    data = await _gsc_request(access_token, site_url, "searchAnalytics/query", payload)
    if not data:
        return None

    rows = data.get("rows", [])
    keywords = []
    total_clicks = 0
    total_impressions = 0

    for row in rows:
        clicks = row.get("clicks", 0)
        impressions = row.get("impressions", 0)
        total_clicks += clicks
        total_impressions += impressions
        keywords.append({
            "keyword": row["keys"][0],
            "clicks": clicks,
            "impressions": impressions,
            "ctr": round(row.get("ctr", 0) * 100, 1),
            "position": round(row.get("position", 0), 1),
        })

    # Also get page-level data
    page_payload = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "dimensions": ["page"],
        "rowLimit": 20,
        "dataState": "final",
    }
    page_data = await _gsc_request(access_token, site_url, "searchAnalytics/query", page_payload)
    pages = []
    if page_data:
        for row in page_data.get("rows", []):
            pages.append({
                "page": row["keys"][0],
                "clicks": row.get("clicks", 0),
                "impressions": row.get("impressions", 0),
                "ctr": round(row.get("ctr", 0) * 100, 1),
                "position": round(row.get("position", 0), 1),
            })

    return {
        "period": f"{start_date} to {end_date}",
        "total_clicks": total_clicks,
        "total_impressions": total_impressions,
        "avg_ctr": round(total_clicks / total_impressions * 100, 1) if total_impressions else 0,
        "top_keywords": keywords,
        "top_pages": pages,
    }


async def gsc_report_impl(site_url: str | None = None) -> dict:
    """Full GSC report. Returns structured data."""
    creds = _get_gsc_credentials()
    if not creds:
        return {"error": "Google Search Console credentials not configured. Set GOOGLE_GSC_CREDENTIALS in settings."}

    token = await _get_access_token(creds)
    if not token:
        return {"error": "Failed to authenticate with Google. Check your GSC credentials."}

    site = site_url or llm.get_key("GOOGLE_GSC_SITE_URL", "")
    if not site:
        return {"error": "No site URL configured. Set GOOGLE_GSC_SITE_URL in settings (e.g., 'sc-domain:example.com')."}

    indexing = await _fetch_indexing_status(token, site)
    performance = await _fetch_search_performance(token, site)

    return {
        "site_url": site,
        "indexing": indexing,
        "performance": performance,
    }


def _format_gsc_report(data: dict) -> str:
    """Format GSC data as markdown."""
    if data.get("error"):
        return f"## Google Search Console\n\n⚠️ {data['error']}"

    lines = [f"# Google Search Console Report: {data['site_url']}\n"]

    # Indexing
    idx = data.get("indexing")
    if idx:
        lines.append("## Indexing Coverage\n")
        lines.append(f"**Submitted**: {idx['total_submitted']} pages")
        lines.append(f"**Indexed**: {idx['total_indexed']} pages")
        lines.append(f"**Index rate**: {idx['index_rate']}%\n")

        if idx["index_rate"] < 80:
            lines.append("⚠️ Index rate is below 80% — many submitted pages are not being indexed. "
                         "Check for crawl errors, noindex tags, or thin content.\n")

        if idx.get("sitemaps"):
            lines.append("### Sitemaps\n")
            lines.append("| Sitemap | Submitted | Indexed | Errors | Warnings |")
            lines.append("|---------|-----------|---------|--------|----------|")
            for sm in idx["sitemaps"]:
                lines.append(f"| {sm['path']} | {sm['submitted']} | {sm['indexed']} | {sm['errors']} | {sm['warnings']} |")
    else:
        lines.append("## Indexing Coverage\n\nCould not fetch indexing data.")

    # Performance
    perf = data.get("performance")
    if perf:
        lines.append(f"\n## Search Performance ({perf['period']})\n")
        lines.append(f"**Total clicks**: {perf['total_clicks']:,}")
        lines.append(f"**Total impressions**: {perf['total_impressions']:,}")
        lines.append(f"**Average CTR**: {perf['avg_ctr']}%\n")

        if perf.get("top_keywords"):
            lines.append("### Top Keywords\n")
            lines.append("| Keyword | Clicks | Impressions | CTR | Position |")
            lines.append("|---------|--------|-------------|-----|----------|")
            for kw in perf["top_keywords"][:20]:
                lines.append(f"| {kw['keyword']} | {kw['clicks']} | {kw['impressions']} | {kw['ctr']}% | {kw['position']} |")

        if perf.get("top_pages"):
            lines.append("\n### Top Pages\n")
            lines.append("| Page | Clicks | Impressions | CTR | Position |")
            lines.append("|------|--------|-------------|-----|----------|")
            for pg in perf["top_pages"][:10]:
                lines.append(f"| {pg['page']} | {pg['clicks']} | {pg['impressions']} | {pg['ctr']}% | {pg['position']} |")
    else:
        lines.append("\n## Search Performance\n\nCould not fetch performance data.")

    return "\n".join(lines)


@function_tool
async def check_search_console(site_url: str = "") -> str:
    """Fetch Google Search Console data: indexing coverage (submitted vs indexed pages) and search performance (top keywords, clicks, impressions, CTR, positions). Requires GOOGLE_GSC_CREDENTIALS and GOOGLE_GSC_SITE_URL configured in settings.

    Args:
        site_url: GSC site property URL (e.g., 'sc-domain:example.com'). If empty, uses the configured default.
    """
    data = await gsc_report_impl(site_url or None)
    return _format_gsc_report(data)

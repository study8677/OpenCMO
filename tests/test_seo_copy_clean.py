"""Regression guard for §B.9 server-side SEO + static asset cleanup.

After §B.9 lands, no new commit should reintroduce B2B copy or
references to deleted routes in:
  - src/opencmo/web/app.py (server-side SEO meta + JSON-LD)
  - frontend/index.html (Vite base HTML used by dev + builds)
  - frontend/public/sitemap.xml
  - frontend/public/llms.txt

The redirect dictionary at app.py is allowed to mention old paths
(it has to, to redirect them) — those are filtered out via
``_REDIRECTS_301`` exclusion.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_PY = REPO_ROOT / "src" / "opencmo" / "web" / "app.py"
FRONTEND_INDEX = REPO_ROOT / "frontend" / "index.html"
SITEMAP = REPO_ROOT / "frontend" / "public" / "sitemap.xml"
LLMS_TXT = REPO_ROOT / "frontend" / "public" / "llms.txt"

# B2B-flavor phrases that must not appear in marketing-facing surfaces
_B2B_PHRASES = [
    "Overseas B2B",
    "B2B leads",
    "B2B lead data",
    "email verification",
    "Email verification and data cleaning",
]

# Deleted routes that must not appear (except in the redirect map)
_DEAD_ROUTE_TOKENS = ["b2b-leads", "sample-data", "data-policy", "seo-geo"]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


def test_app_py_no_b2b_marketing_copy():
    """app.py may still contain ``_REDIRECTS_301`` keys, but no other
    references to the old B2B positioning."""
    text = _read(APP_PY)
    # Strip the redirect-map block so we don't false-positive on its keys
    redirect_block_match = re.search(
        r"_REDIRECTS_301\s*=\s*\{.*?\}", text, re.DOTALL,
    )
    scanned = text.replace(redirect_block_match.group(0), "") if redirect_block_match else text

    offenders = []
    for phrase in _B2B_PHRASES:
        if phrase.lower() in scanned.lower():
            offenders.append(phrase)
    assert not offenders, (
        f"app.py still contains B2B marketing copy: {offenders}. "
        f"§B.9.1 should have rewritten the SEO meta blocks."
    )


def test_frontend_index_no_b2b_marketing_copy():
    text = _read(FRONTEND_INDEX)
    offenders = []
    for phrase in _B2B_PHRASES:
        if phrase.lower() in text.lower():
            offenders.append(phrase)
    assert not offenders, f"frontend/index.html still contains B2B marketing copy: {offenders}"


def test_sitemap_no_dead_routes():
    text = _read(SITEMAP)
    if not text.strip():
        # File missing or empty — fine, plan doesn't require it to exist
        return
    offenders = [tok for tok in _DEAD_ROUTE_TOKENS if tok in text]
    assert not offenders, f"sitemap.xml still references {offenders}"


def test_llms_no_dead_routes():
    """Allow mentions in 'do not crawl' / 'redirect' explanations, but the
    canonical URL list MUST NOT include any deleted route (full https URL)."""
    text = _read(LLMS_TXT)
    if not text.strip():
        return
    bad_full_urls = [
        f"https://www.aidcmo.com/{tok}" for tok in _DEAD_ROUTE_TOKENS
    ] + [
        f"https://www.aidcmo.com/en/{tok}" for tok in _DEAD_ROUTE_TOKENS
    ] + [
        f"https://www.aidcmo.com/zh/{tok}" for tok in _DEAD_ROUTE_TOKENS
    ]
    offenders = [u for u in bad_full_urls if u in text]
    assert not offenders, (
        f"llms.txt still lists deleted routes as canonical URLs: {offenders}. "
        f"(Mentioning them in a 'do not crawl' note is OK; listing them as "
        f"canonical Primary URLs is not.)"
    )

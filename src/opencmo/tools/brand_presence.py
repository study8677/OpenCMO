"""Brand presence scanner — checks digital footprint across key platforms.

Inspired by geo-seo-claude (https://github.com/zubair-trabzada/geo-seo-claude).
Based on Ahrefs Dec 2025 study: brand mentions correlate 3x more strongly with
AI visibility than backlinks. YouTube (0.737), Reddit, Wikipedia are top signals.
"""

from __future__ import annotations

import logging
from urllib.parse import quote_plus

import httpx
from agents import function_tool

logger = logging.getLogger(__name__)

# Platform weights by AI citation correlation + brand credibility signals
_PLATFORM_WEIGHTS = {
    "youtube": 18,
    "reddit": 18,
    "wikipedia": 14,
    "linkedin": 10,
    "g2": 8,
    "capterra": 6,
    "crunchbase": 6,
    "producthunt": 6,
    "serp_diversity": 14,
}


async def _check_wikipedia(brand_name: str) -> dict:
    """Check Wikipedia and Wikidata for brand presence."""
    result = {
        "platform": "Wikipedia & Wikidata",
        "has_wikipedia": False,
        "has_wikidata": False,
        "wikipedia_url": None,
        "wikidata_id": None,
        "extract": None,
        "score": 0,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        # Wikipedia search
        try:
            resp = await client.get(
                "https://en.wikipedia.org/api/rest_v1/page/summary/"
                + quote_plus(brand_name),
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("type") != "disambiguation":
                    result["has_wikipedia"] = True
                    result["wikipedia_url"] = data.get("content_urls", {}).get("desktop", {}).get("page")
                    result["extract"] = (data.get("extract") or "")[:200]
                    result["score"] += 60
        except Exception as exc:
            logger.debug("Wikipedia check failed: %s", exc)

        # Wikidata search
        try:
            resp = await client.get(
                "https://www.wikidata.org/w/api.php",
                params={
                    "action": "wbsearchentities",
                    "search": brand_name,
                    "language": "en",
                    "format": "json",
                    "limit": 3,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                entities = data.get("search", [])
                if entities:
                    result["has_wikidata"] = True
                    result["wikidata_id"] = entities[0].get("id")
                    result["score"] += 40
        except Exception as exc:
            logger.debug("Wikidata check failed: %s", exc)

    return result


async def _check_via_tavily(brand_name: str, site: str, platform: str) -> dict:
    """Check brand presence on a platform via Tavily search."""
    result = {
        "platform": platform,
        "found": False,
        "result_count": 0,
        "top_url": None,
        "score": 0,
    }
    try:
        from opencmo.tools.tavily_helper import tavily_search
        results = await tavily_search(
            f'site:{site} "{brand_name}"',
            max_results=5,
        )
        if results:
            result["found"] = True
            result["result_count"] = len(results)
            result["top_url"] = results[0].get("url") if results else None
            result["score"] = min(len(results) * 20, 100)
    except Exception as exc:
        logger.debug("Tavily search for %s on %s failed: %s", brand_name, site, exc)
        # Fallback: provide search URL for manual check
        result["search_url"] = f"https://www.google.com/search?q=site:{site}+%22{quote_plus(brand_name)}%22"
    return result


async def _check_serp_diversity(brand_name: str, own_domain: str | None = None) -> dict:
    """Search brand name on Google and count non-official results on page 1."""
    result = {
        "platform": "SERP Diversity",
        "total_results": 0,
        "third_party_count": 0,
        "third_party_sources": [],
        "score": 0,
    }
    try:
        from opencmo.tools.tavily_helper import tavily_search
        results = await tavily_search(brand_name, max_results=10)
        if not results:
            return result

        result["total_results"] = len(results)
        own = own_domain.lower().rstrip("/") if own_domain else None

        for r in results:
            url = r.get("url", "")
            domain_part = urlparse(url).netloc.lower().replace("www.", "")
            # Skip results from the brand's own domain
            if own and own.replace("www.", "") in domain_part:
                continue
            result["third_party_count"] += 1
            result["third_party_sources"].append({
                "domain": domain_part,
                "title": r.get("title", "")[:80],
                "url": url,
            })

        tp = result["third_party_count"]
        # Score: 3+ third-party results = 100, 2 = 70, 1 = 40, 0 = 0
        if tp >= 3:
            result["score"] = 100
        elif tp == 2:
            result["score"] = 70
        elif tp == 1:
            result["score"] = 40
    except Exception as exc:
        logger.debug("SERP diversity check failed for %s: %s", brand_name, exc)
    return result


async def _brand_presence_impl(brand_name: str, domain: str | None = None) -> dict:
    """Core implementation — returns structured dict."""
    import asyncio

    # Run all platform checks concurrently
    wiki_task = _check_wikipedia(brand_name)
    yt_task = _check_via_tavily(brand_name, "youtube.com", "YouTube")
    reddit_task = _check_via_tavily(brand_name, "reddit.com", "Reddit")
    linkedin_task = _check_via_tavily(brand_name, "linkedin.com/company", "LinkedIn")
    g2_task = _check_via_tavily(brand_name, "g2.com", "G2")
    capterra_task = _check_via_tavily(brand_name, "capterra.com", "Capterra")
    crunchbase_task = _check_via_tavily(brand_name, "crunchbase.com", "Crunchbase")
    ph_task = _check_via_tavily(brand_name, "producthunt.com", "Product Hunt")
    serp_task = _check_serp_diversity(brand_name, domain)

    wiki, youtube, reddit, linkedin, g2, capterra, crunchbase, ph, serp = await asyncio.gather(
        wiki_task, yt_task, reddit_task, linkedin_task,
        g2_task, capterra_task, crunchbase_task, ph_task, serp_task,
        return_exceptions=True,
    )

    # Handle exceptions
    platforms = {}
    for name, res in [
        ("wikipedia", wiki), ("youtube", youtube), ("reddit", reddit),
        ("linkedin", linkedin), ("g2", g2), ("capterra", capterra),
        ("crunchbase", crunchbase), ("producthunt", ph), ("serp_diversity", serp),
    ]:
        if isinstance(res, Exception):
            platforms[name] = {"platform": name, "found": False, "error": str(res), "score": 0}
        else:
            platforms[name] = res

    # Calculate footprint score (weighted)
    footprint_score = 0.0
    for key, weight in _PLATFORM_WEIGHTS.items():
        footprint_score += platforms.get(key, {}).get("score", 0) * (weight / 100)

    return {
        "brand_name": brand_name,
        "domain": domain,
        "footprint_score": min(round(footprint_score), 100),
        "platforms": platforms,
    }


def _format_report(data: dict) -> str:
    """Format brand presence as markdown."""
    lines = [f"## Brand Digital Footprint — {data['brand_name']}\n"]

    score = data["footprint_score"]
    if score >= 70:
        label = "Strong"
    elif score >= 40:
        label = "Moderate"
    else:
        label = "Weak"

    lines.append(f"**Footprint Score: {score}/100 ({label})**\n")

    # Platform details
    lines.append("### Platform Presence\n")
    lines.append("| Platform | Status | Details |")
    lines.append("|----------|--------|---------|")

    p = data["platforms"]

    # Wikipedia
    wiki = p.get("wikipedia", {})
    if wiki.get("has_wikipedia"):
        lines.append(f"| Wikipedia | ✅ Found | [{wiki.get('wikipedia_url', 'link')}]({wiki.get('wikipedia_url', '')}) |")
    else:
        lines.append("| Wikipedia | ❌ Not found | Consider creating a Wikipedia article |")

    if wiki.get("has_wikidata"):
        lines.append(f"| Wikidata | ✅ Entity {wiki.get('wikidata_id', '')} | Machine-readable brand identity |")
    else:
        lines.append("| Wikidata | ❌ No entity | Create a Wikidata entry for AI entity resolution |")

    # YouTube
    yt = p.get("youtube", {})
    if yt.get("found"):
        lines.append(f"| YouTube | ✅ {yt.get('result_count', 0)} results | Correlation: 0.737 (strongest AI signal) |")
    else:
        lines.append("| YouTube | ❌ Not found | YouTube transcripts are heavily indexed by AI — create video content |")

    # Reddit
    rd = p.get("reddit", {})
    if rd.get("found"):
        lines.append(f"| Reddit | ✅ {rd.get('result_count', 0)} mentions | Reddit has $60M/year licensing deal with Google |")
    else:
        lines.append("| Reddit | ❌ Not found | Start community presence on relevant subreddits |")

    # LinkedIn
    li = p.get("linkedin", {})
    if li.get("found"):
        lines.append("| LinkedIn | ✅ Found | Key signal for Bing Copilot |")
    else:
        lines.append("| LinkedIn | ❌ Not found | Create a LinkedIn company page |")

    # G2
    g2 = p.get("g2", {})
    if g2.get("found"):
        lines.append(f"| G2 | ✅ {g2.get('result_count', 0)} results | SaaS buyer trust signal |")
    else:
        lines.append("| G2 | ❌ Not found | Claim your G2 product page for buyer credibility |")

    # Capterra
    cap = p.get("capterra", {})
    if cap.get("found"):
        lines.append(f"| Capterra | ✅ {cap.get('result_count', 0)} results | Software buyer discovery |")
    else:
        lines.append("| Capterra | ❌ Not found | List on Capterra to reach SMB software buyers |")

    # Crunchbase
    cb = p.get("crunchbase", {})
    if cb.get("found"):
        lines.append(f"| Crunchbase | ✅ Found | Company credibility signal |")
    else:
        lines.append("| Crunchbase | ❌ Not found | Create a Crunchbase profile for company credibility |")

    # Product Hunt
    ph = p.get("producthunt", {})
    if ph.get("found"):
        lines.append(f"| Product Hunt | ✅ {ph.get('result_count', 0)} results | Maker community discovery |")
    else:
        lines.append("| Product Hunt | ❌ Not found | Launch on Product Hunt for early adopter visibility |")

    # SERP Diversity
    lines.append("\n### Brand SERP Diversity\n")
    serp = p.get("serp_diversity", {})
    tp_count = serp.get("third_party_count", 0)
    total = serp.get("total_results", 0)
    if tp_count >= 3:
        lines.append(f"✅ **{tp_count}/{total}** results on page 1 are from third-party sources — strong brand SERP diversity.")
    elif tp_count >= 1:
        lines.append(f"⚠️ Only **{tp_count}/{total}** third-party results — your brand SERP is too dependent on your own domain.")
    else:
        lines.append("❌ No third-party results found for your brand name — brand SERP is weak.")

    tp_sources = serp.get("third_party_sources", [])
    if tp_sources:
        lines.append("\nThird-party sources found:")
        for src in tp_sources[:5]:
            lines.append(f"- [{src['domain']}]({src['url']}): {src['title']}")

    # Recommendations
    lines.append("\n### Priority Actions\n")
    missing = []
    if not wiki.get("has_wikipedia"):
        missing.append("Wikipedia article (correlation: 0.65 — 47.9% of ChatGPT citations come from Wikipedia)")
    if not yt.get("found"):
        missing.append("YouTube presence (correlation: 0.737 — strongest AI visibility signal)")
    if not rd.get("found"):
        missing.append("Reddit community presence (correlation: 0.68)")
    if not wiki.get("has_wikidata"):
        missing.append("Wikidata entity (correlation: 0.61 — enables AI entity disambiguation)")
    if not g2.get("found"):
        missing.append("G2 product page (critical for SaaS buyer trust)")
    if not cb.get("found"):
        missing.append("Crunchbase profile (company credibility and media discovery)")
    if tp_count < 3:
        missing.append("more third-party brand mentions (target 3+ independent results on brand SERP)")

    if missing:
        for i, action in enumerate(missing, 1):
            lines.append(f"{i}. Create **{action}**")
    else:
        lines.append("Brand has strong digital footprint across all key platforms.")

    lines.append("\n> **Schema.org tip:** Add `sameAs` links in your Organization JSON-LD to Wikipedia, Wikidata, YouTube, LinkedIn, and Reddit profiles.")

    return "\n".join(lines)


@function_tool
async def scan_brand_presence(brand_name: str, domain: str = "") -> str:
    """Scan brand presence across platforms that correlate with AI visibility and buyer trust: YouTube, Reddit, Wikipedia, LinkedIn, G2, Capterra, Crunchbase, Product Hunt. Also checks brand SERP diversity (third-party results when searching the brand name). Returns a digital footprint score and platform-by-platform analysis."""
    data = await _brand_presence_impl(brand_name, domain or None)
    return _format_report(data)

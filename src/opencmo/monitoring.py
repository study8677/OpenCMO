"""Monitoring orchestration — discover, review, and recommend."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from typing import Callable

logger = logging.getLogger(__name__)

from opencmo import llm, storage
from opencmo.finding_contract import upgrade_legacy_finding
from opencmo.finding_verifier import run_verifier_suite

ProgressCallback = Callable[[dict], None]

SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


@dataclass
class EvidenceRef:
    domain: str
    source: str
    key: str
    value: str
    url: str | None = None


@dataclass
class Finding:
    domain: str
    severity: str
    title: str
    summary: str
    confidence: float
    evidence_refs: list[EvidenceRef] = field(default_factory=list)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["evidence_refs"] = [asdict(ref) for ref in self.evidence_refs]
        return data


@dataclass
class Recommendation:
    domain: str
    priority: str
    owner_type: str
    action_type: str
    title: str
    summary: str
    rationale: str
    confidence: float
    evidence_refs: list[EvidenceRef] = field(default_factory=list)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["evidence_refs"] = [asdict(ref) for ref in self.evidence_refs]
        return data


def _truncate(text: str, limit: int = 160) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1].rstrip()}…"


def _event(
    stage: str,
    status: str,
    summary: str,
    *,
    agent: str | None = None,
    detail: str | None = None,
    role: str | None = None,
    round_num: int = 0,
) -> dict:
    payload = {
        "stage": stage,
        "status": status,
        "agent": agent or "",
        "summary": summary,
        "detail": detail or summary,
        # Backward-compatible fields used by older UI/tests.
        "role": role or (agent or stage),
        "content": detail or summary,
        "round": round_num,
    }
    return payload


async def _record_step(run_id: int, event: dict) -> None:
    await storage.add_scan_run_step(
        run_id,
        stage=event["stage"],
        status=event["status"],
        summary=event["summary"],
        agent=event.get("agent") or None,
        detail=event.get("detail"),
    )


async def _emit(run_id: int, callback: ProgressCallback | None, event: dict) -> None:
    await _record_step(run_id, event)
    if callback:
        callback(event)


def _metric_ref(domain: str, source: str, key: str, value, url: str | None = None) -> EvidenceRef:
    return EvidenceRef(domain=domain, source=source, key=key, value=str(value), url=url)


async def _build_project_context(
    run_id: int,
    project_id: int,
    analyze_url: str | None,
    locale: str,
    on_progress: ProgressCallback | None,
) -> dict:
    from opencmo import service

    await _emit(run_id, on_progress, _event(
        "context_build",
        "started",
        "Building project context.",
        agent="Project Context Builder",
    ))

    if analyze_url and not llm.get_key("OPENAI_API_KEY"):
        await _emit(run_id, on_progress, _event(
            "context_build", "warning",
            "No LLM API key configured. AI analysis skipped — keywords and competitors will not be extracted automatically.",
            agent="Project Context Builder",
        ))

    if analyze_url and llm.get_key("OPENAI_API_KEY"):
        def relay(role: str, content: str, round_num: int):
            if on_progress:
                label = role.replace("_", " ").title()
                on_progress(_event(
                    "context_build",
                    "running",
                    _truncate(content),
                    agent=label,
                    detail=content,
                    role=role,
                    round_num=round_num,
                ))

        await service.analyze_and_enrich_project(
            project_id,
            analyze_url,
            on_progress=relay,
            locale=locale,
        )
        summary = "Project context refreshed from URL analysis."
    else:
        summary = "Using stored project metadata as context baseline."

    project = await storage.get_project(project_id)
    keywords = await storage.list_tracked_keywords(project_id)
    competitors = await storage.list_competitors(project_id)

    if analyze_url and len(keywords) == 0:
        await _emit(run_id, on_progress, _event(
            "context_build",
            "warning",
            "AI analysis did not extract any keywords. Downstream SEO and SERP checks will have limited coverage.",
            agent="Project Context Builder",
        ))

    await _emit(run_id, on_progress, _event(
        "context_build",
        "completed",
        f"{summary} {len(keywords)} keywords and {len(competitors)} competitors available.",
        agent="Project Context Builder",
    ))

    return {
        "project": project,
        "keywords": keywords,
        "competitors": competitors,
    }


async def _collect_signals(
    run_id: int,
    project_id: int,
    job_type: str,
    job_id: int,
    on_progress: ProgressCallback | None,
) -> None:
    from opencmo import storage as _storage

    await _emit(run_id, on_progress, _event(
        "signal_collect",
        "started",
        "Collecting SEO, GEO, community, and SERP signals.",
        agent="Signal Collector",
    ))

    project = await _storage.get_project(project_id)
    if not project:
        await _emit(run_id, on_progress, _event(
            "signal_collect", "warning",
            f"Project {project_id} not found — skipping signal collection.",
            agent="Signal Collector",
        ))
        return

    import asyncio as _asyncio

    brand = project["brand_name"]
    url = project["url"]
    category = project["category"]
    warnings: list[str] = []

    # --- Define each scan as an independent coroutine ---

    async def _run_seo():
        try:
            from crawl4ai import AsyncWebCrawler

            from opencmo.tools.seo_audit import (
                _build_report,
                _check_robots_and_sitemap,
                _fetch_core_web_vitals,
                _SEOParser,
            )

            async def _crawl_and_parse():
                async with AsyncWebCrawler() as crawler:
                    return await crawler.arun(url=url)

            result = await _asyncio.wait_for(_crawl_and_parse(), timeout=90)
            parser = _SEOParser()
            html = getattr(result, "html", "") or ""
            parser.feed(html)
            cwv = await _fetch_core_web_vitals(url)
            robots_sitemap = await _check_robots_and_sitemap(url)
            report = _build_report(parser, result, url, cwv=cwv, robots_sitemap=robots_sitemap)
            await _storage.save_seo_scan(
                project_id, url, report,
                score_performance=cwv.get("performance") if cwv else None,
                score_lcp=cwv.get("lcp") if cwv else None,
                score_cls=cwv.get("cls") if cwv else None,
                score_tbt=cwv.get("tbt") if cwv else None,
                has_robots_txt=robots_sitemap.get("has_robots") if robots_sitemap else None,
                has_sitemap=robots_sitemap.get("has_sitemap") if robots_sitemap else None,
                has_schema_org=bool(parser.schema_types),
            )
        except Exception as exc:
            warnings.append(f"SEO scan failed: {exc}")
            await _emit(run_id, on_progress, _event(
                "signal_collect", "warning", f"SEO scan failed: {exc}", agent="Signal Collector",
            ))

        try:
            from opencmo.tools.serp_tracker import track_project_keywords
            await track_project_keywords(project_id)
        except Exception as exc:
            warnings.append(f"SERP tracking failed: {exc}")
            await _emit(run_id, on_progress, _event(
                "signal_collect", "warning", f"SERP tracking failed: {exc}", agent="Signal Collector",
            ))

    async def _run_geo():
        try:
            import json as _json

            from opencmo.tools.geo_providers import GEO_PROVIDER_REGISTRY
            from opencmo.tools.text_signals import analyze_geo_sentiment

            enabled = [p for p in GEO_PROVIDER_REGISTRY if p.is_enabled]
            results = {}
            for provider in enabled:
                try:
                    agg = await provider.check_visibility_multi(brand, category)
                    results[provider.name] = agg
                except Exception:
                    pass

            platforms_mentioned = sum(1 for r in results.values() if r.mentioned)
            visibility_score = int(platforms_mentioned / len(enabled) * 40) if enabled else 0
            position_scores = [30 * (1 - r.best_position_pct / 100) for r in results.values() if r.best_position_pct is not None]
            position_score = int(sum(position_scores) / len(position_scores)) if position_scores else 0
            sentiment_snippets: dict[str, str] = {}
            for name, aggregated in results.items():
                snippets = [
                    qr.content_snippet
                    for qr in getattr(aggregated, "per_query_results", [])
                    if getattr(qr, "content_snippet", "")
                ]
                if snippets:
                    sentiment_snippets[name] = "\n".join(snippets)

            sentiment_signal = await analyze_geo_sentiment(brand, sentiment_snippets)
            sentiment_score = sentiment_signal.score
            geo_score = visibility_score + position_score + (sentiment_score or 0)

            payload = {
                name: {
                    "mentioned": r.mentioned,
                    "mention_count": r.total_mention_count,
                    "position_pct": r.best_position_pct,
                }
                for name, r in results.items()
            }
            payload["_sentiment"] = {
                "score": sentiment_score,
                "label": sentiment_signal.label,
                "reasoning": sentiment_signal.reasoning,
            }
            platform_json = _json.dumps(payload)
            await _storage.save_geo_scan(
                project_id, geo_score,
                visibility_score=visibility_score,
                position_score=position_score,
                sentiment_score=sentiment_score,
                platform_results_json=platform_json,
            )
        except Exception as exc:
            warnings.append(f"GEO scan failed: {exc}")
            await _emit(run_id, on_progress, _event(
                "signal_collect", "warning", f"GEO scan failed: {exc}", agent="Signal Collector",
            ))

    async def _run_community():
        try:
            import json as _json

            from opencmo.tools.community import _scan_community_impl
            from opencmo.tools.community_scoring import text_relevance

            tracked_keywords = [
                item["keyword"]
                for item in await _storage.list_tracked_keywords(project_id)
            ]
            competitors = await _storage.list_competitors(project_id)
            competitor_names = [item["name"] for item in competitors]
            competitor_keywords: list[str] = []
            for competitor in competitors:
                competitor_keywords.extend(
                    keyword["keyword"]
                    for keyword in await _storage.list_competitor_keywords(competitor["id"])
                )

            raw = await _scan_community_impl(
                brand, category,
                tracked_keywords=tracked_keywords,
                competitor_names=competitor_names,
                competitor_keywords=competitor_keywords,
                canonical_url=url,
            )
            data = _json.loads(raw)
            total_hits = len(data.get("hits", []))
            await _storage.save_community_scan(project_id, total_hits, raw)

            for hit in data.get("hits", []):
                if hit.get("source_kind") == "external_search":
                    continue
                title = hit.get("title", "")
                preview = hit.get("preview", "")
                relevance = text_relevance(brand, title, preview)
                if relevance < 0.05 and (hit.get("engagement_score") or 0) < 5:
                    continue
                try:
                    disc_id = await _storage.upsert_tracked_discussion(project_id, hit)
                    await _storage.save_discussion_snapshot(
                        disc_id, hit.get("raw_score", 0),
                        hit.get("comments_count", 0),
                        hit.get("engagement_score", 0),
                    )
                except Exception:
                    pass
        except Exception as exc:
            warnings.append(f"Community scan failed: {exc}")
            await _emit(run_id, on_progress, _event(
                "signal_collect", "warning", f"Community scan failed: {exc}", agent="Signal Collector",
            ))

    # --- Run scans in parallel ---
    tasks = []
    if job_type in ("seo", "full"):
        tasks.append(_run_seo())
    if job_type in ("geo", "full"):
        tasks.append(_run_geo())
    if job_type in ("community", "full"):
        tasks.append(_run_community())

    if tasks:
        await _asyncio.gather(*tasks)

    # Update job last_run_at
    if job_id is not None:
        try:
            await _storage.update_job_last_run(job_id)
        except Exception:
            pass

    summary = "Signal collection finished and raw snapshots were stored."
    if warnings:
        summary = f"Signal collection finished with {len(warnings)} warning(s)."
    await _emit(run_id, on_progress, _event(
        "signal_collect",
        "completed",
        summary,
        agent="Signal Collector",
    ))


async def _normalize_signals(
    run_id: int,
    project_id: int,
    context: dict,
    on_progress: ProgressCallback | None,
) -> dict:
    await _emit(run_id, on_progress, _event(
        "signal_normalize",
        "started",
        "Normalizing raw monitoring evidence.",
        agent="Signal Normalizer",
    ))

    seo_history = await storage.get_seo_history(project_id, limit=1)
    geo_history = await storage.get_geo_history(project_id, limit=1)
    community_history = await storage.get_community_history(project_id, limit=1)
    discussions = await storage.get_tracked_discussions(project_id)
    serp_latest = await storage.get_all_serp_latest(project_id)
    competitors = await storage.list_competitors(project_id)

    competitor_keywords: list[dict] = []
    for comp in competitors:
        kws = await storage.list_competitor_keywords(comp["id"])
        competitor_keywords.append({**comp, "keywords": kws})

    normalized = {
        "project": context["project"],
        "keywords": context["keywords"],
        "competitors": competitor_keywords,
        "seo": seo_history[0] if seo_history else None,
        "geo": geo_history[0] if geo_history else None,
        "community": community_history[0] if community_history else None,
        "discussions": discussions,
        "serp": serp_latest,
    }

    await _emit(run_id, on_progress, _event(
        "signal_normalize",
        "completed",
        f"Normalized {len(discussions)} discussions, {len(serp_latest)} tracked keywords, and {len(competitor_keywords)} competitors.",
        agent="Signal Normalizer",
    ))

    return normalized


def _seo_review(data: dict) -> tuple[str, list[Finding], list[Recommendation]]:
    findings: list[Finding] = []
    recommendations: list[Recommendation] = []
    seo = data["seo"]
    serp = data["serp"]
    project = data["project"]

    if not seo:
        findings.append(Finding(
            domain="seo",
            severity="warning",
            title="SEO baseline is missing",
            summary="No recent SEO scan is available, so technical issues and ranking risk are currently blind spots.",
            confidence=0.66,
        ))
        recommendations.append(Recommendation(
            domain="seo",
            priority="high",
            owner_type="engineering",
            action_type="restore_seo_baseline",
            title="Restore a reliable SEO baseline",
            summary="Ensure scheduled SEO scans succeed and keep the latest crawl + CWV data available for every project.",
            rationale="Without a fresh baseline, prioritization becomes guesswork.",
            confidence=0.72,
        ))
        return "SEO review found no usable baseline.", findings, recommendations

    health_score = seo.get("seo_health_score")
    if health_score is not None:
        if health_score < 50.0:
            findings.append(Finding(
                domain="seo",
                severity="critical",
                title="Overall SEO health is critically weak",
                summary=f"Latest SEO health score is {health_score}/100, indicating severe gaps in technical fundamentals or on-page quality.",
                confidence=0.85,
                evidence_refs=[_metric_ref("seo", "seo_scan", "seo_health_score", health_score, project["url"])],
            ))
            recommendations.append(Recommendation(
                domain="seo",
                priority="high",
                owner_type="engineering",
                action_type="improve_seo_health",
                title="Prioritize core SEO technical fixes",
                summary="Address critical gaps across robots.txt, sitemaps, structured data, or page performance.",
                rationale="A critical SEO health score directly suppresses organic visibility.",
                confidence=0.82,
                evidence_refs=[_metric_ref("seo", "seo_scan", "seo_health_score", health_score, project["url"])],
            ))
        elif health_score < 75.0:
            findings.append(Finding(
                domain="seo",
                severity="warning",
                title="SEO health needs improvement",
                summary=f"Latest SEO health score is {health_score}/100, leaving room for technical or on-page optimization.",
                confidence=0.80,
                evidence_refs=[_metric_ref("seo", "seo_scan", "seo_health_score", health_score, project["url"])],
            ))

    lcp = seo.get("score_lcp")
    if lcp is not None and lcp >= 4000:
        findings.append(Finding(
            domain="seo",
            severity="critical",
            title="Largest Contentful Paint is slow",
            summary=f"LCP is {int(lcp)}ms, well beyond the good threshold for landing pages.",
            confidence=0.88,
            evidence_refs=[_metric_ref("seo", "seo_scan", "lcp_ms", int(lcp), project["url"])],
        ))
    elif lcp is not None and lcp >= 2500:
        findings.append(Finding(
            domain="seo",
            severity="warning",
            title="Largest Contentful Paint needs improvement",
            summary=f"LCP is {int(lcp)}ms and is likely suppressing organic page quality.",
            confidence=0.78,
            evidence_refs=[_metric_ref("seo", "seo_scan", "lcp_ms", int(lcp), project["url"])],
        ))

    cls = seo.get("score_cls")
    if cls is not None and cls >= 0.1:
        findings.append(Finding(
            domain="seo",
            severity="warning",
            title="Layout instability is visible",
            summary=f"CLS is {cls:.2f}; unstable layouts are degrading perceived quality.",
            confidence=0.73,
            evidence_refs=[_metric_ref("seo", "seo_scan", "cls", f"{cls:.2f}", project["url"])],
        ))

    if seo.get("has_robots_txt") == 0:
        findings.append(Finding(
            domain="seo",
            severity="critical",
            title="robots.txt is missing",
            summary="The project is missing robots.txt, which weakens crawl governance and site hygiene.",
            confidence=0.92,
            evidence_refs=[_metric_ref("seo", "seo_scan", "has_robots_txt", 0, project["url"])],
        ))
        recommendations.append(Recommendation(
            domain="seo",
            priority="high",
            owner_type="engineering",
            action_type="add_robots_txt",
            title="Add and validate robots.txt",
            summary="Publish a minimal robots.txt and confirm that key pages remain crawlable.",
            rationale="Missing crawl directives are a straightforward technical SEO gap.",
            confidence=0.9,
            evidence_refs=[_metric_ref("seo", "seo_scan", "has_robots_txt", 0, project["url"])],
        ))

    if seo.get("has_sitemap") == 0:
        findings.append(Finding(
            domain="seo",
            severity="warning",
            title="Sitemap is missing",
            summary="No sitemap was detected, which reduces discoverability for newly added pages.",
            confidence=0.84,
            evidence_refs=[_metric_ref("seo", "seo_scan", "has_sitemap", 0, project["url"])],
        ))

    if seo.get("has_schema_org") == 0:
        findings.append(Finding(
            domain="seo",
            severity="warning",
            title="Structured data coverage is missing",
            summary="Schema.org markup was not detected on the scanned page.",
            confidence=0.81,
            evidence_refs=[_metric_ref("seo", "seo_scan", "has_schema_org", 0, project["url"])],
        ))
        recommendations.append(Recommendation(
            domain="seo",
            priority="medium",
            owner_type="engineering",
            action_type="add_structured_data",
            title="Add product-focused structured data",
            summary="Introduce Schema.org markup on core marketing pages to improve machine readability.",
            rationale="Structured data improves how search systems interpret the product.",
            confidence=0.78,
            evidence_refs=[_metric_ref("seo", "seo_scan", "has_schema_org", 0, project["url"])],
        ))

    ranked = [item for item in serp if item.get("position")]
    if serp and not ranked:
        findings.append(Finding(
            domain="seo",
            severity="warning",
            title="Tracked keywords are not ranking yet",
            summary="Tracked keywords have no successful SERP positions in the latest snapshot.",
            confidence=0.71,
            evidence_refs=[_metric_ref("seo", "serp_snapshot", "tracked_keywords", len(serp), project["url"])],
        ))
        recommendations.append(Recommendation(
            domain="seo",
            priority="high",
            owner_type="content",
            action_type="build_rankable_content",
            title="Create rankable landing and comparison content",
            summary="Target tracked keywords with intent-aligned pages instead of relying on the homepage alone.",
            rationale="No current rankings usually means the site lacks focused acquisition pages.",
            confidence=0.76,
            evidence_refs=[_metric_ref("seo", "serp_snapshot", "tracked_keywords", len(serp), project["url"])],
        ))
    elif ranked and not any(item["position"] <= 10 for item in ranked):
        findings.append(Finding(
            domain="seo",
            severity="info",
            title="SEO visibility exists but lacks top-10 coverage",
            summary="The site ranks for tracked keywords, but none are in the top 10 yet.",
            confidence=0.69,
            evidence_refs=[_metric_ref("seo", "serp_snapshot", "top_ranked_keywords", len(ranked), project["url"])],
        ))

    summary = "SEO review completed with technical and ranking signals." if findings else "SEO review found no urgent issues."
    return summary, findings, recommendations


def _geo_review(data: dict) -> tuple[str, list[Finding], list[Recommendation]]:
    findings: list[Finding] = []
    recommendations: list[Recommendation] = []
    geo = data["geo"]
    project = data["project"]

    if not geo:
        findings.append(Finding(
            domain="geo",
            severity="warning",
            title="GEO baseline is missing",
            summary="No recent AI visibility scan is available.",
            confidence=0.66,
        ))
        return "GEO review found no usable baseline.", findings, recommendations

    score = geo.get("geo_score")
    if score is not None and score < 30:
        findings.append(Finding(
            domain="geo",
            severity="critical",
            title="AI visibility is weak",
            summary=f"GEO score is {score}/100, indicating low presence across AI answer surfaces.",
            confidence=0.84,
            evidence_refs=[_metric_ref("geo", "geo_scan", "geo_score", score, project["url"])],
        ))
    elif score is not None and score < 60:
        findings.append(Finding(
            domain="geo",
            severity="warning",
            title="AI visibility is inconsistent",
            summary=f"GEO score is {score}/100 and needs broader mention coverage.",
            confidence=0.77,
            evidence_refs=[_metric_ref("geo", "geo_scan", "geo_score", score, project["url"])],
        ))

    raw_results = geo.get("platform_results_json") or "{}"
    try:
        platform_results = json.loads(raw_results)
    except json.JSONDecodeError:
        platform_results = {}
    mentioned = [name for name, value in platform_results.items() if value.get("mentioned")]

    if platform_results and not mentioned:
        findings.append(Finding(
            domain="geo",
            severity="critical",
            title="Brand is absent from scanned AI platforms",
            summary="No monitored AI platform returned a visible mention for the brand.",
            confidence=0.82,
            evidence_refs=[_metric_ref("geo", "geo_scan", "platform_mentions", 0, project["url"])],
        ))
    elif len(mentioned) <= 1:
        findings.append(Finding(
            domain="geo",
            severity="warning",
            title="AI mentions are concentrated in too few platforms",
            summary=f"Only {len(mentioned)} monitored platform(s) mentioned the brand.",
            confidence=0.74,
            evidence_refs=[_metric_ref("geo", "geo_scan", "platform_mentions", len(mentioned), project["url"])],
        ))

    if findings:
        recommendations.append(Recommendation(
            domain="geo",
            priority="high",
            owner_type="content",
            action_type="expand_ai_citations",
            title="Publish comparison and buyer-intent content for AI retrieval",
            summary="Create product comparisons, FAQ-style pages, and category explainers that LLMs can cite.",
            rationale="AI visibility improves when the product has clear, machine-readable coverage across intent-rich topics.",
            confidence=0.78,
            evidence_refs=[_metric_ref("geo", "geo_scan", "geo_score", score or 0, project["url"])],
        ))
        recommendations.append(Recommendation(
            domain="geo",
            priority="medium",
            owner_type="marketing",
            action_type="seed_third_party_mentions",
            title="Increase third-party mentions in trusted sources",
            summary="Target roundups, community posts, and documentation references that AI systems are likely to ingest.",
            rationale="Independent mentions improve entity recognition and recommendation likelihood.",
            confidence=0.74,
            evidence_refs=[_metric_ref("geo", "geo_scan", "platform_mentions", len(mentioned), project["url"])],
        ))

    summary = "GEO review completed with visibility signals." if findings else "GEO review found stable visibility."
    return summary, findings, recommendations


def _community_review(data: dict) -> tuple[str, list[Finding], list[Recommendation]]:
    findings: list[Finding] = []
    recommendations: list[Recommendation] = []
    community = data["community"]
    discussions = data["discussions"]
    project = data["project"]

    if not community:
        findings.append(Finding(
            domain="community",
            severity="warning",
            title="Community monitoring baseline is missing",
            summary="No recent community scan is available for the project.",
            confidence=0.68,
        ))
        return "Community review found no usable baseline.", findings, recommendations

    total_hits = community.get("total_hits") or 0
    if total_hits == 0:
        findings.append(Finding(
            domain="community",
            severity="info",
            title="No community demand was captured",
            summary="The latest scan found no relevant discussions, suggesting weak discovery or weak query coverage.",
            confidence=0.7,
            evidence_refs=[_metric_ref("community", "community_scan", "total_hits", total_hits, project["url"])],
        ))
        recommendations.append(Recommendation(
            domain="community",
            priority="medium",
            owner_type="community",
            action_type="expand_monitor_queries",
            title="Broaden monitored community queries",
            summary="Add problem-led and competitor-led terms instead of relying only on brand phrases.",
            rationale="Zero hits often means query coverage is too narrow.",
            confidence=0.73,
            evidence_refs=[_metric_ref("community", "community_scan", "total_hits", total_hits, project["url"])],
        ))
        return "Community review found no active discussions.", findings, recommendations

    high_value = [d for d in discussions if (d.get("engagement_score") or 0) >= 20]
    if high_value:
        findings.append(Finding(
            domain="community",
            severity="info",
            title="High-value discussions are available",
            summary=f"{len(high_value)} tracked discussions already show meaningful engagement.",
            confidence=0.79,
            evidence_refs=[_metric_ref("community", "tracked_discussions", "high_value_count", len(high_value), project["url"])],
        ))
        recommendations.append(Recommendation(
            domain="community",
            priority="high",
            owner_type="community",
            action_type="engage_discussions",
            title="Review and engage the highest-signal discussions",
            summary="Prepare human-reviewed replies for the top community threads surfaced by the scan.",
            rationale="Existing active threads are the fastest path to validated market feedback and awareness.",
            confidence=0.81,
            evidence_refs=[_metric_ref("community", "tracked_discussions", "high_value_count", len(high_value), project["url"])],
        ))

    if total_hits < 3:
        findings.append(Finding(
            domain="community",
            severity="warning",
            title="Community signal volume is thin",
            summary=f"Only {total_hits} discussion hit(s) were found in the latest scan.",
            confidence=0.72,
            evidence_refs=[_metric_ref("community", "community_scan", "total_hits", total_hits, project["url"])],
        ))

    summary = "Community review completed with engagement signals." if findings else "Community review found healthy discussion coverage."
    return summary, findings, recommendations


def _competitor_review(data: dict) -> tuple[str, list[Finding], list[Recommendation]]:
    findings: list[Finding] = []
    recommendations: list[Recommendation] = []
    competitors = data["competitors"]
    project_keywords = {kw["keyword"].lower() for kw in data["keywords"]}
    project = data["project"]

    if not competitors:
        findings.append(Finding(
            domain="competitor",
            severity="info",
            title="Competitor baseline is sparse",
            summary="The project has no saved competitors, so competitive monitoring is weak.",
            confidence=0.75,
        ))
        recommendations.append(Recommendation(
            domain="competitor",
            priority="medium",
            owner_type="marketing",
            action_type="expand_competitor_set",
            title="Track at least 3 real competitors",
            summary="Add direct competitors and their core keywords to improve differentiation planning.",
            rationale="Competitive context is needed to prioritize SEO, GEO, and community moves.",
            confidence=0.77,
        ))
        return "Competitor review found no saved baseline.", findings, recommendations

    overlap = 0
    for comp in competitors:
        overlap += len(project_keywords.intersection({kw["keyword"].lower() for kw in comp["keywords"]}))

    if overlap > 0:
        findings.append(Finding(
            domain="competitor",
            severity="warning",
            title="Keyword overlap with competitors is meaningful",
            summary=f"Tracked competitor keywords overlap with the current project keyword set {overlap} time(s).",
            confidence=0.76,
            evidence_refs=[_metric_ref("competitor", "competitor_keywords", "keyword_overlap", overlap, project["url"])],
        ))
        recommendations.append(Recommendation(
            domain="competitor",
            priority="medium",
            owner_type="content",
            action_type="differentiate_positioning",
            title="Create differentiation pages for overlapping terms",
            summary="Publish category, comparison, and migration content that makes your positioning explicit.",
            rationale="High keyword overlap raises the cost of winning generic discovery terms.",
            confidence=0.73,
            evidence_refs=[_metric_ref("competitor", "competitor_keywords", "keyword_overlap", overlap, project["url"])],
        ))

    if len(competitors) < 3:
        recommendations.append(Recommendation(
            domain="competitor",
            priority="low",
            owner_type="marketing",
            action_type="expand_competitor_set",
            title="Broaden competitor coverage",
            summary="Track more competitor domains so monitoring reflects the actual market.",
            rationale="Too-small competitor sets distort strategic conclusions.",
            confidence=0.68,
        ))

    summary = "Competitor review completed with differentiation signals." if findings or recommendations else "Competitor review found no urgent issues."
    return summary, findings, recommendations


def _dedupe_findings(findings: list[Finding]) -> list[Finding]:
    seen: set[tuple[str, str]] = set()
    result: list[Finding] = []
    for finding in findings:
        key = (finding.domain, finding.title)
        if key in seen:
            continue
        seen.add(key)
        result.append(finding)
    return sorted(result, key=lambda item: (SEVERITY_ORDER[item.severity], item.domain, item.title))


def _dedupe_recommendations(recommendations: list[Recommendation]) -> list[Recommendation]:
    seen: set[tuple[str, str]] = set()
    result: list[Recommendation] = []
    for rec in recommendations:
        key = (rec.domain, rec.title)
        if key in seen:
            continue
        seen.add(key)
        result.append(rec)
    return sorted(result, key=lambda item: (PRIORITY_ORDER[item.priority], item.domain, item.title))


def _build_summary(findings: list[dict], recommendations: list[dict]) -> str:
    critical = sum(1 for item in findings if item.get("severity") == "critical")
    warnings = sum(1 for item in findings if item.get("severity") == "warning")
    domains = sorted({item.get("domain", "?") for item in findings + recommendations})
    if not findings and not recommendations:
        return "Monitoring completed without new findings."
    if critical:
        return f"Monitoring found {critical} critical and {warnings} warning issue(s) across {', '.join(domains)}."
    return f"Monitoring produced {len(findings)} findings and {len(recommendations)} recommended actions across {', '.join(domains)}."


def _serialize_recommendation(rec: Recommendation) -> dict:
    payload = rec.to_dict()
    payload["metadata"] = {
        "source_stage": "domain_review",
        "dedupe_key": f"{rec.domain}:{rec.title.strip().lower().replace(' ', '_')}",
        "rationale": rec.rationale,
    }
    return payload


async def run_monitoring_workflow(
    task_id: str,
    project_id: int,
    monitor_id: int,
    job_type: str,
    job_id: int,
    *,
    analyze_url: str | None = None,
    locale: str = "en",
    on_progress: ProgressCallback | None = None,
) -> dict:
    run_id = await storage.create_scan_run(task_id, monitor_id, project_id, job_type)
    await storage.update_scan_run(run_id, status="running")

    try:
        context = await _build_project_context(run_id, project_id, analyze_url, locale, on_progress)
        await _collect_signals(run_id, project_id, job_type, job_id, on_progress)
        normalized = await _normalize_signals(run_id, project_id, context, on_progress)

        all_findings: list[dict] = []
        all_recommendations: list[Recommendation] = []

        await _emit(run_id, on_progress, _event(
            "domain_review",
            "started",
            "Running domain analysts.",
            agent="Monitoring Orchestrator",
        ))

        for agent_name, review_fn in [
            ("SEO Analyst", _seo_review),
            ("GEO Analyst", _geo_review),
            ("Community Analyst", _community_review),
            ("Competitor Analyst", _competitor_review),
        ]:
            summary, findings, recommendations = review_fn(normalized)
            all_findings.extend({**item.to_dict(), "_source_agent": agent_name} for item in findings)
            all_recommendations.extend(recommendations)
            await _emit(run_id, on_progress, _event(
                "domain_review",
                "completed",
                summary,
                agent=agent_name,
                detail=summary,
            ))

        await _emit(run_id, on_progress, _event(
            "finding_verification",
            "started",
            "Validating findings, deduplicating overlap, and classifying evidence quality.",
            agent="Chief Verifier",
        ))

        contract_findings = [
            upgrade_legacy_finding(
                {k: v for k, v in item.items() if not k.startswith("_")},
                source_agent=item.get("_source_agent", "Domain Analyst"),
            )
            for item in all_findings
        ]
        verification = run_verifier_suite(contract_findings, normalized)
        findings = [item.to_storage_dict() for item in verification.validated_findings]
        recommendations = [_serialize_recommendation(item) for item in _dedupe_recommendations(all_recommendations)]

        await _emit(run_id, on_progress, _event(
            "finding_verification",
            "completed",
            f"Validated {len(findings)} findings, dropped {len(verification.dropped_findings)} duplicates/conflicts.",
            agent="Chief Verifier",
            detail=json.dumps(verification.to_dict(), ensure_ascii=False),
        ))

        summary = _build_summary(findings, recommendations)
        await _emit(run_id, on_progress, _event(
            "strategy_synthesis",
            "completed",
            summary,
            agent="Strategy Synthesizer",
        ))

        await storage.replace_scan_artifacts(
            run_id,
            findings,
            recommendations,
        )

        await storage.update_scan_run(run_id, status="completed", summary=summary, completed=True)
        await _emit(run_id, on_progress, _event(
            "persist_publish",
            "completed",
            f"Saved {len(findings)} findings and {len(recommendations)} recommendations.",
            agent="Monitoring Orchestrator",
        ))

        if job_type == "full":
            try:
                from opencmo.background import service as _bg_service

                # Queue report generation as a separate background task so the scan
                # task can complete quickly and not be vulnerable to server restarts.
                dedupe_key = f"report:strategic:{project_id}"
                existing_report_task = await _bg_service.find_active_task_by_dedupe_key(dedupe_key)
                if existing_report_task is None:
                    await _bg_service.enqueue_task(
                        kind="report",
                        project_id=project_id,
                        payload={"project_id": project_id, "kind": "strategic", "source_run_id": run_id},
                        dedupe_key=dedupe_key,
                    )
                    await _emit(run_id, on_progress, _event(
                        "reporting",
                        "started",
                        "Strategic report generation queued.",
                        agent="AI CMO Reporter",
                    ))
            except Exception as exc:
                logger.debug("Report task queue failed: %s", exc)

        # Auto-trigger graph expansion after successful full scan
        if job_type == "full":
            try:
                from opencmo.background import service as bg_service

                existing = await bg_service.find_active_task_by_dedupe_key(f"graph:project:{project_id}")
                if existing is None:
                    await storage.get_or_create_expansion(project_id)
                    await storage.seed_expansion_nodes(project_id)
                    await storage.update_expansion(project_id, desired_state="running")
                    await bg_service.enqueue_task(
                        kind="graph_expansion",
                        project_id=project_id,
                        payload={"project_id": project_id},
                        dedupe_key=f"graph:project:{project_id}",
                    )
                    logger.info("Auto-triggered graph expansion for project %d", project_id)
            except Exception as exc:
                logger.debug("Graph expansion auto-trigger skipped: %s", exc)

        return {
            "run_id": run_id,
            "status": "completed",
            "summary": summary,
            "findings": findings,
            "recommendations": recommendations,
            "verification": verification.to_dict(),
        }
    except Exception as exc:
        await storage.update_scan_run(run_id, status="failed", summary=str(exc), completed=True)
        await _emit(run_id, on_progress, _event(
            "persist_publish",
            "failed",
            str(exc),
            agent="Monitoring Orchestrator",
            detail=str(exc),
        ))
        raise

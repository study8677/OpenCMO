"""Monitoring orchestration — discover, review, and recommend."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Callable

from opencmo import llm, storage

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
    from opencmo.scheduler import run_scheduled_scan

    await _emit(run_id, on_progress, _event(
        "signal_collect",
        "started",
        "Collecting SEO, GEO, community, and SERP signals.",
        agent="Signal Collector",
    ))

    await run_scheduled_scan(project_id, job_type, job_id, triggered_by="manual")

    await _emit(run_id, on_progress, _event(
        "signal_collect",
        "completed",
        "Signal collection finished and raw snapshots were stored.",
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

    score = seo.get("score_performance")
    if score is not None and score < 0.6:
        findings.append(Finding(
            domain="seo",
            severity="critical",
            title="Performance score is materially weak",
            summary=f"Latest performance score is {round(score * 100)}%, which is likely harming crawl efficiency and rankings.",
            confidence=0.85,
            evidence_refs=[_metric_ref("seo", "seo_scan", "score_performance", round(score * 100), project["url"])],
        ))
        recommendations.append(Recommendation(
            domain="seo",
            priority="high",
            owner_type="engineering",
            action_type="improve_performance",
            title="Prioritize performance fixes on the monitored site",
            summary="Reduce render-blocking work and large page payloads on the landing pages that drive acquisition.",
            rationale="Low performance score is a ranking and conversion drag.",
            confidence=0.82,
            evidence_refs=[_metric_ref("seo", "seo_scan", "score_performance", round(score * 100), project["url"])],
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


def _build_summary(findings: list[Finding], recommendations: list[Recommendation]) -> str:
    critical = sum(1 for item in findings if item.severity == "critical")
    warnings = sum(1 for item in findings if item.severity == "warning")
    domains = sorted({item.domain for item in findings + recommendations})
    if not findings and not recommendations:
        return "Monitoring completed without new findings."
    if critical:
        return f"Monitoring found {critical} critical and {warnings} warning issue(s) across {', '.join(domains)}."
    return f"Monitoring produced {len(findings)} findings and {len(recommendations)} recommended actions across {', '.join(domains)}."


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

        all_findings: list[Finding] = []
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
            all_findings.extend(findings)
            all_recommendations.extend(recommendations)
            await _emit(run_id, on_progress, _event(
                "domain_review",
                "completed",
                summary,
                agent=agent_name,
                detail=summary,
            ))

        findings = _dedupe_findings(all_findings)
        recommendations = _dedupe_recommendations(all_recommendations)

        summary = _build_summary(findings, recommendations)
        await _emit(run_id, on_progress, _event(
            "strategy_synthesis",
            "completed",
            summary,
            agent="Strategy Synthesizer",
        ))

        await storage.replace_scan_artifacts(
            run_id,
            [item.to_dict() for item in findings],
            [item.to_dict() for item in recommendations],
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
                from opencmo.reports import generate_strategic_report_bundle

                await generate_strategic_report_bundle(project_id, source_run_id=run_id)
                await _emit(run_id, on_progress, _event(
                    "reporting",
                    "completed",
                    "Strategic report refreshed from the completed monitoring run.",
                    agent="AI CMO Reporter",
                ))
            except Exception as exc:
                await _emit(run_id, on_progress, _event(
                    "reporting",
                    "failed",
                    f"Strategic report refresh failed: {exc}",
                    agent="AI CMO Reporter",
                    detail=str(exc),
                ))

        return {
            "run_id": run_id,
            "status": "completed",
            "summary": summary,
            "findings": [item.to_dict() for item in findings],
            "recommendations": [item.to_dict() for item in recommendations],
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

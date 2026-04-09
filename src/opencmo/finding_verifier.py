"""Verification pass for monitoring findings."""

from __future__ import annotations

from collections import defaultdict

from opencmo.finding_contract import VerificationResult, VerifiedFinding

_ENVIRONMENT_PATTERNS = (
    "timeout",
    "timed out",
    "rate limit",
    "provider",
    "network",
    "api key",
    "credentials",
    "429",
    "unreachable",
)
_STATUS_ORDER = {
    "confirmed": 0,
    "likely": 1,
    "hypothesis": 2,
    "environment_limitation": 3,
}


def _join_warning_text(normalized: dict) -> str:
    warnings = normalized.get("warnings", [])
    if isinstance(warnings, list):
        return " ".join(str(item).lower() for item in warnings)
    return str(warnings).lower()


def apply_evidence_verifier(findings: list[VerifiedFinding]) -> tuple[list[VerifiedFinding], list[str]]:
    notes: list[str] = []
    verified: list[VerifiedFinding] = []
    for finding in findings:
        clone = VerifiedFinding(**finding.__dict__)
        clone.evidence_refs = list(finding.evidence_refs)
        clone.unknowns = list(finding.unknowns)
        clone.source_agents = list(finding.source_agents)
        clone.metadata = dict(finding.metadata)
        if clone.evidence_refs:
            clone.status = "confirmed" if (clone.confidence_score or 0.0) >= 0.75 else "likely"
        else:
            clone.status = "hypothesis"
            clone.unknowns.append("Direct evidence is missing; confirm with fresh scan artifacts before acting.")
            notes.append(f"{clone.title}: downgraded to hypothesis because evidence is missing.")
        verified.append(clone)
    return verified, notes


def apply_environment_verifier(
    findings: list[VerifiedFinding],
    normalized: dict,
) -> tuple[list[VerifiedFinding], list[dict], list[str]]:
    notes: list[str] = []
    limitations: list[dict] = []
    warning_text = _join_warning_text(normalized)
    verified: list[VerifiedFinding] = []
    for finding in findings:
        lowered = f"{finding.title} {finding.finding}".lower()
        if any(pattern in lowered or pattern in warning_text for pattern in _ENVIRONMENT_PATTERNS):
            finding.status = "environment_limitation"
            limitations.append({
                "title": finding.title,
                "domain": finding.domain,
                "reason": "environment_limitation",
                "detail": finding.finding,
            })
            notes.append(f"{finding.title}: classified as environment limitation.")
        verified.append(finding)
    return verified, limitations, notes


def apply_dedupe_verifier(findings: list[VerifiedFinding]) -> tuple[list[VerifiedFinding], list[dict]]:
    grouped: dict[str, list[VerifiedFinding]] = defaultdict(list)
    dropped: list[dict] = []
    for finding in findings:
        grouped[finding.dedupe_key].append(finding)

    deduped: list[VerifiedFinding] = []
    for dedupe_key, items in grouped.items():
        items.sort(key=lambda item: ((item.confidence_score or 0.0), len(item.evidence_refs), item.title), reverse=True)
        winner = items[0]
        deduped.append(winner)
        for loser in items[1:]:
            dropped.append({
                "title": loser.title,
                "domain": loser.domain,
                "reason": "duplicate",
                "kept": winner.title,
                "dedupe_key": dedupe_key,
            })
    deduped.sort(key=lambda item: (_STATUS_ORDER.get(item.status, 99), item.domain, item.dedupe_key, item.title))
    return deduped, dropped


def apply_contradiction_verifier(findings: list[VerifiedFinding]) -> tuple[list[VerifiedFinding], list[dict], list[dict], list[str]]:
    kept: list[VerifiedFinding] = []
    contradictions: list[dict] = []
    dropped: list[dict] = []
    notes: list[str] = []

    by_domain: dict[str, list[VerifiedFinding]] = defaultdict(list)
    for finding in findings:
        by_domain[finding.domain].append(finding)

    for domain, items in by_domain.items():
        baseline_missing = [item for item in items if "baseline is missing" in item.title.lower()]
        evidence_backed = [item for item in items if item.evidence_refs and item not in baseline_missing]
        if baseline_missing and evidence_backed:
            winner = sorted(evidence_backed, key=lambda item: ((item.confidence_score or 0.0), len(item.evidence_refs)), reverse=True)[0]
            for loser in baseline_missing:
                contradictions.append({
                    "domain": domain,
                    "dropped": loser.title,
                    "kept": winner.title,
                    "reason": "baseline_missing_conflicts_with_existing_evidence",
                })
                dropped.append({
                    "title": loser.title,
                    "domain": loser.domain,
                    "reason": "contradiction",
                    "kept": winner.title,
                })
                notes.append(f"{loser.title}: dropped because {winner.title} already provides same-domain evidence.")
            items = [item for item in items if item not in baseline_missing]
        kept.extend(items)
    return kept, contradictions, dropped, notes


def run_verifier_suite(findings: list[VerifiedFinding], normalized: dict) -> VerificationResult:
    evidence_verified, notes = apply_evidence_verifier(findings)
    environment_verified, limitations, env_notes = apply_environment_verifier(evidence_verified, normalized)
    deduped, dropped_duplicates = apply_dedupe_verifier(environment_verified)
    contradiction_checked, contradictions, dropped_contradictions, contradiction_notes = apply_contradiction_verifier(deduped)

    contradiction_checked.sort(key=lambda item: (_STATUS_ORDER.get(item.status, 99), item.domain, item.dedupe_key, item.title))
    return VerificationResult(
        validated_findings=contradiction_checked,
        dropped_findings=[*dropped_duplicates, *dropped_contradictions],
        contradictions=contradictions,
        environment_limitations=limitations,
        verifier_notes=[*notes, *env_notes, *contradiction_notes],
    )

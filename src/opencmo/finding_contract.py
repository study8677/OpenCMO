"""Normalized finding contract used across monitoring and reporting."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Literal

FindingStatus = Literal["confirmed", "likely", "hypothesis", "environment_limitation"]

_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "be",
    "does",
    "has",
    "have",
    "is",
    "may",
    "might",
    "not",
    "the",
    "was",
    "were",
    "with",
}
_SYNONYM_MAP = {
    "detected": "missing",
    "missing": "missing",
    "baseline": "baseline",
    "provider": "provider",
    "timeout": "timeout",
    "schema": "schema",
    "structured": "structured",
    "data": "data",
}


@dataclass
class VerifiedFinding:
    id: str
    domain: str
    severity: str
    status: FindingStatus
    title: str
    finding: str
    impact: str
    fix: str
    confidence_score: float | None
    evidence_refs: list[dict] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    source_agents: list[str] = field(default_factory=list)
    source_stage: str = "domain_review"
    dedupe_key: str = ""
    metadata: dict = field(default_factory=dict)

    def to_metadata(self) -> dict:
        return {
            "id": self.id,
            "status": self.status,
            "impact": self.impact,
            "fix": self.fix,
            "unknowns": list(self.unknowns),
            "source_agents": list(self.source_agents),
            "source_stage": self.source_stage,
            "dedupe_key": self.dedupe_key,
            **self.metadata,
        }

    def to_storage_dict(self) -> dict:
        return {
            "domain": self.domain,
            "severity": self.severity,
            "title": self.title,
            "summary": self.finding,
            "confidence": self.confidence_score,
            "evidence_refs": list(self.evidence_refs),
            "metadata": self.to_metadata(),
        }


@dataclass
class VerificationResult:
    validated_findings: list[VerifiedFinding]
    dropped_findings: list[dict]
    contradictions: list[dict]
    environment_limitations: list[dict]
    verifier_notes: list[str]

    def to_dict(self) -> dict:
        return {
            "validated_findings": [finding.to_storage_dict() for finding in self.validated_findings],
            "dropped_findings": list(self.dropped_findings),
            "contradictions": list(self.contradictions),
            "environment_limitations": list(self.environment_limitations),
            "verifier_notes": list(self.verifier_notes),
        }


def normalize_title(title: str) -> str:
    text = re.sub(r"[^a-z0-9\s]+", " ", title.lower())
    text = re.sub(r"\bno\b", "missing", text)
    text = re.sub(r"\bnot found\b", "missing", text)
    tokens: list[str] = []
    for token in text.split():
        if token in _STOP_WORDS:
            continue
        tokens.append(_SYNONYM_MAP.get(token, token))
    if "sitemap" in tokens and "missing" in tokens:
        return "sitemap missing"
    if "robots" in tokens and "missing" in tokens:
        return "robots missing"
    if "schema" in tokens and "missing" in tokens:
        return "schema missing"
    normalized = " ".join(tokens)
    normalized = normalized.replace("sitemap missing missing", "sitemap missing")
    return normalized.strip()


def build_dedupe_key(domain: str, title: str) -> str:
    normalized = normalize_title(title)
    return f"{domain}:{normalized or 'untitled'}"


def _default_impact(domain: str, severity: str, finding: str) -> str:
    if domain == "seo":
        if severity == "critical":
            return "Organic discovery is likely being suppressed by a material technical issue."
        return "Search visibility may improve more slowly until this issue is resolved."
    if domain == "community":
        return "Demand capture and community-assisted discovery may stay weak without follow-up."
    if domain == "geo":
        return "AI-native search systems may have a weaker understanding of the brand."
    if domain == "competitor":
        return "Positioning and comparison content may stay too generic versus competitors."
    return f"{finding[:1].upper()}{finding[1:]}" if finding else "This may reduce growth visibility."


def _default_fix(title: str, finding: str) -> str:
    lowered = f"{title} {finding}".lower()
    if "sitemap" in lowered:
        return "Publish sitemap.xml and reference it from robots.txt."
    if "robots" in lowered:
        return "Add a minimal robots.txt and verify that key pages remain crawlable."
    if "schema" in lowered or "structured data" in lowered:
        return "Add structured data on core marketing pages and validate it in Search Console tools."
    if "community" in lowered:
        return "Broaden monitored queries and review the highest-signal discussion threads."
    if "competitor" in lowered:
        return "Expand competitor coverage and create clearer differentiation content."
    return "Review the evidence, confirm the root cause, and schedule the smallest useful corrective action."


def upgrade_legacy_finding(finding: dict, *, source_agent: str) -> VerifiedFinding:
    title = str(finding.get("title", "")).strip()
    finding_text = str(finding.get("summary", "")).strip()
    confidence = finding.get("confidence")
    try:
        confidence_value = float(confidence) if confidence is not None else None
    except (TypeError, ValueError):
        confidence_value = None
    dedupe_key = build_dedupe_key(str(finding.get("domain", "general")), title)
    metadata = dict(finding.get("metadata") or {})
    return VerifiedFinding(
        id=metadata.get("id") or dedupe_key,
        domain=str(finding.get("domain", "general")),
        severity=str(finding.get("severity", "info")),
        status="likely",
        title=title or "Untitled finding",
        finding=finding_text,
        impact=metadata.get("impact") or _default_impact(str(finding.get("domain", "general")), str(finding.get("severity", "info")), finding_text),
        fix=metadata.get("fix") or _default_fix(title, finding_text),
        confidence_score=confidence_value,
        evidence_refs=list(finding.get("evidence_refs", [])),
        unknowns=list(metadata.get("unknowns", [])),
        source_agents=[source_agent],
        source_stage=metadata.get("source_stage", "domain_review"),
        dedupe_key=metadata.get("dedupe_key") or dedupe_key,
        metadata={k: v for k, v in metadata.items() if k not in {"impact", "fix", "unknowns", "source_stage", "dedupe_key"}},
    )


def finding_to_metadata_json(finding: VerifiedFinding) -> dict:
    return finding.to_metadata()


def finding_from_storage(row: dict) -> VerifiedFinding:
    metadata = dict(row.get("metadata") or {})
    return VerifiedFinding(
        id=metadata.get("id") or build_dedupe_key(row.get("domain", "general"), row.get("title", "")),
        domain=row.get("domain", "general"),
        severity=row.get("severity", "info"),
        status=metadata.get("status", "likely"),
        title=row.get("title", ""),
        finding=row.get("summary", ""),
        impact=metadata.get("impact", ""),
        fix=metadata.get("fix", ""),
        confidence_score=row.get("confidence"),
        evidence_refs=list(row.get("evidence_refs", [])),
        unknowns=list(metadata.get("unknowns", [])),
        source_agents=list(metadata.get("source_agents", [])),
        source_stage=metadata.get("source_stage", "domain_review"),
        dedupe_key=metadata.get("dedupe_key") or build_dedupe_key(row.get("domain", "general"), row.get("title", "")),
        metadata={k: v for k, v in metadata.items() if k not in {"status", "impact", "fix", "unknowns", "source_agents", "source_stage", "dedupe_key"}},
    )


def serialize_dataclass(value) -> dict:
    return asdict(value)

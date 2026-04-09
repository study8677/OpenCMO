from __future__ import annotations

from opencmo.finding_contract import upgrade_legacy_finding
from opencmo.finding_verifier import run_verifier_suite


def _legacy_finding(*, title: str, summary: str, confidence: float | None = 0.8, evidence_refs=None):
    return {
        "domain": "seo",
        "severity": "warning",
        "title": title,
        "summary": summary,
        "confidence": confidence,
        "evidence_refs": evidence_refs or [],
    }


def test_verifier_dedupes_and_downgrades_missing_evidence():
    findings = [
        upgrade_legacy_finding(
            _legacy_finding(
                title="Sitemap is missing",
                summary="No sitemap was detected on the primary domain.",
                evidence_refs=[{"domain": "seo", "source": "seo_scan", "key": "has_sitemap", "value": "0"}],
            ),
            source_agent="SEO Analyst",
        ),
        upgrade_legacy_finding(
            _legacy_finding(
                title="No sitemap detected",
                summary="The site does not expose sitemap.xml.",
                evidence_refs=[{"domain": "seo", "source": "seo_scan", "key": "has_sitemap", "value": "0"}],
            ),
            source_agent="SEO Analyst",
        ),
        upgrade_legacy_finding(
            _legacy_finding(
                title="Schema might be weak",
                summary="Structured data may be insufficient for rich results.",
                evidence_refs=[],
            ),
            source_agent="SEO Analyst",
        ),
    ]

    result = run_verifier_suite(findings, normalized={})

    assert len(result.validated_findings) == 2
    assert result.validated_findings[0].status == "confirmed"
    assert result.validated_findings[1].status == "hypothesis"
    assert result.dropped_findings[0]["reason"] == "duplicate"
    assert any("evidence" in note.lower() for note in result.verifier_notes)


def test_verifier_flags_environment_limitations():
    findings = [
        upgrade_legacy_finding(
            _legacy_finding(
                title="Community monitoring baseline is missing",
                summary="Provider timeout prevented community retrieval during this scan.",
                confidence=0.4,
                evidence_refs=[],
            ),
            source_agent="Community Analyst",
        )
    ]

    result = run_verifier_suite(findings, normalized={"warnings": ["reddit provider timeout"]})

    assert len(result.environment_limitations) == 1
    assert result.validated_findings[0].status == "environment_limitation"
    assert result.environment_limitations[0]["title"] == "Community monitoring baseline is missing"

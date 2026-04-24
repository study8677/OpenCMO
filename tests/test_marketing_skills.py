"""Tests for the OpenCMO marketing skill registry."""

from opencmo.marketing_skills import (
    DEFAULT_MARKETING_SKILL_ID,
    MARKETING_SKILLS_UPSTREAM_COMMIT,
    get_marketing_skill,
    list_marketing_skills,
    marketing_skill_ids,
)
from opencmo.services.blog_generation import _build_scoring_rubric


def test_marketing_skill_registry_exposes_expected_v1_skills():
    assert MARKETING_SKILLS_UPSTREAM_COMMIT == "737c3c6ea2c90c8eb977fdf2b971f02474859dc9"
    assert DEFAULT_MARKETING_SKILL_ID == "content_strategy"
    assert marketing_skill_ids() == {
        "content_strategy",
        "copywriting",
        "ai_seo",
        "competitor_alternatives",
        "programmatic_seo",
        "directory_submissions",
    }
    assert all(skill.source_url.startswith("https://github.com/coreyhaines31/marketingskills/") for skill in list_marketing_skills())


def test_marketing_skill_prompt_block_includes_framework_and_contract():
    skill = get_marketing_skill("ai_seo")
    block = skill.as_prompt_block()

    assert "Marketing Skill Framework: AI SEO" in block
    assert "Skill Output Contract" in block
    assert "FAQ" in block


def test_unknown_marketing_skill_raises_clear_error():
    try:
        get_marketing_skill("unknown")
    except ValueError as exc:
        assert "Invalid marketing skill" in str(exc)
        assert "content_strategy" in str(exc)
    else:
        raise AssertionError("Expected unknown skill to raise ValueError")


def test_scoring_rubric_adds_skill_specific_dimensions():
    skill = get_marketing_skill("competitor_alternatives")
    rubrics = _build_scoring_rubric(skill)

    assert "seo" in rubrics
    assert "comparison_fairness" in rubrics
    assert "decision_helpfulness" in rubrics

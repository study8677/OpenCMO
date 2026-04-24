"""Marketing skill registry adapted for OpenCMO content workflows."""

from opencmo.marketing_skills.registry import (
    DEFAULT_MARKETING_SKILL_ID,
    MARKETING_SKILLS_UPSTREAM_COMMIT,
    MarketingSkill,
    get_marketing_skill,
    list_marketing_skills,
    marketing_skill_ids,
)

__all__ = [
    "DEFAULT_MARKETING_SKILL_ID",
    "MARKETING_SKILLS_UPSTREAM_COMMIT",
    "MarketingSkill",
    "get_marketing_skill",
    "list_marketing_skills",
    "marketing_skill_ids",
]

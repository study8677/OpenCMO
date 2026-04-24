"""Structured marketing skill prompts for OpenCMO.

Adapted from coreyhaines31/marketingskills at commit
737c3c6ea2c90c8eb977fdf2b971f02474859dc9.

Upstream license: MIT. See https://github.com/coreyhaines31/marketingskills.
The content below is a compact OpenCMO-specific adaptation, not a verbatim copy
of the source skill files.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

MARKETING_SKILLS_UPSTREAM_REPO = "https://github.com/coreyhaines31/marketingskills"
MARKETING_SKILLS_UPSTREAM_COMMIT = "737c3c6ea2c90c8eb977fdf2b971f02474859dc9"
DEFAULT_MARKETING_SKILL_ID = "content_strategy"


@dataclass(frozen=True)
class MarketingSkill:
    id: str
    name: str
    source_path: str
    description: str
    prompt_overlay: str
    output_contract: str
    quality_rubrics: Mapping[str, str]

    @property
    def source_url(self) -> str:
        return f"{MARKETING_SKILLS_UPSTREAM_REPO}/tree/{MARKETING_SKILLS_UPSTREAM_COMMIT}/{self.source_path}"

    def to_public_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "source_path": self.source_path,
            "source_url": self.source_url,
            "source_commit": MARKETING_SKILLS_UPSTREAM_COMMIT,
            "license": "MIT",
        }

    def as_prompt_block(self) -> str:
        return "\n\n".join(
            [
                f"## Marketing Skill Framework: {self.name}",
                self.prompt_overlay.strip(),
                "## Skill Output Contract",
                self.output_contract.strip(),
            ]
        )


_COMMON_RUBRIC_SUFFIX = (
    'Return ONLY a JSON object: {"score": <number>, "reasoning": "<brief explanation>"}'
)


_SKILLS: dict[str, MarketingSkill] = {
    "content_strategy": MarketingSkill(
        id="content_strategy",
        name="Content Strategy",
        source_path="skills/content-strategy",
        description="Plans searchable or shareable content from product, audience, keyword, and competitor signals.",
        prompt_overlay="""\
Use the draft to advance a content strategy, not just a one-off article.
Choose whether the piece is primarily searchable, shareable, or both.
Tie the topic to a buyer stage, target query, customer problem, and product-led angle.
Prefer topic clusters, internal-link opportunities, and next content ideas over isolated advice.
""",
        output_contract="""\
Produce a publishable markdown draft with a clear H1, useful sections, and a short final section named "Content Strategy Notes" that lists target query, buyer stage, content type, and next internal links.
""",
        quality_rubrics={
            "strategy_fit": f"""\
Score how well this draft fits a coherent content strategy (0-100).

Criteria:
- Clear searchable/shareable purpose
- Strong match to customer problem and product value
- Buyer-stage fit is obvious
- Suggests useful internal links or cluster follow-ups

{_COMMON_RUBRIC_SUFFIX}
""",
        },
    ),
    "copywriting": MarketingSkill(
        id="copywriting",
        name="Conversion Copywriting",
        source_path="skills/copywriting",
        description="Improves persuasive clarity, CTA quality, benefit framing, and page-ready marketing copy.",
        prompt_overlay="""\
Write like a conversion copywriter: clarity over cleverness, concrete benefits over feature lists, and customer language over company language.
Make the opening value proposition immediately obvious.
Use specific outcomes, objection handling, and a direct CTA.
Remove vague marketing filler.
""",
        output_contract="""\
Produce a publishable markdown draft. Include strong headline/subheadline logic in the opening, benefit-led sections, objection handling, and a concise CTA section.
""",
        quality_rubrics={
            "conversion_clarity": f"""\
Score this draft's conversion copy quality (0-100).

Criteria:
- The main value proposition is clear in the first section
- Benefits are specific and tied to outcomes
- Objections are handled without hype
- CTA is direct and relevant

{_COMMON_RUBRIC_SUFFIX}
""",
        },
    ),
    "ai_seo": MarketingSkill(
        id="ai_seo",
        name="AI SEO",
        source_path="skills/ai-seo",
        description="Shapes content for answer engines, LLM citation, extractable passages, and schema-ready structure.",
        prompt_overlay="""\
Optimize for AI search and answer engines.
Use extractable answer blocks, direct definitions, comparison tables when useful, factual statements, source-aware phrasing, FAQ-style questions, and freshness cues.
Avoid keyword stuffing. Make each important paragraph understandable out of context.
""",
        output_contract="""\
Produce a publishable markdown draft with direct answer sections, an FAQ section, and an "AI Citation Readiness" section listing recommended schema, citable claims, and missing proof points.
""",
        quality_rubrics={
            "extractability": f"""\
Score this draft's AI-answer extractability (0-100).

Criteria:
- Key answers work as standalone passages
- Headings match natural-language queries
- Tables, lists, or FAQs are used where they improve extraction
- Claims are specific and easy for AI systems to cite

{_COMMON_RUBRIC_SUFFIX}
""",
            "citation_readiness": f"""\
Score this draft's citation readiness (0-100).

Criteria:
- Includes citable facts, dates, or proof points where available
- Avoids unsupported exaggerated claims
- Calls out missing evidence instead of inventing it
- Suggests schema or machine-readable follow-ups

{_COMMON_RUBRIC_SUFFIX}
""",
        },
    ),
    "competitor_alternatives": MarketingSkill(
        id="competitor_alternatives",
        name="Competitor Alternatives",
        source_path="skills/competitor-alternatives",
        description="Creates honest alternative, comparison, and decision-helper content for competitor-intent searches.",
        prompt_overlay="""\
Write for readers comparing tools.
Be fair about competitor strengths and product limitations.
Go beyond a feature checklist: explain why differences matter by use case.
Make the decision framework practical for someone evaluating alternatives.
""",
        output_contract="""\
Produce a publishable markdown comparison or alternative draft with TL;DR, evaluation criteria, comparison sections, "choose this if" guidance, migration notes, and FAQ-ready questions.
""",
        quality_rubrics={
            "comparison_fairness": f"""\
Score this draft's comparison fairness (0-100).

Criteria:
- Competitor strengths are acknowledged
- Claims are qualified when evidence is missing
- The draft helps readers choose, not just sell
- Limitations and best-fit scenarios are clear

{_COMMON_RUBRIC_SUFFIX}
""",
            "decision_helpfulness": f"""\
Score how helpful this draft is for a buyer decision (0-100).

Criteria:
- Criteria are explicit and relevant
- Use-case recommendations are concrete
- Pricing, migration, or adoption concerns are addressed when data exists
- The final recommendation is easy to scan

{_COMMON_RUBRIC_SUFFIX}
""",
        },
    ),
    "programmatic_seo": MarketingSkill(
        id="programmatic_seo",
        name="Programmatic SEO",
        source_path="skills/programmatic-seo",
        description="Turns repeatable keyword patterns into page templates, data requirements, and quality checks.",
        prompt_overlay="""\
Think in scalable page patterns, but avoid thin content.
Identify the repeating keyword pattern, variables, unique data needed per page, internal-link architecture, and indexation risk.
Prioritize fewer high-value pages over many weak pages.
""",
        output_contract="""\
Produce a markdown strategy draft with page pattern, URL/title/meta templates, data fields, sample page outline, internal linking plan, and quality checks before publishing.
""",
        quality_rubrics={
            "template_viability": f"""\
Score this draft's programmatic SEO viability (0-100).

Criteria:
- Repeating pattern and variables are clear
- Every page can have unique value
- Data requirements are realistic
- Internal linking and indexation considerations are included

{_COMMON_RUBRIC_SUFFIX}
""",
        },
    ),
    "directory_submissions": MarketingSkill(
        id="directory_submissions",
        name="Directory Submissions",
        source_path="skills/directory-submissions",
        description="Builds directory-launch readiness, destination page priorities, positioning variants, and tracker-ready assets.",
        prompt_overlay="""\
Treat directories as a distribution foundation, not the whole strategy.
Check whether destination pages, screenshots, pricing, legal pages, structured data, and review readiness exist.
Vary positioning by directory type instead of repeating one description.
Prioritize the pages that backlinks should point to before submission.
""",
        output_contract="""\
Produce a markdown action plan with readiness checklist, destination pages to build first, directory tier priority, positioning variants, review plan, and tracker fields.
""",
        quality_rubrics={
            "readiness": f"""\
Score this directory submission plan's readiness discipline (0-100).

Criteria:
- Hard blockers are separated from nice-to-haves
- Destination pages are prioritized before submissions
- Required assets are explicit
- The plan avoids spam directories and duplicate positioning

{_COMMON_RUBRIC_SUFFIX}
""",
            "distribution_fit": f"""\
Score this plan's distribution fit (0-100).

Criteria:
- Directory tiers match the product category
- Positioning varies by audience
- Review and launch timing are practical
- KPIs connect backlinks to traffic, citations, or signups

{_COMMON_RUBRIC_SUFFIX}
""",
        },
    ),
}


def marketing_skill_ids() -> set[str]:
    return set(_SKILLS)


def list_marketing_skills() -> list[MarketingSkill]:
    return list(_SKILLS.values())


def get_marketing_skill(skill_id: str | None) -> MarketingSkill:
    normalized = (skill_id if isinstance(skill_id, str) else DEFAULT_MARKETING_SKILL_ID).strip() or DEFAULT_MARKETING_SKILL_ID
    if normalized not in _SKILLS:
        valid = ", ".join(sorted(_SKILLS))
        raise ValueError(f"Invalid marketing skill '{normalized}'. Must be one of: {valid}")
    return _SKILLS[normalized]

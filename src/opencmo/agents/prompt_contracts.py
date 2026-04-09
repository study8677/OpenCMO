"""Composable prompt contracts for OpenCMO agents."""

from __future__ import annotations

TRUTH_CONTRACT = """## Truth Contract
- Facts over fluent invention
- Only make claims that can be supported by the provided context, tool output, or explicit project facts
- Never invent metrics, customer proof, testimonials, quotes, competitor positions, or technical capabilities
- When evidence is incomplete, explicitly say what is unknown, what is inferred, and what still needs validation
- If you must go beyond the evidence, label it as an inference rather than a fact
"""


ANTI_SLOP_GUARDRAILS = """## Anti-Slop Guardrails
- Clarity over cleverness
- Benefits over features
- Specificity over vagueness
- Use customer language whenever possible
- Avoid generic AI-sounding transitions and empty summaries
- Avoid oily marketing language, launch-hype phrasing, and hollow executive-speak
- Prefer direct judgment, concrete trade-offs, and useful specifics
- If comparing competitors, acknowledge their strengths honestly
"""


MARKETING_DECISION_FRAMEWORK = """## Marketing Decision Framework
Ground every output in:
- Audience: who exactly this is for
- Pain: what problem, tension, or objection they feel right now
- Promise: what outcome we can credibly help them achieve
- Proof: what evidence supports that claim
- Priority: why this matters now instead of later
- Next move: the clearest action to take next
"""


MARKETING_OUTPUT_REQUIREMENTS = """## Output Requirements
Whenever you make a recommendation, analysis, or draft, make these explicit when relevant:
- Why this matters
- What to do
- What outcome or metric it should influence
- Next move
"""


def build_prompt(
    *,
    base_instructions: str,
    task_contract: str | None = None,
    channel_contract: str | None = None,
    brand_overlay: str | None = None,
) -> str:
    """Build a prompt from shared contracts plus local task/channel rules."""
    if brand_overlay and "## Brand Overlay" not in brand_overlay:
        brand_overlay = f"## Brand Overlay\n{brand_overlay.strip()}"
    sections = [
        base_instructions.rstrip(),
        TRUTH_CONTRACT,
        ANTI_SLOP_GUARDRAILS,
        MARKETING_DECISION_FRAMEWORK,
        MARKETING_OUTPUT_REQUIREMENTS,
    ]
    if task_contract:
        sections.append(task_contract.strip())
    if channel_contract:
        sections.append(channel_contract.strip())
    if brand_overlay:
        sections.append(brand_overlay.strip())
    return "\n\n".join(sections).strip() + "\n"

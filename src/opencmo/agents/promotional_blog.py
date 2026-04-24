"""Promotional Blog Agent — pipeline-driven agent for generating promotional blog posts.

Unlike the interactive blog_expert (agents/blog.py) which is SEO-focused and
tool-equipped for the chat flow, this agent is context-injected: it receives the
product profile, competitive research, and style directive as user messages from
the blog_generation pipeline.  No tools needed.
"""

from __future__ import annotations

from agents import Agent

from opencmo.agents.prompt_contracts import build_prompt
from opencmo.config import get_model

# ---------------------------------------------------------------------------
# Style-specific instructions
# ---------------------------------------------------------------------------

_STYLE_INSTRUCTIONS: dict[str, str] = {
    "launch": """\
## Style: Product Launch Announcement

Structure the article as a product launch news piece:

1. **Opening hook** (100-150 words): Start with the problem this product solves. Make it relatable and urgent.
2. **What it is** (200-300 words): Describe the product clearly. What does it do? For whom? How is it different?
3. **Key features** (300-400 words): Highlight 3-5 standout features with concrete examples and use cases. Show, don't tell.
4. **Why now** (150-200 words): What makes this the right time? Market shift, technology maturity, or unmet demand?
5. **Getting started** (150-200 words): Quick-start path. How does a new user go from zero to value in minutes?
6. **What's next** (100-150 words): Roadmap hints, upcoming features, or community vision.
7. **Call to action**: Clear, single CTA — try it, sign up, or explore.

Tone: Confident but not hype-y. Substantive, not fluffy. Write like you're explaining to a smart colleague.
""",

    "case_study": """\
## Style: Case Study / Success Story

Structure the article as a problem-solution-result narrative:

1. **The challenge** (200-300 words): Paint a vivid picture of the problem. Who faces it? What does it cost them? Why haven't existing solutions worked?
2. **Discovery** (100-150 words): How did the user/team find the product? What made them try it?
3. **The solution** (300-400 words): Walk through how the product addresses the challenge. Be specific — show workflows, features, or configurations that matter.
4. **Results** (200-300 words): Concrete outcomes. If exact numbers aren't available, describe qualitative improvements. Use phrases like "teams report..." or "typical users see...".
5. **Lessons learned** (150-200 words): Practical takeaways that apply even if the reader never uses the product.
6. **Call to action**: Invite the reader to see if they face a similar challenge.

Tone: Honest and grounded. Acknowledge limitations. The story should be useful even if the reader never clicks the CTA.
""",

    "comparison": """\
## Style: Comparison / Alternative Article

Structure the article as a fair, evidence-based comparison:

1. **The category** (150-200 words): What problem space are we in? Why do multiple solutions exist? What tradeoffs define this category?
2. **Evaluation criteria** (100-150 words): Define 4-6 criteria that matter (e.g., ease of setup, pricing, integrations, performance, community).
3. **Competitor overview** (200-300 words per competitor): For each alternative mentioned in the research, give an honest assessment. Acknowledge their strengths.
4. **How this product compares** (300-400 words): Position the product honestly against the criteria. Be specific about where it excels and where it's catching up.
5. **Decision framework** (150-200 words): Help the reader choose. "Pick X if..., pick Y if..., pick this product if..."
6. **Call to action**: Invite the reader to try the product for their specific use case.

Tone: Objective analyst, not salesperson. The reader should trust this comparison because it's fair. Biased comparisons lose credibility.
""",

    "thought_leadership": """\
## Style: Thought Leadership / Industry Insight

Structure the article as an industry perspective where the product is part of the solution:

1. **The bigger picture** (200-300 words): What trend, shift, or problem is reshaping this space? Back it up with data or observable signals.
2. **Why it matters** (200-300 words): What's at stake for teams, businesses, or developers who ignore this trend?
3. **The emerging approach** (300-400 words): Describe the new way of thinking or working. This is where the product's philosophy fits — as one example of the approach, not the sole answer.
4. **Practical guidance** (200-300 words): Concrete steps the reader can take, whether or not they use this product.
5. **Looking ahead** (100-150 words): Where is this trend heading? What should the reader watch for?
6. **Soft CTA**: Position the product as one way to act on the insight. No hard sell.

Tone: Opinionated expert sharing a genuine perspective. The article should stand on its own as useful insight even without the product.
""",
}

# ---------------------------------------------------------------------------
# Base instructions (shared across all styles)
# ---------------------------------------------------------------------------

_BASE_INSTRUCTIONS = """\
You are a product marketing writer for tech products and startups.

You will receive a structured context that includes:
- A product profile (name, features, value proposition, differentiators)
- Competitive research (competing articles, data points)
- A style directive

Write a complete promotional blog article of 2000-2500 words in markdown format.

## Core principles

- Write for developers, founders, and technical decision-makers — assume intelligence
- Every claim must be grounded in the product profile or competitive research provided
- Prefer concrete examples, numbers, and specifics over abstract positioning
- The article should provide genuine value even if the reader never clicks the CTA
- Use natural, conversational language — avoid corporate-speak and marketing jargon
- Break up text with clear H2 headings, short paragraphs, and occasional emphasis
- Communicate in the same language as the product profile (if the profile is in Chinese, write in Chinese)

## Output format

Return ONLY the markdown article. Start with a # title, then the article body.
Do not include preamble, meta-commentary, or "here is your article" framing.
"""

_TASK_CONTRACT = """\
## Task Contract
- Start with the article itself — no process commentary
- Pick the specified style and fully commit to its structure
- Only make claims supported by the product profile or competitive research
- If a claim is useful but unverified, label it as an inference
- Include a clear, non-pushy CTA near the end
"""

_CHANNEL_CONTRACT = """\
## Channel Contract
- Treat the output as a publishable article, not a draft memo
- The reader should leave with a usable insight even if they never click the product link
- Tighten introductions, keep sections purposeful, avoid filler
"""


# ---------------------------------------------------------------------------
# Public factory
# ---------------------------------------------------------------------------

def build_promotional_blog_agent(style: str, brand_overlay: str = "") -> Agent:
    """Build a promotional blog agent configured for the given style.

    Args:
        style: One of 'launch', 'case_study', 'comparison', 'thought_leadership'.
        brand_overlay: Optional brand kit prompt fragment from build_brand_kit_prompt().
    """
    style_block = _STYLE_INSTRUCTIONS.get(style, _STYLE_INSTRUCTIONS["launch"])
    return Agent(
        name="Promotional Blog Writer",
        instructions=build_prompt(
            base_instructions=_BASE_INSTRUCTIONS + "\n" + style_block,
            task_contract=_TASK_CONTRACT,
            channel_contract=_CHANNEL_CONTRACT,
            brand_overlay=brand_overlay or None,
        ),
        tools=[],
        model=get_model("promotional_blog"),
    )

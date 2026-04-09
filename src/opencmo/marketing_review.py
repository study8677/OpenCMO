"""Shared LLM-based marketing output review for agent final responses."""

from __future__ import annotations

import json

from opencmo import llm

_REVIEWED_AGENT_NAMES = {
    "CMO Agent",
    "Community Monitor",
    "SEO Audit Expert",
    "Trend Research",
    "Blog SEO Expert",
    "AI Visibility Expert",
    "Twitter Expert",
    "Reddit Expert",
    "LinkedIn Expert",
    "Product Hunt Expert",
    "Hacker News Expert",
    "Devto Expert",
    "Zhihu Expert",
    "Xiaohongshu Expert",
    "V2EX Expert",
    "Juejin Expert",
    "Jike Expert",
    "WeChat Expert",
    "OSChina Expert",
    "GitCode Expert",
    "Sspai Expert",
    "InfoQ Expert",
    "Ruanyifeng Weekly Expert",
}

_PROFILE_MAP = {
    "CMO Agent": "strategic_marketing",
    "Community Monitor": "community_social",
    "SEO Audit Expert": "seo_growth",
    "Trend Research": "trend_strategy",
    "Blog SEO Expert": "longform_content",
    "AI Visibility Expert": "positioning_strategy",
    "Twitter Expert": "community_social",
    "Reddit Expert": "community_social",
    "LinkedIn Expert": "professional_social",
    "Product Hunt Expert": "launch_positioning",
    "Hacker News Expert": "technical_launch",
    "Devto Expert": "longform_content",
    "Zhihu Expert": "longform_content",
    "Xiaohongshu Expert": "community_social",
    "V2EX Expert": "community_social",
    "Juejin Expert": "longform_content",
    "Jike Expert": "community_social",
    "WeChat Expert": "longform_content",
    "OSChina Expert": "technical_launch",
    "GitCode Expert": "technical_launch",
    "Sspai Expert": "longform_content",
    "InfoQ Expert": "technical_launch",
    "Ruanyifeng Weekly Expert": "technical_launch",
}

_PROFILE_GUIDANCE = {
    "strategic_marketing": "Strengthen strategic framing, differentiation, prioritization, and business trade-offs.",
    "community_social": "Reduce marketing tone, make the voice more human, useful, and natively community-friendly.",
    "professional_social": "Increase clarity, proof, and executive relevance while keeping the tone concise and professional.",
    "seo_growth": "Tie technical findings to demand capture, rankings, and practical growth outcomes.",
    "trend_strategy": "Separate noise from signal, clarify why the trend matters now, and turn insight into content or channel actions.",
    "longform_content": "Make the writing more vivid, specific, and naturally persuasive while preserving structure and utility.",
    "positioning_strategy": "Sharpen market positioning, recommendation potential, and why the brand should be cited or remembered.",
    "launch_positioning": "Make the launch framing clearer, more differentiated, and more grounded in user value.",
    "technical_launch": "Keep credibility high, avoid hype, and make the technical and practical value easier to grasp.",
}

_REVIEW_SYSTEM = """You are a senior product-marketing editor reviewing outputs from specialized marketing agents.

Apply a light-touch editorial pass so the draft is stronger on:
- audience clarity
- pain/problem articulation
- promised outcome
- proof/evidence framing
- priority and urgency
- next action clarity
- natural, human marketing language

Hard constraints:
- Preserve the original language
- Preserve all factual claims unless they are unsupported by the draft itself
- Preserve code blocks, URLs, markdown structure, and platform-specific constraints
- Do not materially restructure the draft unless clarity is broken
- Do not add fabricated metrics, testimonials, customers, or competitive claims
- Do not mention that you are reviewing or editing the draft
- If the draft is already strong, make only light edits

Return valid JSON with this shape only:
{
  "revised_output": "final revised output",
  "weak_points": ["audience" | "pain" | "promise" | "proof" | "priority" | "next_move" | "clarity" | "customer_language" | "anti_ai_tone"]
}"""


def get_marketing_review_profile(agent_name: str | None) -> str:
    return _PROFILE_MAP.get(agent_name or "", "general_marketing")


def should_review_marketing_output(agent_name: str | None, output_text: str) -> bool:
    if not agent_name or agent_name not in _REVIEWED_AGENT_NAMES:
        return False
    if not output_text or len(output_text.strip()) < 40:
        return False
    return True


async def review_marketing_output_with_metadata(
    *,
    agent_name: str | None,
    user_message: str,
    output_text: str,
) -> dict:
    """Run a final marketing-language refinement pass when configured."""
    if not should_review_marketing_output(agent_name, output_text):
        return {
            "final_output": output_text,
            "review_applied": False,
            "profile": get_marketing_review_profile(agent_name),
            "weak_points": [],
        }

    api_key = await llm.get_key_async("OPENAI_API_KEY")
    if not api_key:
        return {
            "final_output": output_text,
            "review_applied": False,
            "profile": get_marketing_review_profile(agent_name),
            "weak_points": [],
        }

    profile = get_marketing_review_profile(agent_name)
    profile_guidance = _PROFILE_GUIDANCE.get(profile, "Improve clarity and persuasion while preserving facts.")

    user_prompt = (
        f"Agent: {agent_name}\n\n"
        f"Review profile: {profile}\n"
        f"Profile guidance: {profile_guidance}\n\n"
        f"User request:\n{user_message}\n\n"
        f"Draft output:\n{output_text}"
    )
    try:
        revised = await llm.chat_completion(
            _REVIEW_SYSTEM,
            user_prompt,
            temperature=0.2,
            timeout=90,
        )
    except Exception:
        return {
            "final_output": output_text,
            "review_applied": False,
            "profile": profile,
            "weak_points": [],
        }

    try:
        parsed = json.loads(revised)
    except json.JSONDecodeError:
        cleaned = revised.strip()
        if cleaned:
            return {
                "final_output": cleaned,
                "review_applied": True,
                "profile": profile,
                "weak_points": [],
            }
        return {
            "final_output": output_text,
            "review_applied": False,
            "profile": profile,
            "weak_points": [],
        }

    final_output = str(parsed.get("revised_output", "")).strip() or output_text
    weak_points = parsed.get("weak_points", [])
    if not isinstance(weak_points, list):
        weak_points = []

    return {
        "final_output": final_output,
        "review_applied": True,
        "profile": profile,
        "weak_points": [str(item) for item in weak_points[:5]],
    }


async def review_marketing_output(
    *,
    agent_name: str | None,
    user_message: str,
    output_text: str,
) -> str:
    result = await review_marketing_output_with_metadata(
        agent_name=agent_name,
        user_message=user_message,
        output_text=output_text,
    )
    return result["final_output"]

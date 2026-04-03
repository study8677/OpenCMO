"""Text signal extraction — sentiment, citation quality, and recommendation analysis."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SentimentSignal:
    """Extracted sentiment signal from AI platform snippets."""

    score: int | None  # 0-30 when available
    label: str  # "positive", "neutral", "negative", "not_mentioned", "unavailable"
    reasoning: str  # brief explanation


def _get_llm_client():
    from openai import AsyncOpenAI

    from opencmo import llm

    return AsyncOpenAI(
        api_key=llm.get_key("OPENAI_API_KEY"),
        base_url=llm.get_key("OPENAI_BASE_URL") or None,
    )


def _get_model() -> str:
    from opencmo import llm
    return llm.get_key("OPENCMO_MODEL_DEFAULT", "gpt-4o")


async def analyze_geo_sentiment(
    brand_name: str,
    snippets: dict[str, str],
) -> SentimentSignal:
    """Analyze sentiment of brand mentions across AI platform snippets.

    Args:
        brand_name: The brand to analyze sentiment for.
        snippets: Mapping of platform_name -> content_snippet text.

    Returns:
        SentimentSignal with score (0-30), label, and reasoning.
    """
    if not snippets:
        return SentimentSignal(score=0, label="not_mentioned", reasoning="No snippets available")

    # Build a combined context from all snippets (cap at 6000 chars total)
    combined = []
    budget = 6000
    for platform, text in snippets.items():
        if not text:
            continue
        chunk = text[:1500]
        if len("\n".join(combined)) + len(chunk) > budget:
            break
        combined.append(f"[{platform}]\n{chunk}")

    if not combined:
        return SentimentSignal(score=0, label="not_mentioned", reasoning="All snippets empty")

    context = "\n\n".join(combined)

    try:
        client = _get_llm_client()
        model = _get_model()

        resp = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You analyze how AI search platforms talk about a brand. "
                        "Given snippets from multiple AI platforms, assess the sentiment "
                        "toward the specified brand.\n\n"
                        "Return ONLY a JSON object with these fields:\n"
                        '- "label": one of "positive", "neutral", "negative", "not_mentioned"\n'
                        '- "score": integer 0-30 where:\n'
                        "  - 25-30: strong recommendation, featured prominently, praised\n"
                        "  - 18-24: mentioned positively, listed as a good option\n"
                        "  - 10-17: mentioned neutrally, listed without strong opinion\n"
                        "  - 5-9: mentioned with caveats, warnings, or compared unfavorably\n"
                        "  - 0-4: negative sentiment, criticized, or not mentioned at all\n"
                        '- "reasoning": one sentence explaining your assessment\n\n'
                        "No markdown fences. Just the JSON object."
                    ),
                },
                {
                    "role": "user",
                    "content": f'Brand: "{brand_name}"\n\nSnippets:\n{context}',
                },
            ],
            temperature=0.3,
        )

        text = resp.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]

        result = json.loads(text.strip())
        raw_score = result.get("score")
        score = max(0, min(30, int(raw_score))) if raw_score is not None else None
        label = result.get("label", "unavailable")
        reasoning = result.get("reasoning", "")

        return SentimentSignal(score=score, label=label, reasoning=reasoning)

    except Exception as exc:
        logger.debug("Sentiment analysis failed for %s", brand_name, exc_info=True)
        return SentimentSignal(
            score=None,
            label="unavailable",
            reasoning=f"Sentiment analysis unavailable: {exc}",
        )

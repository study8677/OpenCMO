"""Citability scorer — rates content blocks for AI citation readiness.

Inspired by geo-seo-claude (https://github.com/zubair-trabzada/geo-seo-claude).
Based on research showing AI-cited passages are typically 134-167 words,
self-contained, fact-rich, and structurally clear.
"""

from __future__ import annotations

import json
import logging
import re

from agents import function_tool

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Scoring weights
# --------------------------------------------------------------------------
_W_ANSWER_QUALITY = 0.30
_W_SELF_CONTAINED = 0.25
_W_READABILITY = 0.20
_W_STAT_DENSITY = 0.15
_W_UNIQUENESS = 0.10

# Regex patterns
_DEFINITION_RE = re.compile(
    r"\b(is|are|refers to|means|defined as|consists of)\b", re.I
)
_QUESTION_RE = re.compile(r"\?")
_CLAIM_RE = re.compile(
    r"\b(research shows|studies indicate|according to|data suggests|evidence shows|"
    r"experts agree|analysis reveals|statistics show)\b", re.I,
)
_PRONOUN_RE = re.compile(r"\b(it|this|that|these|those|they|them|he|she|its)\b", re.I)
_NAMED_ENTITY_RE = re.compile(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)+\b")
_STAT_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?%|\$\d+|\d{4}\b|\d+(?:\.\d+)?\s*(?:x|times|percent|million|billion|users|customers)")
_LIST_RE = re.compile(r"^[\s]*(?:\d+[\.\):]|[-*•])\s", re.M)
_ORIGINAL_RE = re.compile(
    r"\b(our research|we found|our data|case study|our analysis|we tested|"
    r"our team|in our experience|we observed|our survey)\b", re.I,
)


def _score_answer_quality(text: str, heading: str | None) -> float:
    """Score how well the block directly answers a question (0-100)."""
    score = 0.0
    # Heading is a question
    if heading and _QUESTION_RE.search(heading):
        score += 25
    # Contains definition pattern early (first 200 chars)
    if _DEFINITION_RE.search(text[:200]):
        score += 30
    elif _DEFINITION_RE.search(text):
        score += 15
    # Contains research/evidence claims
    claims = len(_CLAIM_RE.findall(text))
    score += min(claims * 10, 25)
    # Starts with a direct statement (not a pronoun)
    first_word = text.split()[0] if text.split() else ""
    if first_word and not _PRONOUN_RE.match(first_word):
        score += 10
    # Has numbered steps or list structure
    if _LIST_RE.search(text):
        score += 10
    return min(score, 100)


def _score_self_containment(text: str) -> float:
    """Score how well the block stands alone (0-100)."""
    words = text.split()
    word_count = len(words)
    score = 0.0

    # Optimal length: 134-167 words
    if 134 <= word_count <= 167:
        score += 40
    elif 100 <= word_count <= 250:
        score += 25
    elif 50 <= word_count <= 300:
        score += 15
    elif word_count < 30:
        score += 0
    else:
        score += 10

    # Pronoun density — lower is better for self-containment
    pronouns = len(_PRONOUN_RE.findall(text))
    pronoun_pct = pronouns / max(word_count, 1) * 100
    if pronoun_pct < 2:
        score += 30
    elif pronoun_pct < 5:
        score += 20
    elif pronoun_pct < 8:
        score += 10

    # Named entities — more = more self-contained
    entities = len(_NAMED_ENTITY_RE.findall(text))
    score += min(entities * 5, 30)

    return min(score, 100)


def _score_readability(text: str) -> float:
    """Score structural readability (0-100)."""
    score = 0.0
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    # Sentence count
    if 3 <= len(sentences) <= 8:
        score += 30
    elif 2 <= len(sentences) <= 12:
        score += 20
    else:
        score += 10

    # Sentence length variety
    lengths = [len(s.split()) for s in sentences]
    if lengths:
        avg_len = sum(lengths) / len(lengths)
        if 10 <= avg_len <= 25:
            score += 25
        elif 8 <= avg_len <= 30:
            score += 15

    # Has lists or structured content
    if _LIST_RE.search(text):
        score += 20

    # Has bold/italic markers (markdown)
    if re.search(r'\*\*[^*]+\*\*', text) or re.search(r'\*[^*]+\*', text):
        score += 15

    # Structural keywords
    if re.search(r'\b(first|second|third|finally|in conclusion|for example|such as)\b', text, re.I):
        score += 10

    return min(score, 100)


def _score_statistical_density(text: str) -> float:
    """Score presence of statistics, numbers, dates (0-100)."""
    stats = len(_STAT_NUMBER_RE.findall(text))
    score = min(stats * 15, 60)

    # Percentage mentions
    pct_count = len(re.findall(r'\d+(?:\.\d+)?%', text))
    score += min(pct_count * 10, 20)

    # Year references (2020-2030)
    years = len(re.findall(r'\b20[2-3]\d\b', text))
    score += min(years * 10, 20)

    return min(score, 100)


def _score_uniqueness(text: str) -> float:
    """Score uniqueness signals — original research, case studies (0-100)."""
    score = 0.0

    # Original research indicators
    originals = len(_ORIGINAL_RE.findall(text))
    score += min(originals * 20, 40)

    # Specific tool/product/brand names (capitalized words)
    proper_nouns = len(re.findall(r'\b[A-Z][a-z]{2,}\b', text))
    score += min(proper_nouns * 3, 30)

    # Quoted sources
    if re.search(r'"[^"]{10,}"', text):
        score += 15

    # Specific numbers (not generic)
    if re.search(r'\d{3,}', text):
        score += 15

    return min(score, 100)


def _score_passage(text: str, heading: str | None = None) -> dict:
    """Score a single text passage on 5 dimensions. Returns breakdown dict."""
    text = text.strip()
    if not text or len(text.split()) < 15:
        return {
            "total_score": 0, "grade": "F", "word_count": len(text.split()),
            "preview": text[:80],
            "breakdown": {
                "answer_quality": 0, "self_containment": 0,
                "readability": 0, "statistical_density": 0, "uniqueness": 0,
            },
        }

    aq = _score_answer_quality(text, heading)
    sc = _score_self_containment(text)
    rd = _score_readability(text)
    sd = _score_statistical_density(text)
    uq = _score_uniqueness(text)

    total = (
        aq * _W_ANSWER_QUALITY
        + sc * _W_SELF_CONTAINED
        + rd * _W_READABILITY
        + sd * _W_STAT_DENSITY
        + uq * _W_UNIQUENESS
    )

    if total >= 80:
        grade = "A"
    elif total >= 65:
        grade = "B"
    elif total >= 50:
        grade = "C"
    elif total >= 35:
        grade = "D"
    else:
        grade = "F"

    return {
        "total_score": round(total, 1),
        "grade": grade,
        "word_count": len(text.split()),
        "heading": heading or "(no heading)",
        "preview": text[:120].replace("\n", " "),
        "breakdown": {
            "answer_quality": round(aq, 1),
            "self_containment": round(sc, 1),
            "readability": round(rd, 1),
            "statistical_density": round(sd, 1),
            "uniqueness": round(uq, 1),
        },
    }


def _split_markdown_blocks(markdown: str) -> list[tuple[str | None, str]]:
    """Split markdown into (heading, content) blocks."""
    blocks: list[tuple[str | None, str]] = []
    current_heading: str | None = None
    current_lines: list[str] = []

    for line in markdown.splitlines():
        heading_match = re.match(r'^(#{1,4})\s+(.+)', line)
        if heading_match:
            # Save previous block
            text = "\n".join(current_lines).strip()
            if text and len(text.split()) >= 15:
                blocks.append((current_heading, text))
            current_heading = heading_match.group(2)
            current_lines = []
        else:
            current_lines.append(line)

    # Last block
    text = "\n".join(current_lines).strip()
    if text and len(text.split()) >= 15:
        blocks.append((current_heading, text))

    return blocks


async def _citability_impl(url: str) -> dict:
    """Core implementation — returns structured dict."""
    from opencmo.tools.crawl import fetch_url_content

    try:
        content, _source = await fetch_url_content(url, max_chars=50000)
    except Exception as exc:
        return {"error": str(exc), "url": url, "avg_score": 0, "blocks": []}

    if not content or len(content.strip()) < 100:
        return {"error": "No usable content found", "url": url, "avg_score": 0, "blocks": []}

    blocks = _split_markdown_blocks(content)
    if not blocks:
        # Fallback: split by double newlines
        paragraphs = [p.strip() for p in content.split("\n\n") if len(p.split()) >= 15]
        blocks = [(None, p) for p in paragraphs]

    scored = [_score_passage(text, heading) for heading, text in blocks]
    scored = [s for s in scored if s["total_score"] > 0]

    if not scored:
        return {"error": "No scoreable blocks found", "url": url, "avg_score": 0, "blocks": []}

    scored.sort(key=lambda s: s["total_score"], reverse=True)

    avg_score = sum(s["total_score"] for s in scored) / len(scored)
    grade_dist = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for s in scored:
        grade_dist[s["grade"]] = grade_dist.get(s["grade"], 0) + 1

    optimal_count = sum(1 for s in scored if 134 <= s["word_count"] <= 167)

    return {
        "url": url,
        "avg_score": round(avg_score, 1),
        "total_blocks": len(scored),
        "optimal_length_blocks": optimal_count,
        "grade_distribution": grade_dist,
        "top_blocks": scored[:3],
        "bottom_blocks": scored[-3:] if len(scored) > 3 else [],
        "all_scores": [s["total_score"] for s in scored],
    }


def _format_report(data: dict) -> str:
    """Format citability analysis as markdown."""
    if data.get("error"):
        return f"## Citability Analysis Failed\n\n{data['error']}"

    lines = [f"## Citability Score Report — {data['url']}\n"]

    avg = data["avg_score"]
    if avg >= 80:
        grade_label = "Excellent"
    elif avg >= 65:
        grade_label = "Good"
    elif avg >= 50:
        grade_label = "Moderate"
    elif avg >= 35:
        grade_label = "Below Average"
    else:
        grade_label = "Needs Improvement"

    lines.append(f"**Overall Citability Score: {avg}/100 ({grade_label})**\n")
    lines.append(f"- Blocks analyzed: {data['total_blocks']}")
    lines.append(f"- Optimal length blocks (134-167 words): {data['optimal_length_blocks']}")

    # Grade distribution
    gd = data["grade_distribution"]
    lines.append(f"\n### Grade Distribution\n")
    lines.append("| Grade | Count |")
    lines.append("|-------|-------|")
    for grade in ("A", "B", "C", "D", "F"):
        lines.append(f"| {grade} | {gd.get(grade, 0)} |")

    # Top blocks
    if data["top_blocks"]:
        lines.append("\n### Top Citeable Blocks\n")
        for i, block in enumerate(data["top_blocks"], 1):
            bd = block["breakdown"]
            lines.append(f"**{i}. [{block['grade']}] {block['total_score']}/100** — {block.get('heading', 'No heading')}")
            lines.append(f"> {block['preview']}...")
            lines.append(f"  - Answer Quality: {bd['answer_quality']}/100, Self-Containment: {bd['self_containment']}/100")
            lines.append(f"  - Readability: {bd['readability']}/100, Statistics: {bd['statistical_density']}/100, Uniqueness: {bd['uniqueness']}/100")
            lines.append(f"  - Word count: {block['word_count']}\n")

    # Bottom blocks
    if data["bottom_blocks"]:
        lines.append("### Lowest-Scoring Blocks (improvement targets)\n")
        for i, block in enumerate(data["bottom_blocks"], 1):
            lines.append(f"**{i}. [{block['grade']}] {block['total_score']}/100** — {block.get('heading', 'No heading')}")
            lines.append(f"> {block['preview']}...\n")

    # Recommendations
    lines.append("### Recommendations\n")
    if avg < 50:
        lines.append("- **Restructure content into self-contained answer blocks** (134-167 words each)")
        lines.append("- **Add statistics, percentages, and specific data** to increase citation density")
        lines.append("- **Use definition patterns** ('X is...', 'X refers to...') early in each section")
    elif avg < 70:
        lines.append("- **Add more statistical evidence** to support claims")
        lines.append("- **Reduce pronoun usage** — restate the subject in each block for self-containment")
        lines.append("- **Use structured formats** (numbered lists, bold key terms) for scannability")
    else:
        lines.append("- Content is well-optimized for AI citations. Focus on maintaining quality.")
        lines.append("- Consider adding more **original research indicators** (case studies, proprietary data)")

    return "\n".join(lines)


@function_tool
async def score_page_citability(url: str) -> str:
    """Score a web page's content blocks for AI citation readiness (0-100). Analyzes answer quality, self-containment, readability, statistical density, and uniqueness signals."""
    data = await _citability_impl(url)
    return _format_report(data)

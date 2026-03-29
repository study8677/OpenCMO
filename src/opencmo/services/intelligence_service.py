"""Intelligence service — AI-powered analysis and competitor discovery."""

from __future__ import annotations

import json
import logging

from opencmo import storage

logger = logging.getLogger(__name__)


async def _llm_call(client, model: str, messages: list[dict]) -> str:
    """Single LLM chat completion call, returns content string.

    Uses the centralized llm module when client is None.
    """
    if client is None:
        from opencmo import llm
        return await llm.chat_completion_messages(messages)
    resp = await client.chat.completions.create(
        model=model, messages=messages, temperature=0.7,
    )
    return resp.choices[0].message.content.strip()


async def analyze_url_with_ai(url: str, on_progress=None, locale: str = "en") -> dict:
    """Crawl a URL and use multi-agent discussion (3 roles × 3 rounds) to
    extract brand name, category, and monitoring keywords.

    Args:
        url: The URL to analyze.
        on_progress: Optional callback(role, content, round_num) called after each agent speaks.
        locale: Language for the discussion ("zh" for Chinese, "en" for English).

    Returns {"brand_name": str, "category": str, "keywords": list[str]}.
    """
    fallback = {"brand_name": "", "category": "", "keywords": []}
    emit = on_progress or (lambda *a: None)

    # Language instruction based on locale
    lang_instruction = (
        "You MUST respond in Chinese (中文). All your analysis and output should be in Chinese."
        if locale == "zh"
        else "You MUST respond in English."
    )

    # 1. Crawl the URL
    try:
        from opencmo.tools.crawl import fetch_url_content

        emit("system", f"Fetching {url} ...", 0)
        raw_content, source = await fetch_url_content(
            url,
            max_chars=20000,
            tavily_extract_depth="advanced",
        )
        if not raw_content.strip():
            logger.warning("Empty crawl result for %s", url)
            emit("system", "No content found on page.", 0)
            return fallback
        verb = "Extracted" if source == "tavily" else "Crawled"
        emit("system", f"{verb} {len(raw_content)} chars. Filtering noise...", 0)
    except Exception:
        logger.exception("Failed to crawl %s", url)
        emit("system", "Failed to crawl the page.", 0)
        return fallback

    # 2. Filter: use LLM to extract only useful product info, discard nav/footer/ads
    try:
        from opencmo import llm

        client = await llm.get_openai_client()
        model = await llm.get_model()

        filter_resp = await _llm_call(client, model, [
            {
                "role": "system",
                "content": (
                    "You are a content filter. Extract ONLY the useful product/project information "
                    "from a crawled webpage. Remove all navigation menus, headers, footers, sidebars, "
                    "cookie notices, sign-up prompts, GitHub UI chrome (star counts, fork buttons, "
                    "file listings, contributor lists), ads, and other boilerplate. "
                    "Keep: product name, description, features, tech stack, use cases, README content, "
                    "taglines, pricing info, and any text that describes what the product does. "
                    "Return the cleaned content as plain text, preserving the original language."
                ),
            },
            {"role": "user", "content": f"URL: {url}\n\nRaw crawled content:\n{raw_content}"},
        ])
        content = filter_resp.strip()
        emit("system", f"Filtered to {len(content)} chars of useful content. Starting discussion...", 0)
        logger.info("Content filtered: %d → %d chars", len(raw_content), len(content))

        briefing = (
            f"We are analyzing a product/project to create a brand monitoring strategy.\n"
            f"URL: {url}\n\nWebpage content:\n{content}"
        )

        roles = {
            "product_analyst": (
                "You are a Product Analyst. Focus on: what the product/project actually does, "
                "its core features, target audience, and competitive positioning. "
                "Identify the real brand/product name (NOT the hosting platform like GitHub/GitLab/npm). "
                f"Be concise (3-5 sentences per round). {lang_instruction}"
            ),
            "seo_specialist": (
                "You are an SEO Specialist. Focus on: what search keywords users would type to "
                "find this kind of product, competitor product names, high-intent long-tail keywords. "
                "Think about what people search on Google/Bing when looking for solutions in this space. "
                f"Be concise (3-5 sentences per round). {lang_instruction}"
            ),
            "community_strategist": (
                "You are a Community Strategist. Focus on: what discussion topics to monitor on "
                "Reddit/HN/Dev.to, community-specific jargon, pain points users discuss, "
                "hashtags and category tags. "
                f"Be concise (3-5 sentences per round). {lang_instruction}"
            ),
        }

        discussion: list[str] = []

        # Round 1: Each role gives initial analysis
        for role_name, system_prompt in roles.items():
            reply = await _llm_call(client, model, [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{briefing}\n\nGive your initial analysis."},
            ])
            discussion.append(f"[{role_name}] {reply}")
            emit(role_name, reply, 1)
            logger.info("Round 1 - %s done", role_name)

        # Round 2: Each role responds to others' analysis
        round1_summary = "\n\n".join(discussion)
        for role_name, system_prompt in roles.items():
            reply = await _llm_call(client, model, [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{briefing}\n\nRound 1 discussion:\n{round1_summary}\n\nBuild on your colleagues' insights. Refine your keyword suggestions."},
            ])
            discussion.append(f"[{role_name}] {reply}")
            emit(role_name, reply, 2)
            logger.info("Round 2 - %s done", role_name)

        # Round 3: Consensus — a moderator synthesizes the final strategy
        full_discussion = "\n\n".join(discussion)
        final_text = await _llm_call(client, model, [
            {
                "role": "system",
                "content": (
                    "You are the Strategy Director. Synthesize the team discussion into a final monitoring strategy. "
                    "Return ONLY valid JSON, no markdown fences, no extra text."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"URL: {url}\n\n"
                    f"Team discussion:\n{full_discussion}\n\n"
                    f"Based on the discussion, produce the final monitoring strategy as JSON:\n"
                    f'{{"brand_name": "the actual product name",'
                    f' "category": "one-word category (devtools/saas/ai/marketing/analytics/ecommerce/...)",'
                    f' "keywords": ["5-8 monitoring keywords covering brand name, product category, competitor terms, and user search queries"],'
                    f' "competitors": [{{"name": "competitor product/brand name", "url": "their website URL or empty string", "keywords": ["2-4 keywords that competitor ranks for"]}}]}}'
                    f'\nProvide 3-5 real competitors in the same market space. Only include actual known products/brands, not generic terms.'
                )
            },
        ])
        emit("strategy_director", final_text, 3)
        logger.info("Round 3 - synthesis done")

        # Parse JSON
        text = final_text
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()

        data = json.loads(text)
        return {
            "brand_name": str(data.get("brand_name", "")).strip(),
            "category": str(data.get("category", "")).strip(),
            "keywords": [str(k).strip() for k in data.get("keywords", []) if k],
            "competitors": data.get("competitors", []),
        }
    except Exception:
        logger.exception("AI analysis failed for %s", url)
        return fallback


async def analyze_and_enrich_project(project_id: int, url: str, on_progress=None, locale: str = "en") -> None:
    """Run AI analysis on a URL and update the project with extracted metadata + keywords."""
    analysis = await analyze_url_with_ai(url, on_progress=on_progress, locale=locale)

    if analysis["brand_name"] or analysis["category"]:
        await storage.update_project(
            project_id,
            brand_name=analysis["brand_name"] or None,
            category=analysis["category"] or None,
        )
        logger.info(
            "Project %d enriched: brand=%s, category=%s, keywords=%d",
            project_id,
            analysis["brand_name"],
            analysis["category"],
            len(analysis["keywords"]),
        )

    for kw in analysis["keywords"]:
        if kw:
            try:
                kw_id = await storage.add_tracked_keyword(project_id, kw)
                if kw_id:
                    await storage.seed_node_if_expansion_exists(project_id, "keyword", kw_id, priority=80)
            except Exception:
                pass

    # Auto-save discovered competitors
    for comp in analysis.get("competitors", []):
        try:
            name = str(comp.get("name", "")).strip()
            if not name:
                continue
            comp_id = await storage.add_competitor(
                project_id,
                name,
                url=str(comp.get("url", "")).strip() or None,
            )
            if comp_id:
                await storage.seed_node_if_expansion_exists(project_id, "competitor", comp_id, priority=90)
            for ckw in comp.get("keywords", []):
                ckw = str(ckw).strip()
                if ckw:
                    ckw_id = await storage.add_competitor_keyword(comp_id, ckw)
                    if ckw_id:
                        await storage.seed_node_if_expansion_exists(project_id, "competitor_keyword", ckw_id, priority=60)
            logger.info("Auto-discovered competitor: %s for project %d", name, project_id)
        except Exception:
            logger.debug("Failed to save competitor %s", comp, exc_info=True)


async def discover_competitors(project_id: int, on_progress=None) -> list[dict]:
    """Use AI to discover competitors for an existing project.

    Returns list of {name, url, keywords} dicts.
    """
    project = await storage.get_project(project_id)
    if not project:
        return []

    emit = on_progress or (lambda *a: None)
    brand = project["brand_name"]
    category = project["category"]
    url = project["url"]

    # Gather existing keywords for context
    keywords_list = await storage.list_tracked_keywords(project_id)
    kw_text = ", ".join(k["keyword"] for k in keywords_list) if keywords_list else "N/A"

    try:
        from opencmo import llm

        client = await llm.get_openai_client()
        model = await llm.get_model()

        emit("system", f"Discovering competitors for {brand}...", 0)

        result_text = await _llm_call(client, model, [
            {
                "role": "system",
                "content": (
                    "You are a competitive intelligence analyst. Given a brand/product, "
                    "identify its real competitors in the market. Return ONLY valid JSON array, "
                    "no markdown fences, no extra text."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Brand: {brand}\n"
                    f"URL: {url}\n"
                    f"Category: {category}\n"
                    f"Current tracked keywords: {kw_text}\n\n"
                    f"Find 3-6 real competitors for this product. For each competitor, provide:\n"
                    f'[{{"name": "competitor name", "url": "website URL", '
                    f'"keywords": ["3-5 keywords this competitor is known for or ranks for"]}}]\n'
                    f"Only include actual known products/brands that compete in the same space. "
                    f"Do NOT include generic terms or the brand itself."
                ),
            },
        ])

        # Parse JSON
        text = result_text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()

        competitors = json.loads(text)
        if not isinstance(competitors, list):
            competitors = []

        # Save to DB
        saved = []
        for comp in competitors:
            name = str(comp.get("name", "")).strip()
            if not name:
                continue
            comp_url = str(comp.get("url", "")).strip() or None
            comp_id = await storage.add_competitor(project_id, name, url=comp_url)
            if comp_id:
                await storage.seed_node_if_expansion_exists(project_id, "competitor", comp_id, priority=90)
            comp_kws = []
            for ckw in comp.get("keywords", []):
                ckw = str(ckw).strip()
                if ckw:
                    ckw_id = await storage.add_competitor_keyword(comp_id, ckw)
                    if ckw_id:
                        await storage.seed_node_if_expansion_exists(project_id, "competitor_keyword", ckw_id, priority=60)
                    comp_kws.append(ckw)
            saved.append({"id": comp_id, "name": name, "url": comp_url, "keywords": comp_kws})
            logger.info("AI discovered competitor: %s", name)

        emit("system", f"Found {len(saved)} competitors.", 1)
        return saved

    except Exception:
        logger.exception("Competitor discovery failed for project %d", project_id)
        return []

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

    # Language & ecosystem config based on locale
    is_zh = locale == "zh"
    lang_instruction = (
        "You MUST respond in Chinese (中文). All your analysis and output should be in Chinese."
        if is_zh
        else "You MUST respond in English."
    )
    search_ecosystem = (
        "Baidu, Sogou, 360 Search, Douyin Search, WeChat Search, Xiaohongshu Search, and Google"
        if is_zh
        else "Google, Bing, DuckDuckGo, and YouTube"
    )
    community_platforms = (
        "知乎, V2EX, 掘金, 即刻, 小红书, 微信公众号, OSChina, CSDN, as well as Reddit, Hacker News, and Dev.to"
        if is_zh
        else "Reddit, Hacker News, Dev.to, Twitter/X, YouTube, Stack Overflow, and Product Hunt"
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
                    "You are a content filter for product intelligence. Your job is to extract "
                    "ONLY the useful product/project information from a crawled webpage.\n\n"
                    "REMOVE: navigation menus, headers, footers, sidebars, cookie notices, "
                    "sign-up prompts, GitHub UI chrome (star counts, fork buttons, file listings, "
                    "contributor avatars, issue counts), ads, testimonials, and other boilerplate.\n\n"
                    "KEEP and structure:\n"
                    "- Product/project name and tagline\n"
                    "- What it does (core value proposition)\n"
                    "- Key features and capabilities\n"
                    "- Tech stack and implementation details\n"
                    "- Target users and use cases\n"
                    "- Pricing model (free/freemium/paid/open-source)\n"
                    "- Any mentioned integrations or ecosystem\n"
                    "- README content if from a code repository\n\n"
                    "Return the cleaned content as plain text, preserving the original language. "
                    "If the page is a GitHub/GitLab repo, prioritize the README content over UI elements."
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
                "You are a Senior Product Analyst with 10+ years of experience in tech product strategy.\n\n"
                "YOUR MISSION: Deconstruct this product to its strategic essence.\n\n"
                "ANALYSIS FRAMEWORK — you MUST address every point with specifics, not generalities:\n"
                "1. **Brand Identity**: The real product/brand name. NEVER use the hosting platform "
                "(GitHub, GitLab, npm, PyPI) as the brand name. If the page is a repo, the brand is "
                "the project name, not 'GitHub'.\n"
                "2. **Value Proposition**: What specific problem does it solve? Write a one-sentence "
                "pitch that a founder could use in an elevator.\n"
                "3. **Target Persona**: Who is the ideal user? Be granular — role, company size, "
                "pain level (e.g., 'solo indie devs shipping SaaS products who can't afford a "
                "marketing team' NOT just 'developers').\n"
                "4. **Competitive Moat**: What makes this defensible? Name specific moats: "
                "open-source community, proprietary data, integration lock-in, vertical expertise, "
                "network effects, or cost advantage.\n"
                "5. **Category Fit**: Pick exactly ONE from: devtools / saas / ai / marketing / "
                "analytics / ecommerce / fintech / productivity / security / infra / education / "
                "design / other. Justify your choice in one sentence.\n\n"
                "ANTI-HALLUCINATION RULES:\n"
                "- Only claim features that are explicitly mentioned on the page.\n"
                "- If the page doesn't mention pricing, say 'Pricing: not found on page' "
                "instead of guessing.\n"
                "- Tag each claim with [HIGH/MEDIUM/LOW confidence] based on evidence strength.\n"
                "- HIGH = directly stated on page. MEDIUM = reasonably inferred. LOW = speculative.\n\n"
                f"{lang_instruction}"
            ),
            "seo_specialist": (
                "You are a Senior SEO & Search Strategist specializing in product discoverability.\n\n"
                "YOUR MISSION: Identify the exact keywords that will drive qualified traffic "
                "to this product.\n\n"
                f"TARGET SEARCH ECOSYSTEM: {search_ecosystem}.\n\n"
                "KEYWORD FRAMEWORK — produce keywords in EXACTLY these 5 buckets:\n"
                "1. **Brand Keywords** (2-3): exact product name, common abbreviations, "
                "and likely misspellings.\n"
                "2. **Category Keywords** (2-3): what users search when exploring this product "
                "category (e.g., 'open source CRM', 'AI writing tool').\n"
                "3. **Problem Keywords** (2-3): search queries describing the pain point "
                "(e.g., 'how to automate SEO audit', 'monitor brand mentions automatically').\n"
                "4. **Competitor Keywords** (1-2): names of real, verifiable competitor products.\n"
                "5. **Long-tail Intent Keywords** (2-3): 3-6 word phrases with adoption intent "
                "(e.g., 'best free alternative to Ahrefs', 'self-hosted analytics 2024').\n\n"
                "QUALITY RULES:\n"
                "- Every keyword must be something a real human would actually type into a search box.\n"
                "- Do NOT invent competitor names. Only name competitors you are certain exist.\n"
                "- Tag each keyword with [HIGH/MEDIUM/LOW confidence].\n"
                "- HIGH = certain this keyword has real search volume. MEDIUM = likely but unverified. "
                "LOW = speculative.\n"
                "- Prefer specific phrases over single generic words.\n\n"
                f"{lang_instruction}"
            ),
            "community_strategist": (
                "You are a Senior Community Intelligence Strategist who monitors developer "
                "and tech communities for market signals.\n\n"
                "YOUR MISSION: Define the exact monitoring queries and platforms to capture "
                "relevant market signals for this product.\n\n"
                f"TARGET PLATFORMS: {community_platforms}.\n\n"
                "MONITORING FRAMEWORK — produce monitoring items in EXACTLY these 5 buckets:\n"
                "1. **Brand Queries** (2-3): exact phrases to catch direct product mentions "
                "(include name variations and common misspellings).\n"
                "2. **Problem Queries** (2-3): pain-point discussions where this product could "
                "be recommended (e.g., 'struggling with SEO for my startup', "
                "'need a tool to monitor competitors').\n"
                "3. **Competitor Queries** (1-2): discussions comparing or seeking alternatives "
                "to competitors in this space.\n"
                "4. **Trend Signals** (2-3): specific subreddits, tags, hashtags, or topic areas "
                "where the target audience congregates.\n"
                "5. **Engagement Hooks** (1-2): types of threads where mentioning this product "
                "would be genuinely helpful, not spammy (e.g., 'what tools do you use for X', "
                "'looking for Y alternative').\n\n"
                "QUALITY RULES:\n"
                "- Every query must be a phrase someone would naturally write in a community post "
                "or search within a platform.\n"
                "- Include platform-specific formats where useful (subreddit names, hashtags).\n"
                "- Do NOT include generic queries like 'best tool' without context.\n"
                "- Tag each item with [HIGH/MEDIUM/LOW confidence].\n"
                "- Think about WHERE the target persona actually hangs out, not where you wish "
                "they were.\n\n"
                f"{lang_instruction}"
            ),
        }

        discussion: list[str] = []

        # Round 1: Each role gives structured initial analysis with role-specific prompts
        round1_prompts = {
            "product_analyst": (
                f"{briefing}\n\n"
                "ROUND 1 — Product Deconstruction\n"
                "Follow your 5-point framework strictly. For each point, cite specific evidence "
                "from the webpage content (quote key phrases when possible). Tag every claim "
                "with a confidence level."
            ),
            "seo_specialist": (
                f"{briefing}\n\n"
                "ROUND 1 — Keyword Discovery\n"
                "Follow your 5-bucket framework strictly. For each keyword, explain in 1 sentence "
                "why this keyword matters for this specific product (not generic reasons). "
                "Tag every keyword with a confidence level."
            ),
            "community_strategist": (
                f"{briefing}\n\n"
                "ROUND 1 — Community Signal Mapping\n"
                "Follow your 5-bucket framework strictly. For each monitoring query, specify "
                "which platform(s) it targets and what type of signal it would capture "
                "(awareness / demand / competitive intel / sentiment). Tag with confidence level."
            ),
        }
        for role_name, system_prompt in roles.items():
            reply = await _llm_call(client, model, [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": round1_prompts[role_name]},
            ])
            discussion.append(f"[{role_name}] {reply}")
            emit(role_name, reply, 1)
            logger.info("Round 1 - %s done", role_name)

        # Round 2: Adversarial cross-review with role-specific challenges
        round1_summary = "\n\n".join(discussion)
        round2_prompts = {
            "product_analyst": (
                f"{briefing}\n\n"
                f"Round 1 discussion:\n{round1_summary}\n\n"
                "ROUND 2 — Cross-Review (Product Analyst)\n"
                "Review your colleagues' Round 1 output and respond to these:\n"
                "1. Does the SEO Specialist's category keyword match your Category Fit? "
                "If not, argue which is correct.\n"
                "2. Does the Community Strategist's target persona match your Target Persona? "
                "Flag any misalignment.\n"
                "3. Are any competitor names the SEO Specialist mentioned actually NOT competitors? "
                "Challenge any you believe are wrong.\n"
                "4. Based on their insights, REVISE your analysis — especially refine the "
                "Target Persona and Competitive Moat if needed.\n"
                "Tag all revisions with [REVISED] and explain why."
            ),
            "seo_specialist": (
                f"{briefing}\n\n"
                f"Round 1 discussion:\n{round1_summary}\n\n"
                "ROUND 2 — Cross-Review (SEO Specialist)\n"
                "Review your colleagues' Round 1 output and respond to these:\n"
                "1. Does the Product Analyst's brand name give you better brand keyword ideas? "
                "Add any you missed.\n"
                "2. Does the Community Strategist's problem queries reveal problem keywords "
                "you didn't think of? Adopt the good ones.\n"
                "3. Challenge: are your competitor keywords REAL products? Remove any you're "
                "not at least MEDIUM confidence about.\n"
                "4. Based on their insights, produce a FINAL refined keyword list — "
                "re-rank by priority (must-have vs nice-to-have).\n"
                "Tag all changes with [ADDED], [REMOVED], or [PROMOTED]."
            ),
            "community_strategist": (
                f"{briefing}\n\n"
                f"Round 1 discussion:\n{round1_summary}\n\n"
                "ROUND 2 — Cross-Review (Community Strategist)\n"
                "Review your colleagues' Round 1 output and respond to these:\n"
                "1. Does the Product Analyst's target persona help you narrow down WHICH "
                "communities to prioritize? Re-rank your platform list.\n"
                "2. Does the SEO Specialist's keyword list give you better monitoring queries? "
                "Adopt any that would work as community search terms.\n"
                "3. Challenge: are your suggested platforms actually where THIS product's "
                "audience hangs out? Remove any that are too generic.\n"
                "4. Based on their insights, produce a FINAL refined monitoring plan — "
                "prioritize the top 3-4 highest-signal monitoring queries.\n"
                "Tag all changes with [ADDED], [REMOVED], or [PROMOTED]."
            ),
        }
        for role_name, system_prompt in roles.items():
            reply = await _llm_call(client, model, [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": round2_prompts[role_name]},
            ])
            discussion.append(f"[{role_name}] {reply}")
            emit(role_name, reply, 2)
            logger.info("Round 2 - %s done", role_name)

        # Round 3: Consensus — Strategy Director with quality gates
        full_discussion = "\n\n".join(discussion)
        final_text = await _llm_call(client, model, [
            {
                "role": "system",
                "content": (
                    "You are the Strategy Director. You synthesize multi-expert discussions into "
                    "a final, validated monitoring strategy.\n\n"
                    "SYNTHESIS RULES:\n"
                    "1. Return ONLY valid JSON. No markdown fences, no commentary, no extra text.\n"
                    "2. brand_name must be the ACTUAL product name confirmed by the Product Analyst. "
                    "Never use a hosting platform name.\n"
                    "3. category must be exactly ONE word from: devtools, saas, ai, marketing, "
                    "analytics, ecommerce, fintech, productivity, security, infra, education, "
                    "design, other. Use the Product Analyst's recommendation unless the SEO "
                    "Specialist made a compelling counter-argument.\n"
                    "4. keywords: select 6-10 of the HIGHEST confidence keywords from the SEO "
                    "Specialist's final list. Must include: at least 1 brand keyword, at least "
                    "2 category/problem keywords, and at least 1 competitor keyword.\n"
                    "5. competitors: include 3-5 REAL products only. Only include competitors that "
                    "the SEO Specialist tagged as at least MEDIUM confidence. Each must have a "
                    "plausible website URL (or empty string).\n\n"
                    "QUALITY GATES (check before outputting):\n"
                    "- Does brand_name match what the Product Analyst identified?\n"
                    "- Are all keywords specific enough to be useful search terms?\n"
                    "- Are all competitors real products (not generic terms like 'other tools')?\n"
                    "- Did you incorporate Round 2 refinements (items tagged [ADDED]/[PROMOTED])?\n"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"URL: {url}\n\n"
                    f"Expert discussion (2 rounds, 3 specialists):\n{full_discussion}\n\n"
                    f"Produce the final monitoring strategy as JSON:\n"
                    f'{{"brand_name": "the actual product name",'
                    f' "category": "one-word category",'
                    f' "keywords": ["6-10 highest-confidence monitoring keywords"],'
                    f' "competitors": [{{"name": "competitor name", "url": "website URL or empty string", "keywords": ["2-4 keywords"]}}]}}'
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

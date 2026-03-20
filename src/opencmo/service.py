"""Service layer — shared business logic for CLI and Web."""

from __future__ import annotations

import json
import logging
import os

from opencmo import storage

logger = logging.getLogger(__name__)


async def create_monitor(
    brand: str,
    url: str,
    category: str,
    job_type: str = "full",
    cron_expr: str = "0 9 * * *",
    keywords: list[str] | None = None,
) -> dict:
    """Create monitor + project + keywords. Returns {project_id, monitor_id, keywords_added}."""
    project_id = await storage.ensure_project(brand, url, category)
    job_id = await storage.add_scheduled_job(project_id, job_type, cron_expr)
    kw_added: list[str] = []
    for kw in keywords or []:
        kw = kw.strip()
        if kw:
            await storage.add_tracked_keyword(project_id, kw)
            kw_added.append(kw)
    return {"project_id": project_id, "monitor_id": job_id, "keywords_added": kw_added}


async def remove_monitor(job_id: int) -> bool:
    """Remove a scheduled job. Returns True if deleted."""
    return await storage.remove_scheduled_job(job_id)


async def get_monitor(job_id: int) -> dict | None:
    """Find a single monitor by job id."""
    jobs = await storage.list_scheduled_jobs()
    return next((j for j in jobs if j["id"] == job_id), None)


async def list_monitors() -> list[dict]:
    """Return all scheduled jobs with project info."""
    return await storage.list_scheduled_jobs()


async def get_monitor_history(job_id: int) -> dict | None:
    """Get latest scans for a monitor's project. Returns None if monitor not found."""
    job = await get_monitor(job_id)
    if not job:
        return None
    latest = await storage.get_latest_scans(job["project_id"])
    return {"job": job, "latest": latest}


async def run_monitor(job_id: int) -> dict:
    """Run a monitor scan synchronously. Returns {ok, error?}."""
    job = await get_monitor(job_id)
    if not job:
        return {"ok": False, "error": f"Monitor #{job_id} not found."}

    from opencmo.scheduler import run_scheduled_scan

    await run_scheduled_scan(
        job["project_id"], job["job_type"], job_id, triggered_by="manual"
    )
    return {"ok": True, "job": job}


async def resolve_project(id_or_brand: str) -> tuple[int | None, str]:
    """Resolve project_id from int or brand_name. Returns (id, error_msg)."""
    try:
        pid = int(id_or_brand)
        project = await storage.get_project(pid)
        if project:
            return pid, ""
        return None, f"Project #{pid} not found."
    except ValueError:
        pass

    projects = await storage.list_projects()
    matches = [p for p in projects if p["brand_name"].lower() == id_or_brand.lower()]
    if len(matches) == 1:
        return matches[0]["id"], ""
    elif len(matches) > 1:
        ids = ", ".join(f"#{p['id']}" for p in matches)
        return None, f"Multiple projects match '{id_or_brand}': {ids}. Use project ID instead."
    return None, f"No project found for '{id_or_brand}'."


async def manage_keywords(
    project_id: int,
    action: str = "list",
    keyword: str | None = None,
    keyword_id: int | None = None,
) -> dict:
    """Manage tracked keywords. Returns {action, result}."""
    if action == "list":
        keywords = await storage.list_tracked_keywords(project_id)
        return {"action": "list", "keywords": keywords}
    elif action == "add":
        if not keyword:
            return {"action": "add", "error": "Keyword is required."}
        kw_id = await storage.add_tracked_keyword(project_id, keyword)
        return {"action": "add", "keyword_id": kw_id, "keyword": keyword}
    elif action == "rm":
        if keyword_id is None:
            return {"action": "rm", "error": "keyword_id is required."}
        ok = await storage.remove_tracked_keyword(keyword_id)
        return {"action": "rm", "removed": ok, "keyword_id": keyword_id}
    return {"action": action, "error": f"Unknown action: {action}"}


async def send_project_report(project_id: int) -> dict:
    """Send email report for a project."""
    from opencmo.tools.email_report import send_report_impl

    return await send_report_impl(project_id)


async def get_status_summary() -> list[dict]:
    """Return structured status for all projects (used by Dashboard + CLI /status)."""
    projects = await storage.list_projects()
    result = []
    for p in projects:
        latest = await storage.get_latest_scans(p["id"])
        result.append({**p, "latest": latest})
    return result


async def _llm_call(client, model: str, messages: list[dict]) -> str:
    """Single LLM chat completion call, returns content string."""
    resp = await client.chat.completions.create(
        model=model, messages=messages, temperature=0.7,
    )
    return resp.choices[0].message.content.strip()


async def analyze_url_with_ai(url: str, on_progress=None) -> dict:
    """Crawl a URL and use multi-agent discussion (3 roles × 3 rounds) to
    extract brand name, category, and monitoring keywords.

    Args:
        url: The URL to analyze.
        on_progress: Optional callback(role, content, round_num) called after each agent speaks.

    Returns {"brand_name": str, "category": str, "keywords": list[str]}.
    """
    fallback = {"brand_name": "", "category": "", "keywords": []}
    emit = on_progress or (lambda *a: None)

    # 1. Crawl the URL
    try:
        from crawl4ai import AsyncWebCrawler

        emit("system", f"Crawling {url} ...", 0)
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
        raw_content = (result.markdown or "")[:20000]
        if not raw_content.strip():
            logger.warning("Empty crawl result for %s", url)
            emit("system", "No content found on page.", 0)
            return fallback
        emit("system", f"Crawled {len(raw_content)} chars. Filtering noise...", 0)
    except Exception:
        logger.exception("Failed to crawl %s", url)
        emit("system", "Failed to crawl the page.", 0)
        return fallback

    # 2. Filter: use LLM to extract only useful product info, discard nav/footer/ads
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url=os.environ.get("OPENAI_BASE_URL") or None,
        )
        model = os.environ.get("OPENCMO_MODEL_DEFAULT", "gpt-4o")

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
                "Be concise (3-5 sentences per round)."
            ),
            "seo_specialist": (
                "You are an SEO Specialist. Focus on: what search keywords users would type to "
                "find this kind of product, competitor product names, high-intent long-tail keywords. "
                "Think about what people search on Google/Bing when looking for solutions in this space. "
                "Be concise (3-5 sentences per round)."
            ),
            "community_strategist": (
                "You are a Community Strategist. Focus on: what discussion topics to monitor on "
                "Reddit/HN/Dev.to, community-specific jargon, pain points users discuss, "
                "hashtags and category tags. "
                "Be concise (3-5 sentences per round)."
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
                    f' "keywords": ["5-8 monitoring keywords covering brand name, product category, competitor terms, and user search queries"]}}'
                ),
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
        }
    except Exception:
        logger.exception("AI analysis failed for %s", url)
        return fallback


async def analyze_and_enrich_project(project_id: int, url: str, on_progress=None) -> None:
    """Run AI analysis on a URL and update the project with extracted metadata + keywords."""
    analysis = await analyze_url_with_ai(url, on_progress=on_progress)

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
                await storage.add_tracked_keyword(project_id, kw)
            except Exception:
                pass

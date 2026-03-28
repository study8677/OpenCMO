"""Service layer — shared business logic for CLI and Web."""

from __future__ import annotations

import json
import logging
import os

from opencmo import storage

logger = logging.getLogger(__name__)

_APPROVAL_CHANNELS = {
    "reddit_post": "reddit",
    "reddit_reply": "reddit",
    "twitter_post": "twitter",
    "blog_post": "blog",
    "reddit_comment": "reddit",
}

_PUBLISH_ENV_KEYS = {
    "reddit": (
        "OPENCMO_AUTO_PUBLISH",
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET",
        "REDDIT_USERNAME",
        "REDDIT_PASSWORD",
    ),
    "twitter": (
        "OPENCMO_AUTO_PUBLISH",
        "TWITTER_API_KEY",
        "TWITTER_API_SECRET",
        "TWITTER_ACCESS_TOKEN",
        "TWITTER_ACCESS_SECRET",
    ),
}


async def _sync_runtime_job(job_id: int) -> None:
    from opencmo import scheduler

    job = await storage.get_scheduled_job(job_id)
    if job:
        scheduler.sync_job_record(job)


async def _hydrate_publish_settings(channel: str) -> None:
    for key in _PUBLISH_ENV_KEYS.get(channel, ()):
        value = await storage.get_setting(key)
        if value:
            os.environ[key] = value


def _require_payload_fields(payload: dict, *fields: str) -> None:
    missing = [field for field in fields if not str(payload.get(field, "")).strip()]
    if missing:
        raise ValueError(f"Missing required payload fields: {', '.join(missing)}")


async def _preview_approval_payload(approval_type: str, payload: dict) -> tuple[str, dict]:
    from opencmo.tools import publishers

    if approval_type == "reddit_post":
        _require_payload_fields(payload, "subreddit", "title", "body")
        result = await publishers.publish_reddit_post_impl(
            payload["subreddit"], payload["title"], payload["body"], dry_run=True,
        )
    elif approval_type == "reddit_reply":
        _require_payload_fields(payload, "parent_id", "body")
        result = await publishers.publish_reddit_reply_impl(
            payload["parent_id"], payload["body"], dry_run=True,
        )
    elif approval_type == "twitter_post":
        _require_payload_fields(payload, "text")
        result = await publishers.publish_tweet_impl(payload["text"], dry_run=True)
    elif approval_type in ("blog_post", "reddit_comment"):
        _require_payload_fields(payload, "body")
        result = {
            "ok": True,
            "preview": {
                "title": payload.get("title", ""),
                "body": payload.get("body", "")[:500],
                "content_preview": payload.get("body", "")[:300] + "...",
            },
        }
    else:
        raise ValueError(f"Unsupported approval_type: {approval_type}")

    if not result.get("ok"):
        raise ValueError(result.get("error") or "Failed to build approval preview.")

    return _APPROVAL_CHANNELS[approval_type], result["preview"]


async def _execute_approval_payload(approval_type: str, payload: dict) -> dict:
    from opencmo.tools import publishers

    if approval_type == "reddit_post":
        return await publishers.publish_reddit_post_impl(
            payload["subreddit"], payload["title"], payload["body"], dry_run=False,
        )
    if approval_type == "reddit_reply":
        return await publishers.publish_reddit_reply_impl(
            payload["parent_id"], payload["body"], dry_run=False,
        )
    if approval_type == "twitter_post":
        return await publishers.publish_tweet_impl(payload["text"], dry_run=False)
    if approval_type in ("blog_post", "reddit_comment"):
        # Internal draft — store as campaign artifact, no external publish needed
        return await publishers.save_blog_draft_impl(payload)
    return {"ok": False, "error": f"Unsupported approval_type: {approval_type}"}


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
    await _sync_runtime_job(job_id)
    kw_added: list[str] = []
    for kw in keywords or []:
        kw = kw.strip()
        if kw:
            kw_id = await storage.add_tracked_keyword(project_id, kw)
            kw_added.append(kw)
            if kw_id:
                await storage.seed_node_if_expansion_exists(project_id, "keyword", kw_id, priority=80)
    return {"project_id": project_id, "monitor_id": job_id, "keywords_added": kw_added}


async def remove_monitor(job_id: int) -> bool:
    """Remove a scheduled job. Returns True if deleted."""
    ok = await storage.remove_scheduled_job(job_id)
    if ok:
        from opencmo import scheduler

        scheduler.unschedule_job(job_id)
    return ok


async def update_monitor(
    job_id: int,
    *,
    cron_expr: str | None = None,
    enabled: bool | None = None,
) -> bool:
    """Update a scheduled job and reconcile the in-memory scheduler."""
    ok = await storage.update_scheduled_job(job_id, cron_expr=cron_expr, enabled=enabled)
    if ok:
        await _sync_runtime_job(job_id)
    return ok


async def get_monitor(job_id: int) -> dict | None:
    """Find a single monitor by job id."""
    return await storage.get_scheduled_job(job_id)


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
        if kw_id:
            await storage.seed_node_if_expansion_exists(project_id, "keyword", kw_id, priority=80)
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


async def create_approval(
    project_id: int,
    approval_type: str,
    payload: dict,
    *,
    content: str = "",
    title: str = "",
    target_label: str = "",
    target_url: str = "",
    agent_name: str = "",
) -> dict:
    """Create a pending approval from the exact publish payload."""
    channel, preview = await _preview_approval_payload(approval_type, payload)
    body = content.strip()
    if not body:
        body = payload.get("body") or payload.get("text") or title
    return await storage.create_approval(
        project_id,
        channel,
        approval_type,
        body,
        payload,
        preview,
        title=title,
        target_label=target_label,
        target_url=target_url,
        agent_name=agent_name,
    )


async def list_approvals(status: str | None = None, limit: int = 50) -> list[dict]:
    """List approval records."""
    return await storage.list_approvals(status=status, limit=limit)


async def get_approval(approval_id: int) -> dict | None:
    """Return one approval record."""
    return await storage.get_approval(approval_id)


async def approve_approval(approval_id: int, decision_note: str = "") -> dict:
    """Publish the exact stored approval payload and persist the outcome."""
    approval = await storage.get_approval(approval_id)
    if not approval:
        return {"ok": False, "error": "Approval not found."}
    if approval["status"] != "pending":
        return {"ok": False, "error": f"Approval is already {approval['status']}."}

    channel = approval["channel"]
    await _hydrate_publish_settings(channel)
    # Blog drafts are internal — skip the external publish gate
    if channel != "blog" and os.environ.get("OPENCMO_AUTO_PUBLISH", "0") != "1":
        return {
            "ok": False,
            "error": "OPENCMO_AUTO_PUBLISH is not enabled.",
            "error_code": "auto_publish_disabled",
            "approval": approval,
        }

    result = await _execute_approval_payload(approval["approval_type"], approval["payload"])
    if result.get("ok"):
        await storage.update_approval_status(
            approval_id,
            "approved",
            decision_note=decision_note,
            publish_result=result,
        )
        return {"ok": True, "approval": await storage.get_approval(approval_id)}

    await storage.update_approval_status(
        approval_id,
        "failed",
        decision_note=decision_note,
        publish_result=result,
    )
    return {"ok": False, "error": result.get("error", "Publish failed."), "approval": await storage.get_approval(approval_id)}


async def reject_approval(approval_id: int, decision_note: str = "") -> dict:
    """Reject a pending approval without publishing."""
    approval = await storage.get_approval(approval_id)
    if not approval:
        return {"ok": False, "error": "Approval not found."}
    if approval["status"] != "pending":
        return {"ok": False, "error": f"Approval is already {approval['status']}."}

    await storage.update_approval_status(approval_id, "rejected", decision_note=decision_note)
    return {"ok": True, "approval": await storage.get_approval(approval_id)}


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
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url=os.environ.get("OPENAI_BASE_URL") or None,
        )
        model = os.environ.get("OPENCMO_MODEL_DEFAULT", "gpt-4o")

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

"""Graph expansion engine -- wave-based BFS discovery of competitors and keywords."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Callable
from urllib.parse import urlparse

from opencmo import storage
from opencmo.scrape_config import get_scrape_profile

logger = logging.getLogger(__name__)

MAX_OPS_PER_WAVE = 20
MIN_DELAY = 1.5  # seconds between operations

ProgressCallback = Callable[[dict], None] | None


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _emit(callback: ProgressCallback, stage: str, summary: str) -> None:
    if callback:
        callback({"stage": stage, "status": "running", "summary": summary})


# ---------------------------------------------------------------------------
# Web search helper (bypasses agent framework)
# ---------------------------------------------------------------------------


async def _web_search_direct(query: str) -> str:
    """Search via crawl4ai Google scrape. No agent framework dependency."""
    try:
        from crawl4ai import AsyncWebCrawler
        from opencmo.tools.crawl import _extract_markdown

        url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num=5"
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
        content = _extract_markdown(result)
        return content[:4000] if content else ""
    except Exception as exc:
        logger.warning("Web search failed for %r: %s", query, exc)
        return ""


# ---------------------------------------------------------------------------
# LLM helper (reuses service._llm_call pattern)
# ---------------------------------------------------------------------------


def _get_llm_client():
    from openai import AsyncOpenAI

    return AsyncOpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_BASE_URL") or None,
    )


def _get_model() -> str:
    return os.environ.get("OPENCMO_MODEL_DEFAULT", "gpt-4o")


async def _llm_call(client, model: str, messages: list[dict]) -> str:
    resp = await client.chat.completions.create(
        model=model, messages=messages, temperature=0.7,
    )
    return resp.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Expansion strategies
# ---------------------------------------------------------------------------


async def _expand_competitor(
    project_id: int, comp_db_id: int, wave: int, callback: ProgressCallback,
) -> int:
    """Expand a competitor: discover their competitors and keywords."""
    competitors = await storage.list_competitors(project_id)
    comp = next((c for c in competitors if c["id"] == comp_db_id), None)
    if not comp:
        return 0

    name = comp["name"]
    _emit(callback, "expand_competitor", f"Exploring competitor: {name}")

    search_text = await _web_search_direct(f"{name} vs alternatives competitors")
    if not search_text:
        return 0

    client = _get_llm_client()
    model = _get_model()

    try:
        result_text = await _llm_call(client, model, [
            {
                "role": "system",
                "content": (
                    "You are a competitive intelligence analyst. Given search results about a product, "
                    "identify its real competitors and keywords. Return ONLY valid JSON, no markdown fences."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Product: {name}\n"
                    f"URL: {comp.get('url', 'N/A')}\n\n"
                    f"Search results:\n{search_text[:3000]}\n\n"
                    f"Extract competitors and keywords from the search results.\n"
                    f'Return: {{"competitors": [{{"name": "...", "url": "..."}}], '
                    f'"keywords": ["keyword1", "keyword2"]}}\n'
                    f"Only include actual products/brands, not generic terms or the product itself."
                ),
            },
        ])
    except Exception:
        logger.exception("LLM call failed for competitor expansion: %s", name)
        return 0

    text = result_text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM response for competitor %s", name)
        return 0

    new_count = 0

    # Discovered competitors
    for c in data.get("competitors", [])[:5]:
        c_name = str(c.get("name", "")).strip()
        if not c_name:
            continue
        c_url = str(c.get("url", "")).strip() or None
        new_comp_id = await storage.add_competitor(project_id, c_name, url=c_url)
        is_new = await storage.add_expansion_node(project_id, "competitor", new_comp_id, wave)
        if is_new:
            await storage.add_expansion_edge(
                project_id, "competitor", comp_db_id,
                "competitor", new_comp_id, "discovered_competitor", wave,
            )
            new_count += 1

    # Keywords from the competitor
    for kw in data.get("keywords", [])[:5]:
        kw = str(kw).strip()
        if not kw:
            continue
        ckw_id = await storage.add_competitor_keyword(comp_db_id, kw)
        is_new = await storage.add_expansion_node(
            project_id, "competitor_keyword", ckw_id, wave,
        )
        if is_new:
            await storage.add_expansion_edge(
                project_id, "competitor", comp_db_id,
                "competitor_keyword", ckw_id, "discovered_comp_keyword", wave,
            )
            new_count += 1

    return new_count


async def _expand_keyword(
    project_id: int, kw_db_id: int, wave: int, callback: ProgressCallback,
) -> int:
    """Expand a keyword: check SERP + generate related keywords."""
    keywords = await storage.list_tracked_keywords(project_id)
    kw = next((k for k in keywords if k["id"] == kw_db_id), None)
    if not kw:
        return 0

    keyword_text = kw["keyword"]
    _emit(callback, "expand_keyword", f"Exploring keyword: {keyword_text}")

    # Check SERP ranking
    project = await storage.get_project(project_id)
    if project:
        domain = urlparse(project["url"]).netloc.removeprefix("www.")
        try:
            from opencmo.tools.serp_tracker import _check_ranking

            result = await _check_ranking(keyword_text, domain)
            await storage.save_serp_snapshot(
                project_id, keyword_text,
                result.position, result.url_found, result.provider, result.error,
            )
        except Exception:
            logger.debug("SERP check failed for %s", keyword_text, exc_info=True)

    # Generate related keywords via LLM
    client = _get_llm_client()
    model = _get_model()

    try:
        result_text = await _llm_call(client, model, [
            {
                "role": "system",
                "content": (
                    "You are an SEO keyword researcher. Given a keyword, suggest 3-5 related "
                    "long-tail keywords. Return ONLY a JSON array of strings, no markdown fences."
                ),
            },
            {
                "role": "user",
                "content": f'Base keyword: "{keyword_text}"\nReturn: ["related keyword 1", ...]',
            },
        ])
    except Exception:
        logger.exception("LLM call failed for keyword expansion: %s", keyword_text)
        return 0

    text = result_text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]

    try:
        related = json.loads(text.strip())
        if not isinstance(related, list):
            related = []
    except json.JSONDecodeError:
        return 0

    new_count = 0
    for rk in related[:5]:
        rk = str(rk).strip()
        if not rk or rk.lower() == keyword_text.lower():
            continue
        new_kw_id = await storage.add_tracked_keyword(project_id, rk)
        is_new = await storage.add_expansion_node(project_id, "keyword", new_kw_id, wave)
        if is_new:
            await storage.add_expansion_edge(
                project_id, "keyword", kw_db_id,
                "keyword", new_kw_id, "discovered_keyword", wave,
            )
            new_count += 1

    return new_count


async def _expand_competitor_keyword(
    project_id: int, ckw_db_id: int, wave: int, callback: ProgressCallback,
) -> int:
    """Check if the brand ranks for a competitor keyword."""
    # Find the keyword text by looking across all competitor keywords
    db = await storage.get_db()
    try:
        cursor = await db.execute(
            "SELECT keyword FROM competitor_keywords WHERE id = ?", (ckw_db_id,),
        )
        row = await cursor.fetchone()
    finally:
        await db.close()

    if not row:
        return 0

    keyword_text = row[0]
    _emit(callback, "expand_comp_kw", f"Checking brand SERP for: {keyword_text}")

    project = await storage.get_project(project_id)
    if not project:
        return 0

    domain = urlparse(project["url"]).netloc.removeprefix("www.")

    try:
        from opencmo.tools.serp_tracker import _check_ranking

        result = await _check_ranking(keyword_text, domain)
        await storage.save_serp_snapshot(
            project_id, keyword_text,
            result.position, result.url_found, result.provider, result.error,
        )
    except Exception:
        logger.debug("SERP check failed for %s", keyword_text, exc_info=True)

    # If brand ranks, also track as brand keyword
    if hasattr(result, "position") and result.position:
        await storage.add_tracked_keyword(project_id, keyword_text)

    return 0  # no new expansion nodes from this strategy


# ---------------------------------------------------------------------------
# Core expansion loop
# ---------------------------------------------------------------------------

_STRATEGY = {
    "competitor": _expand_competitor,
    "keyword": _expand_keyword,
    "competitor_keyword": _expand_competitor_keyword,
}


async def run_expansion(
    project_id: int, on_progress: ProgressCallback = None,
) -> None:
    """Main expansion loop. Processes waves until paused or no frontier.

    Pause mechanism: reads desired_state from DB before each node operation.
    No in-memory Event — survives server restarts via DB state.
    """
    profile = get_scrape_profile()
    delay = max(profile.request_delay_seconds, MIN_DELAY)

    while True:
        # Check desired state
        exp = await storage.get_expansion(project_id)
        if not exp or exp["desired_state"] != "running":
            await storage.update_expansion(project_id, runtime_state="paused")
            _emit(on_progress, "paused", "Expansion paused.")
            return

        # Strict BFS: only process the lowest unexplored wave
        frontier_wave = await storage.get_min_unexplored_wave(project_id)
        if frontier_wave is None:
            await storage.update_expansion(
                project_id, runtime_state="idle", desired_state="idle",
            )
            _emit(on_progress, "completed", "No more frontier nodes.")
            return

        wave = frontier_wave + 1  # new discoveries go into this wave
        await storage.update_expansion(
            project_id, runtime_state="running", current_wave=wave,
        )
        frontier = await storage.get_frontier_nodes(project_id, wave=frontier_wave)
        _emit(
            on_progress, "wave_start",
            f"Wave {wave}: {len(frontier)} nodes to explore.",
        )

        ops = 0
        wave_discovered = 0
        for node in frontier:
            # Re-check desired state before each op
            exp = await storage.get_expansion(project_id)
            if not exp or exp["desired_state"] != "running":
                await storage.update_expansion(project_id, runtime_state="paused")
                _emit(on_progress, "paused", "Expansion paused.")
                return

            if ops >= MAX_OPS_PER_WAVE:
                break  # remaining frontier stays for next loop iteration

            # Heartbeat
            await storage.update_expansion(project_id, heartbeat_at=_now())

            # Expand
            strategy = _STRATEGY.get(node["node_type"])
            new_count = 0
            if strategy:
                try:
                    new_count = await strategy(
                        project_id, node["db_row_id"], wave, on_progress,
                    )
                except Exception:
                    logger.exception(
                        "Expansion failed for %s/%d",
                        node["node_type"], node["db_row_id"],
                    )

            await storage.mark_node_explored(
                project_id, node["node_type"], node["db_row_id"],
            )
            wave_discovered += new_count
            ops += 1

            # Update counters
            exp = await storage.get_expansion(project_id)
            if exp:
                await storage.update_expansion(
                    project_id,
                    nodes_explored=(exp["nodes_explored"] or 0) + 1,
                    nodes_discovered=(exp["nodes_discovered"] or 0) + new_count,
                )

            await asyncio.sleep(delay)

        _emit(
            on_progress, "wave_done",
            f"Wave {wave}: explored {ops}, discovered {wave_discovered}.",
        )

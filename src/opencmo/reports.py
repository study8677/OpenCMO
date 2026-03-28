"""AI CMO report generation for strategic briefs and periodic reports."""

from __future__ import annotations

import html
import json
import logging
import os
from datetime import datetime, timedelta, timezone

from opencmo import storage

logger = logging.getLogger(__name__)

_REPORT_MODEL_DEFAULT = "gpt-4o"
_PERIODIC_WINDOW_DAYS = 7


def _json_dump(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is not None:
            return parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None


def _filter_window(items: list[dict], field: str, start: datetime) -> list[dict]:
    result: list[dict] = []
    for item in items:
        timestamp = _parse_ts(item.get(field))
        if timestamp and timestamp >= start:
            result.append(item)
    return result


def _safe_delta(latest, previous):
    if latest is None or previous is None:
        return None
    return latest - previous


def _rank_label(position: int | None) -> str:
    if position is None:
        return "未排名"
    return f"#{position}"


def _simple_markdown_to_html(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    html_lines: list[str] = []
    in_list = False

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            html_lines.append("</ul>")
            in_list = False

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            close_list()
            continue
        if stripped.startswith("### "):
            close_list()
            html_lines.append(f"<h3>{html.escape(stripped[4:])}</h3>")
            continue
        if stripped.startswith("## "):
            close_list()
            html_lines.append(f"<h2>{html.escape(stripped[3:])}</h2>")
            continue
        if stripped.startswith("# "):
            close_list()
            html_lines.append(f"<h1>{html.escape(stripped[2:])}</h1>")
            continue
        if stripped.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{html.escape(stripped[2:])}</li>")
            continue
        close_list()
        html_lines.append(f"<p>{html.escape(stripped)}</p>")

    close_list()
    return "\n".join(html_lines)


async def _generate_llm_markdown(system_prompt: str, user_prompt: str) -> str:
    """Generate markdown with the configured LLM."""
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_BASE_URL") or None,
    )
    model = os.environ.get("OPENCMO_MODEL_DEFAULT", _REPORT_MODEL_DEFAULT)
    response = await client.chat.completions.create(
        model=model,
        temperature=0.5,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content.strip()


async def _get_recent_recommendations(project_id: int, limit: int = 6) -> list[dict]:
    db = await storage.get_db()
    try:
        cursor = await db.execute(
            """SELECT rec.domain, rec.priority, rec.owner_type, rec.action_type,
                      rec.title, rec.summary, rec.rationale
               FROM scan_recommendations rec
               JOIN scan_runs r ON r.id = rec.run_id
               WHERE r.project_id = ?
               ORDER BY r.id DESC,
                 CASE rec.priority
                   WHEN 'high' THEN 0
                   WHEN 'medium' THEN 1
                   ELSE 2
                 END,
                 rec.id
               LIMIT ?""",
            (project_id, limit),
        )
        rows = await cursor.fetchall()
        return [
            {
                "domain": row[0],
                "priority": row[1],
                "owner_type": row[2],
                "action_type": row[3],
                "title": row[4],
                "summary": row[5],
                "rationale": row[6],
            }
            for row in rows
        ]
    finally:
        await db.close()


async def _get_recent_approvals(project_id: int, start: datetime) -> list[dict]:
    db = await storage.get_db()
    try:
        cursor = await db.execute(
            """SELECT id, approval_type, status, title, agent_name, created_at, decided_at
               FROM approvals
               WHERE project_id = ?
               ORDER BY created_at DESC, id DESC
               LIMIT 20""",
            (project_id,),
        )
        rows = await cursor.fetchall()
        approvals = [
            {
                "id": row[0],
                "approval_type": row[1],
                "status": row[2],
                "title": row[3],
                "agent_name": row[4],
                "created_at": row[5],
                "decided_at": row[6],
            }
            for row in rows
        ]
    finally:
        await db.close()
    return _filter_window(approvals, "created_at", start)


async def _build_strategic_facts(project_id: int) -> tuple[dict, dict]:
    project = await storage.get_project(project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found.")

    keywords = await storage.list_tracked_keywords(project_id)
    competitors = await storage.list_competitors(project_id)
    competitor_cards: list[dict] = []
    for competitor in competitors:
        competitor_cards.append({
            **competitor,
            "keywords": await storage.list_competitor_keywords(competitor["id"]),
        })

    latest = await storage.get_latest_scans(project_id)
    previous = await storage.get_previous_scans(project_id)
    monitoring = await storage.get_latest_monitoring_summary(project_id)
    findings = await storage.get_task_findings_by_project(project_id, limit=6)
    recommendations = await _get_recent_recommendations(project_id, limit=6)
    previous_human = await storage.get_latest_report(project_id, "strategic", "human")

    seo_score = latest.get("seo", {}).get("score") if latest.get("seo") else None
    geo_score = latest.get("geo", {}).get("score") if latest.get("geo") else None
    community_hits = latest.get("community", {}).get("total_hits") if latest.get("community") else None
    seo_delta = _safe_delta(
        latest.get("seo", {}).get("score") if latest.get("seo") else None,
        previous.get("seo", {}).get("score") if previous and previous.get("seo") else None,
    )
    geo_delta = _safe_delta(
        latest.get("geo", {}).get("score") if latest.get("geo") else None,
        previous.get("geo", {}).get("score") if previous and previous.get("geo") else None,
    )

    strengths: list[str] = []
    if seo_score is not None and seo_score >= 0.8:
        strengths.append(f"SEO 基础分达到 {round(seo_score * 100)}%，站点健康度较稳。")
    if geo_score is not None and geo_score >= 60:
        strengths.append(f"GEO 得分 {geo_score}/100，AI 可见性已经形成基础。")
    if community_hits:
        strengths.append(f"社区侧已发现 {community_hits} 条相关讨论，有可运营的自然信号。")
    if latest.get("serp"):
        ranked = [item for item in latest["serp"] if item.get("position")]
        if ranked:
            strengths.append(f"已有 {len(ranked)} 个关键词进入搜索结果。")

    risks: list[str] = []
    if seo_score is None:
        risks.append("SEO 基线仍不完整。")
    elif seo_score < 0.7:
        risks.append(f"SEO 基础分仅 {round(seo_score * 100)}%，技术面仍拖后腿。")
    if geo_score is None:
        risks.append("GEO 数据缺失，AI 渠道认知仍是盲区。")
    elif geo_score < 45:
        risks.append(f"GEO 得分 {geo_score}/100，AI 平台认知偏弱。")
    if not competitor_cards:
        risks.append("竞品画像仍然稀薄。")
    if monitoring and monitoring.get("findings_count", 0) > 0:
        risks.append(f"最近一次监控仍有 {monitoring['findings_count']} 条待处理发现。")

    change_lines: list[str] = []
    if previous_human:
        if seo_delta is not None:
            change_lines.append(f"SEO 相比上一版变动 {seo_delta:+.2f}。")
        if geo_delta is not None:
            change_lines.append(f"GEO 相比上一版变动 {geo_delta:+.0f}。")
        if latest.get("serp"):
            top_keyword = latest["serp"][0]
            change_lines.append(
                f"当前首个跟踪关键词 {top_keyword['keyword']} 排名 {_rank_label(top_keyword.get('position'))}。"
            )

    facts = {
        "project": project,
        "keywords": keywords,
        "competitors": competitor_cards,
        "latest_scans": latest,
        "previous_scans": previous,
        "monitoring_summary": monitoring,
        "findings": findings,
        "recommendations": recommendations,
        "strengths": strengths,
        "risks": risks,
        "change_lines": change_lines,
        "previous_report_excerpt": (previous_human["content"][:1600] if previous_human else ""),
    }
    meta = {
        "sample_count": sum(
            1 for item in (
                latest.get("seo"),
                latest.get("geo"),
                latest.get("community"),
                latest.get("serp"),
                keywords,
                competitor_cards,
            ) if item
        ),
        "low_sample": False,
        "facts_summary": (
            f"{len(keywords)} 个关键词, {len(competitor_cards)} 个竞品, "
            f"{len(findings)} 条发现, {len(recommendations)} 条建议"
        ),
        "change_count": len(change_lines),
    }
    return facts, meta


async def _build_periodic_facts(
    project_id: int,
    *,
    now: datetime | None = None,
    window_days: int = _PERIODIC_WINDOW_DAYS,
) -> tuple[dict, dict]:
    project = await storage.get_project(project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found.")

    if now is None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
    elif now.tzinfo is not None:
        now = now.astimezone(timezone.utc).replace(tzinfo=None)
    window_start_dt = now - timedelta(days=window_days)
    window_start = window_start_dt.isoformat(timespec="seconds")
    window_end = now.isoformat(timespec="seconds")

    seo_history = _filter_window(await storage.get_seo_history(project_id, limit=30), "scanned_at", window_start_dt)
    geo_history = _filter_window(await storage.get_geo_history(project_id, limit=30), "scanned_at", window_start_dt)
    community_history = _filter_window(
        await storage.get_community_history(project_id, limit=30),
        "scanned_at",
        window_start_dt,
    )
    discussions = await storage.get_tracked_discussions(project_id)
    recent_approvals = await _get_recent_approvals(project_id, window_start_dt)
    recommendations = await _get_recent_recommendations(project_id, limit=6)
    findings = await storage.get_task_findings_by_project(project_id, limit=6)
    serp_latest = await storage.get_all_serp_latest(project_id)

    sample_count = sum(1 for items in (seo_history, geo_history, community_history, serp_latest) if items)
    low_sample = sample_count < 2

    seo_delta = None
    if len(seo_history) >= 2:
        seo_delta = _safe_delta(seo_history[0].get("score_performance"), seo_history[-1].get("score_performance"))
    geo_delta = None
    if len(geo_history) >= 2:
        geo_delta = _safe_delta(geo_history[0].get("geo_score"), geo_history[-1].get("geo_score"))
    community_delta = None
    if len(community_history) >= 2:
        community_delta = _safe_delta(community_history[0].get("total_hits"), community_history[-1].get("total_hits"))

    top_changes: list[str] = []
    if seo_history:
        current = seo_history[0].get("score_performance")
        if current is not None:
            line = f"最新 SEO 分数 {round(current * 100)}%"
            if seo_delta is not None:
                line += f"，窗口内变动 {seo_delta:+.2f}"
            top_changes.append(line + "。")
    if geo_history:
        current = geo_history[0].get("geo_score")
        if current is not None:
            line = f"最新 GEO 分数 {current}/100"
            if geo_delta is not None:
                line += f"，窗口内变动 {geo_delta:+.0f}"
            top_changes.append(line + "。")
    if community_history:
        current = community_history[0].get("total_hits")
        if current is not None:
            line = f"最新社区命中 {current} 条"
            if community_delta is not None:
                line += f"，窗口内变动 {community_delta:+.0f}"
            top_changes.append(line + "。")
    if serp_latest:
        ranked = [item for item in serp_latest if item.get("position")]
        top_changes.append(f"当前共有 {len(ranked)}/{len(serp_latest)} 个关键词进入自然搜索结果。")
    if low_sample:
        top_changes.insert(0, "样本稀疏，以下结论仅供方向判断。")

    facts = {
        "project": project,
        "window_start": window_start,
        "window_end": window_end,
        "seo_history": seo_history,
        "geo_history": geo_history,
        "community_history": community_history,
        "discussions": discussions[:8],
        "serp_latest": serp_latest,
        "findings": findings,
        "recommendations": recommendations,
        "recent_approvals": recent_approvals,
        "top_changes": top_changes[:3],
    }
    meta = {
        "sample_count": sample_count,
        "low_sample": low_sample,
        "facts_summary": (
            f"SEO 样本 {len(seo_history)}, GEO 样本 {len(geo_history)}, "
            f"Community 样本 {len(community_history)}, SERP 关键词 {len(serp_latest)}"
        ),
        "window_days": window_days,
        "window_start": window_start,
        "window_end": window_end,
    }
    return facts, meta


def _fallback_markdown(kind: str, audience: str, facts: dict, meta: dict, previous_exists: bool) -> str:
    project = facts["project"]
    if kind == "strategic" and audience == "human":
        strengths = facts.get("strengths") or ["当前有效信号仍有限，需要继续补齐 SEO/GEO/竞品基线。"]
        risks = facts.get("risks") or ["暂无明确风险，但样本仍偏少。"]
        recommendations = facts.get("recommendations") or []
        lines = [
            "# AI CMO 战略报告",
            "",
            "## 项目定位与一句话判断",
            f"- {project['brand_name']} 是一个 {project['category']} 项目，当前更适合被定义为“监控基础已建立，但增长叙事仍需强化”的阶段。",
            "",
            "## 当前优势",
            *[f"- {item}" for item in strengths[:4]],
            "",
            "## 当前短板/风险",
            *[f"- {item}" for item in risks[:4]],
            "",
            "## 竞品格局与差异化",
        ]
        competitors = facts.get("competitors") or []
        if competitors:
            lines.extend(
                f"- 已记录竞品 {item['name']}，建议围绕其关键词和定位做差异化内容。"
                for item in competitors[:3]
            )
        else:
            lines.append("- 当前竞品画像仍然稀薄，差异化判断的置信度有限。")
        lines.extend(["", "## CMO 建议"])
        if recommendations:
            lines.extend(f"- {item['title']}：{item['summary']}" for item in recommendations[:4])
        else:
            lines.append("- 先补齐监控基线，再进入更明确的增长判断。")
        if previous_exists:
            lines.extend(["", "## 最近变化摘要"])
            changes = facts.get("change_lines") or ["本次新增报告版本，但量化变化仍有限。"]
            lines.extend(f"- {item}" for item in changes[:4])
        return "\n".join(lines)

    if kind == "strategic":
        lines = [
            "# Strategic Agent Brief",
            "",
            f"- objective: 提升 {project['brand_name']} 在 SEO、GEO 与竞品对位上的增长确定性",
            "- constraints: 只基于已验证监控事实推进，不夸大趋势",
            "- priority_directions:",
        ]
        directions = facts.get("recommendations") or []
        if directions:
            lines.extend(f"  - {item['title']}" for item in directions[:4])
        else:
            lines.append("  - 补齐监控样本")
        lines.extend([
            "- suggested_agents: SEO Agent, GEO Agent, Research Agent",
            "- do_not: 不要把低样本信号写成确定趋势",
        ])
        return "\n".join(lines)

    if kind == "periodic" and audience == "human":
        lines = [
            "# AI CMO 周报",
            "",
            "## 本周最重要的 3 个变化",
        ]
        changes = facts.get("top_changes") or ["本周暂无足够样本形成明确变化。"]
        lines.extend(f"- {item}" for item in changes[:3])
        lines.extend([
            "",
            "## SEO/GEO/SERP/Community 趋势摘要",
            f"- {meta['facts_summary']}",
            "",
            "## 本周新增风险与亮点",
        ])
        findings = facts.get("findings") or []
        if findings:
            lines.extend(f"- {item['title']}：{item['summary']}" for item in findings[:4])
        else:
            lines.append("- 当前没有新增高置信度风险。")
        lines.extend([
            "",
            "## 竞品/市场信号变化",
            f"- 本周可用社区讨论 {len(facts.get('discussions') or [])} 条，审批动作 {len(facts.get('recent_approvals') or [])} 条。",
            "",
            "## 下周建议与关注点",
        ])
        recommendations = facts.get("recommendations") or []
        if recommendations:
            lines.extend(f"- {item['title']}：{item['summary']}" for item in recommendations[:4])
        else:
            lines.append("- 继续积累样本，再输出更强判断。")
        if meta.get("low_sample"):
            lines.insert(2, "- 样本稀疏，结论低置信度。")
        return "\n".join(lines)

    lines = [
        "# Weekly Agent Brief",
        "",
        f"- project: {project['brand_name']}",
        f"- sample_count: {meta['sample_count']}",
        f"- low_sample: {str(meta.get('low_sample', False)).lower()}",
        "- focus:",
    ]
    recommendations = facts.get("recommendations") or []
    if recommendations:
        lines.extend(f"  - {item['title']}" for item in recommendations[:4])
    else:
        lines.append("  - 继续采集更多稳定样本")
    lines.extend([
        "- guardrails:",
        "  - 不要把缺失信号补写成趋势",
        "  - 所有动作都要回到项目增长判断",
    ])
    return "\n".join(lines)


def _prompts(kind: str, audience: str, facts: dict, meta: dict, previous_exists: bool) -> tuple[str, str]:
    project = facts["project"]
    system_common = (
        "你是 AI CMO。你的职责不是做运营流水账，而是把监控事实转成高站位、可执行、"
        "但不过度臆测的管理判断。必须使用中文输出。不要虚构数据；样本不足时要明确指出低置信度。"
    )
    if kind == "strategic" and audience == "human":
        system = (
            f"{system_common} 输出 Markdown。严格使用以下一级/二级结构："
            "1. 项目定位与一句话判断 2. 当前优势 3. 当前短板/风险 4. 竞品格局与差异化 5. CMO 建议"
        )
        if previous_exists:
            system += " 6. 最近变化摘要"
        user = (
            f"项目：{project['brand_name']} ({project['category']})\n"
            f"目标网址：{project['url']}\n"
            f"版本是否已有历史：{previous_exists}\n"
            f"摘要元数据：{_json_dump(meta)}\n\n"
            f"事实包：\n{_json_dump(facts)}"
        )
        return system, user

    if kind == "strategic" and audience == "agent":
        system = (
            f"{system_common} 输出 Markdown，保持简短。结构固定为："
            "目标、约束、优先方向、建议执行 agent、禁止事项。"
        )
        user = f"项目战略事实包：\n{_json_dump({'meta': meta, 'facts': facts})}"
        return system, user

    if kind == "periodic" and audience == "human":
        system = (
            f"{system_common} 输出 Markdown。结构固定为："
            "1. 本周最重要的 3 个变化 2. SEO/GEO/SERP/Community 趋势摘要 "
            "3. 本周新增风险与亮点 4. 竞品/市场信号变化 5. 下周建议与关注点。"
            "样本稀疏时，必须在开头显式标注。"
        )
        user = (
            f"项目：{project['brand_name']} ({project['category']})\n"
            f"统计窗口：{meta['window_start']} 到 {meta['window_end']}\n"
            f"元数据：{_json_dump(meta)}\n\n"
            f"事实包：\n{_json_dump(facts)}"
        )
        return system, user

    system = (
        f"{system_common} 输出 Markdown，保持像给 agent 的 brief。结构固定为："
        "项目、样本情况、下周目标、优先方向、护栏。"
    )
    user = f"周期报告事实包：\n{_json_dump({'meta': meta, 'facts': facts})}"
    return system, user


async def _generate_report_record(
    *,
    kind: str,
    audience: str,
    facts: dict,
    meta: dict,
    previous_exists: bool,
) -> dict:
    system_prompt, user_prompt = _prompts(kind, audience, facts, meta, previous_exists)
    used_fallback = False
    llm_error = None

    try:
        content = await _generate_llm_markdown(system_prompt, user_prompt)
        if not content.strip():
            raise RuntimeError("LLM returned empty report content.")
    except Exception as exc:
        used_fallback = True
        llm_error = str(exc)
        logger.exception("Report generation fell back to template for %s/%s", kind, audience)
        content = _fallback_markdown(kind, audience, facts, meta, previous_exists)

    record_meta = {
        **meta,
        "used_fallback": used_fallback,
        "model": os.environ.get("OPENCMO_MODEL_DEFAULT", _REPORT_MODEL_DEFAULT),
    }
    if llm_error:
        record_meta["llm_error"] = llm_error

    return {
        "generation_status": "completed",
        "content": content,
        "content_html": _simple_markdown_to_html(content),
        "meta": record_meta,
    }


async def _persist_bundle(
    *,
    project_id: int,
    kind: str,
    source_run_id: int | None,
    window_start: str | None,
    window_end: str | None,
    facts: dict,
    meta: dict,
) -> dict:
    previous_human = await storage.get_latest_report(project_id, kind, "human")
    records = {
        "human": await _generate_report_record(
            kind=kind,
            audience="human",
            facts=facts,
            meta=meta,
            previous_exists=bool(previous_human),
        ),
        "agent": await _generate_report_record(
            kind=kind,
            audience="agent",
            facts=facts,
            meta=meta,
            previous_exists=bool(previous_human),
        ),
    }
    created = await storage.create_report_bundle(
        project_id=project_id,
        kind=kind,
        source_run_id=source_run_id,
        window_start=window_start,
        window_end=window_end,
        records=records,
    )
    payload = {"kind": kind}
    payload.update({item["audience"]: item for item in created})
    return payload


async def generate_strategic_report_bundle(project_id: int, source_run_id: int | None = None) -> dict:
    """Generate and persist the latest strategic report bundle."""
    facts, meta = await _build_strategic_facts(project_id)
    return await _persist_bundle(
        project_id=project_id,
        kind="strategic",
        source_run_id=source_run_id,
        window_start=None,
        window_end=None,
        facts=facts,
        meta=meta,
    )


async def generate_periodic_report_bundle(
    project_id: int,
    *,
    source_run_id: int | None = None,
    now: datetime | None = None,
    window_days: int = _PERIODIC_WINDOW_DAYS,
) -> dict:
    """Generate and persist the latest periodic report bundle."""
    facts, meta = await _build_periodic_facts(project_id, now=now, window_days=window_days)
    return await _persist_bundle(
        project_id=project_id,
        kind="periodic",
        source_run_id=source_run_id,
        window_start=meta["window_start"],
        window_end=meta["window_end"],
        facts=facts,
        meta=meta,
    )

"""AI CMO report generation for strategic briefs and periodic reports."""

from __future__ import annotations

import asyncio
import html
import json
import logging
import os
from datetime import datetime, timedelta, timezone

from opencmo import storage

logger = logging.getLogger(__name__)

_REPORT_MODEL_DEFAULT = "gpt-4o"
_PERIODIC_WINDOW_DAYS = 7
_REPORT_LLM_TIMEOUT_SECONDS = 300.0


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
    api_key = await _get_runtime_setting("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=(await _get_runtime_setting("OPENAI_BASE_URL")) or None,
    )
    model = await _get_report_model()
    response = await asyncio.wait_for(
        client.chat.completions.create(
            model=model,
            temperature=0.5,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        ),
        timeout=await _get_report_timeout_seconds(),
    )
    return response.choices[0].message.content.strip()


async def _get_runtime_setting(key: str, default: str | None = None) -> str | None:
    value = await storage.get_setting(key)
    if value not in (None, ""):
        return value
    env_value = os.environ.get(key)
    if env_value not in (None, ""):
        return env_value
    return default


async def _get_report_model() -> str:
    return (await _get_runtime_setting("OPENCMO_MODEL_DEFAULT", _REPORT_MODEL_DEFAULT)) or _REPORT_MODEL_DEFAULT


async def _get_report_timeout_seconds() -> float:
    raw_value = await _get_runtime_setting(
        "OPENCMO_REPORT_LLM_TIMEOUT_SECONDS",
        str(_REPORT_LLM_TIMEOUT_SECONDS),
    )
    try:
        timeout = float(raw_value or _REPORT_LLM_TIMEOUT_SECONDS)
    except (TypeError, ValueError):
        return _REPORT_LLM_TIMEOUT_SECONDS
    return max(1.0, timeout)


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
    findings = await storage.get_task_findings_by_project(project_id, limit=15)
    recommendations = await _get_recent_recommendations(project_id, limit=12)
    previous_human = await storage.get_latest_report(project_id, "strategic", "human")

    # --- Multi-agent enrichment: pull data from ALL specialist agents ---
    insights = await storage.list_insights(project_id=project_id, limit=15)
    citability_history = await storage.get_citability_history(project_id, limit=3)
    ai_crawler_history = await storage.get_ai_crawler_history(project_id, limit=3)
    brand_presence_history = await storage.get_brand_presence_history(project_id, limit=3)
    discussions = await storage.get_tracked_discussions(project_id)
    serp_latest = await storage.get_all_serp_latest(project_id)

    # Try to get knowledge graph data for competitive landscape
    graph_data = None
    try:
        expansion = await storage.get_expansion(project_id)
        if expansion:
            graph_data = await storage.get_graph_data(expansion["id"])
    except Exception:
        pass  # graph may not exist yet

    # Recent approvals (last 30 days for strategic context)
    approvals_window = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)
    recent_approvals = await _get_recent_approvals(project_id, approvals_window)

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
    if serp_latest:
        ranked = [item for item in serp_latest if item.get("position")]
        if ranked:
            strengths.append(f"已有 {len(ranked)}/{len(serp_latest)} 个关键词进入搜索结果。")
    if citability_history:
        avg = citability_history[0].get("avg_score")
        if avg and avg >= 0.6:
            strengths.append(f"AI 引文可信度评分 {round(avg * 100)}%，内容被 AI 引用的潜力较高。")
    if brand_presence_history:
        fp = brand_presence_history[0].get("footprint_score")
        if fp and fp >= 60:
            strengths.append(f"品牌数字足迹分 {fp}/100，线上存在感已初步建立。")
    if ai_crawler_history:
        blocked = ai_crawler_history[0].get("blocked_count", 0)
        total = ai_crawler_history[0].get("total_crawlers", 14)
        if blocked == 0:
            strengths.append(f"全部 {total} 个 AI 爬虫均已放行，对 AI 索引完全开放。")

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
    if citability_history:
        avg = citability_history[0].get("avg_score")
        if avg is not None and avg < 0.4:
            risks.append(f"AI 引文可信度评分仅 {round(avg * 100)}%，内容结构化程度不足以被 AI 引用。")
    if ai_crawler_history:
        blocked = ai_crawler_history[0].get("blocked_count", 0)
        if blocked > 3:
            risks.append(f"有 {blocked} 个 AI 爬虫被 robots.txt 屏蔽，AI 索引受限。")
    if brand_presence_history:
        fp = brand_presence_history[0].get("footprint_score")
        if fp is not None and fp < 30:
            risks.append(f"品牌数字足迹分仅 {fp}/100，线上存在感薄弱。")
    # Flag critical/warning insights as risks
    critical_insights = [i for i in insights if i.get("severity") in ("critical", "warning")]
    for ins in critical_insights[:3]:
        risks.append(f"[{ins['severity'].upper()}] {ins['title']}：{ins['summary']}")

    change_lines: list[str] = []
    if previous_human:
        if seo_delta is not None:
            change_lines.append(f"SEO 相比上一版变动 {seo_delta:+.2f}。")
        if geo_delta is not None:
            change_lines.append(f"GEO 相比上一版变动 {geo_delta:+.0f}。")
        if serp_latest:
            top_keyword = serp_latest[0]
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
        "insights": insights,
        "citability": citability_history,
        "ai_crawler": ai_crawler_history,
        "brand_presence": brand_presence_history,
        "discussions": discussions[:12],
        "serp_latest": serp_latest,
        "graph_data": graph_data,
        "recent_approvals": recent_approvals,
        "strengths": strengths,
        "risks": risks,
        "change_lines": change_lines,
        "previous_report_excerpt": (previous_human["content"][:2000] if previous_human else ""),
    }
    data_sources = [
        latest.get("seo"), latest.get("geo"), latest.get("community"),
        serp_latest, keywords, competitor_cards, insights,
        citability_history, ai_crawler_history, brand_presence_history,
        discussions, graph_data,
    ]
    sample_count = sum(1 for item in data_sources if item)
    meta = {
        "sample_count": sample_count,
        "total_data_sources": len(data_sources),
        "low_sample": sample_count < 3,
        "facts_summary": (
            f"{len(keywords)} 个关键词, {len(competitor_cards)} 个竞品, "
            f"{len(findings)} 条发现, {len(recommendations)} 条建议, "
            f"{len(insights)} 条洞察, {len(discussions)} 条社区讨论, "
            f"{len(citability_history)} 条引文分析, {len(ai_crawler_history)} 条爬虫检测, "
            f"{len(brand_presence_history)} 条品牌存在感分析"
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
    recommendations = await _get_recent_recommendations(project_id, limit=12)
    findings = await storage.get_task_findings_by_project(project_id, limit=15)
    serp_latest = await storage.get_all_serp_latest(project_id)

    # --- Multi-agent enrichment ---
    insights = await storage.list_insights(project_id=project_id, limit=15)
    citability_history = await storage.get_citability_history(project_id, limit=5)
    ai_crawler_history = await storage.get_ai_crawler_history(project_id, limit=5)
    brand_presence_history = await storage.get_brand_presence_history(project_id, limit=5)

    data_sources = [seo_history, geo_history, community_history, serp_latest,
                    insights, citability_history, ai_crawler_history, brand_presence_history]
    sample_count = sum(1 for items in data_sources if items)
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
    if citability_history:
        avg = citability_history[0].get("avg_score")
        if avg is not None:
            top_changes.append(f"AI 引文可信度评分 {round(avg * 100)}%。")
    if brand_presence_history:
        fp = brand_presence_history[0].get("footprint_score")
        if fp is not None:
            top_changes.append(f"品牌数字足迹分 {fp}/100。")
    if low_sample:
        top_changes.insert(0, "样本稀疏，以下结论仅供方向判断。")

    facts = {
        "project": project,
        "window_start": window_start,
        "window_end": window_end,
        "seo_history": seo_history,
        "geo_history": geo_history,
        "community_history": community_history,
        "discussions": discussions[:12],
        "serp_latest": serp_latest,
        "findings": findings,
        "recommendations": recommendations,
        "insights": insights,
        "citability": citability_history,
        "ai_crawler": ai_crawler_history,
        "brand_presence": brand_presence_history,
        "recent_approvals": recent_approvals,
        "top_changes": top_changes[:5],
    }
    meta = {
        "sample_count": sample_count,
        "total_data_sources": len(data_sources),
        "low_sample": low_sample,
        "facts_summary": (
            f"SEO 样本 {len(seo_history)}, GEO 样本 {len(geo_history)}, "
            f"Community 样本 {len(community_history)}, SERP 关键词 {len(serp_latest)}, "
            f"洞察 {len(insights)} 条, 引文分析 {len(citability_history)} 条, "
            f"爬虫检测 {len(ai_crawler_history)} 条, 品牌存在感 {len(brand_presence_history)} 条"
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
            "## 1. 执行摘要与项目定性",
            f"- {project['brand_name']} 是一个 {project['category']} 项目，当前更适合被定义为“监控基础已建立，但增长叙事仍需强化”的阶段。",
            "",
            "## 2. 核心竞争力与优势护城河解析",
            *[f"- {item}" for item in strengths[:4]],
            "",
            "## 3. 风险扫描与增长短板预警",
            *[f"- {item}" for item in risks[:4]],
            "",
            "## 4. 竞品全景与流量抢占分析",
        ]
        competitors = facts.get("competitors") or []
        if competitors:
            lines.extend(
                f"- 已记录竞品 {item['name']}，建议围绕其关键词和定位做差异化挖掘与布局。"
                for item in competitors[:3]
            )
        else:
            lines.append("- 当前竞品画像仍然稀薄，差异化判断的置信度有限。")
        lines.extend(["", "## 5. 目标受众与社区舆论洞察"])
        lines.append("- 目前需积累更多社区及社媒上的原生态提及，以完善真实用户画像与情绪洞察。")
        lines.extend(["", "## 6. 下一阶段 CMO 战略规划与具体执行行动"])
        if recommendations:
            lines.extend(f"- {item['title']}：{item['summary']}" for item in recommendations[:4])
        else:
            lines.append("- 先补齐各个维度的监控基线，再进入明确无误的增长与执行阶段。")
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
        "你是 AI CMO（首席营销官），拥有完整的多智能体营销系统：SEO审计专家、GEO(AI搜索可见性)分析师、"
        "SERP排名追踪器、社区舆情监控(Reddit/HN/Dev.to/知乎/V2EX/掘金等)、AI引文可信度(Citability)评估引擎、"
        "AI爬虫检测模块、品牌数字足迹(Brand Presence)扫描器、竞品知识图谱、以及Insights洞察引擎。"
        "以下事实包(facts)是上述所有智能体在真实运行中采集到的一手数据。\n\n"
        "核心原则：\n"
        "1. 你必须对事实包中的每一类数据进行深入解读，不能遗漏任何智能体的产出。\n"
        "2. 不是简单罗列数据，而是像真正的 CMO 那样做业务推演——数据现象背后意味着什么？对增长有什么影响？应该怎么做？\n"
        "3. 不要虚构数据；某个维度数据缺失时，明确标注并说明获取方法。\n"
        "4. 必须使用中文输出。\n"
        "5. 报告要足够深入和详实，像一份面向CEO/投资人级别的商业分析文档。\n"
    )
    if kind == "strategic" and audience == "human":
        system = (
            f"{system_common}"
            "你的任务是生成一份极其深入的战略分析报告。输出 Markdown，报告总长度应在 2000-4000 字之间。\n\n"
            "严格按以下 6 大模块结构生成，每个模块都必须展开详细论述，不能用简短的一两句话敷衍：\n\n"
            "## 1. 执行摘要与项目定性 (Executive Summary)\n"
            "  - 一句话定义项目当前所处的增长阶段\n"
            "  - 从 SEO分数、GEO分数、品牌足迹分、AI引文可信度等多维指标综合评估项目的「数字化健康度」\n"
            "  - 如果有历史报告，对比版本差异并给出趋势判断\n\n"
            "## 2. 核心竞争力与优势护城河解析 (Core Competencies)\n"
            "  - 逐一解读每个优势信号背后的商业含义\n"
            "  - 分析 AI 引文可信度(Citability)和 AI爬虫放行状态对「被AI推荐」的影响\n"
            "  - 社区讨论中的正面信号与品牌数字足迹的协同效应\n"
            "  - SERP排名中已拿下的关键词意味着什么流量机会\n\n"
            "## 3. 风险扫描与增长短板预警 (Risk Scanning)\n"
            "  - 逐一深入解读每个风险信号的根因和潜在影响\n"
            "  - 结合 Insights 洞察系统中的 warning/critical 级别告警做交叉验证\n"
            "  - 评估哪些风险会直接影响获客转化，哪些是长期隐患\n"
            "  - 给出风险优先级排序\n\n"
            "## 4. 竞品全景与流量抢占分析 (Competitive Landscape)\n"
            "  - 如果有竞品数据和知识图谱数据，做详细的竞品对比分析\n"
            "  - 关键词重叠与差异化机会\n"
            "  - SERP中的直接竞争态势\n"
            "  - 在AI搜索(GEO)中的相对位置\n"
            "  - 如果竞品数据不完善，指出如何补充\n\n"
            "## 5. 目标受众与社区舆论洞察 (Audience & Community Sentiment)\n"
            "  - 分析社区讨论(discussions)的主题和情绪基调\n"
            "  - 从社区流量来源(Reddit、HN、知乎、V2EX等)推断用户画像\n"
            "  - 审批队列中的内容产出动势如何\n"
            "  - 品牌在各个平台上的存在感差异\n\n"
            "## 6. 下一阶段 CMO 战略规划与具体执行行动 (CMO Strategy & Actions)\n"
            "  - 基于以上全部分析给出 3-5 个可执行的战略方向\n"
            "  - 每个方向要具体到：由哪个Agent执行、预期指标变化、实施优先级\n"
            "  - 给一个清晰的「30天行动路线图」\n"
            "  - 标明需要人工介入的关键节点\n"
        )
        user = (
            f"项目：{project['brand_name']} ({project['category']})\n"
            f"目标网址：{project['url']}\n"
            f"版本是否已有历史报告：{previous_exists}\n"
            f"数据来源覆盖度：{meta.get('sample_count', 0)}/{meta.get('total_data_sources', 0)} 个数据源有数据\n"
            f"摘要元数据：{_json_dump(meta)}\n\n"
            f"=== 完整事实包（来自所有智能体的采集结果）===\n{_json_dump(facts)}"
        )
        return system, user

    if kind == "strategic" and audience == "agent":
        system = (
            f"{system_common}"
            "输出 Markdown，保持简短精炼，像给执行团队的行动简报。结构固定为：\n"
            "1. 战略目标（一句话）\n"
            "2. 约束条件（不可逾越的底线）\n"
            "3. 优先方向（按优先级排序的 3-5 个方向）\n"
            "4. 推荐执行 Agent 分工（哪个Agent负责哪个方向）\n"
            "5. 禁止事项\n"
            "6. 关键数据指标当前值（快速参考）"
        )
        user = f"项目战略事实包：\n{_json_dump({'meta': meta, 'facts': facts})}"
        return system, user

    if kind == "periodic" and audience == "human":
        system = (
            f"{system_common}"
            "你的任务是生成一份深度周报。输出 Markdown，报告总长度应在 1500-3000 字之间。\n\n"
            "严格按以下结构生成，每个模块都要做深入的业务推导，不能停留在数据罗列层面：\n\n"
            "## 1. 本周最重要的变化 (Top Changes)\n"
            "  - 列出 3-5 个最重要的变化，每个变化不仅要说「发生了什么」，还要解释「为什么重要」「对增长意味着什么」\n"
            "  - 如果有 AI引文可信度、品牌数字足迹的变化也要覆盖\n\n"
            "## 2. 多维度趋势深度分析 (SEO/GEO/SERP/Community/Citability/Brand Presence)\n"
            "  - 对每个有数据的维度做趋势诊断（上升/下降/持平），并分析走势背后的原因\n"
            "  - 做跨维度关联分析：例如 SEO得分下降是否影响了SERP排名？社区讨论增加是否推动了GEO可见性？\n"
            "  - AI爬虫放行状态有无变化？AI引文可信度的趋势如何？\n\n"
            "## 3. 本周新增风险与亮点 (Risks & Wins)\n"
            "  - 结合 Insights 洞察系统的告警做深入解读\n"
            "  - 风险要给出具体影响评估和缓解建议\n"
            "  - 亮点要说明如何扩大战果\n\n"
            "## 4. 竞品与市场信号变化 (Competitive & Market Signals)\n"
            "  - 社区讨论中有无竞品相关的新动向\n"
            "  - SERP排名中竞品的排名变化\n"
            "  - 审批队列中的内容产出情况\n\n"
            "## 5. 下周战略焦点与执行计划 (Next Week Strategy)\n"
            "  - 给出 3-5 个具体的下周行动项\n"
            "  - 每个行动项标明负责的Agent和预期结果\n"
            "  - 标注需要人工决策的事项\n\n"
            "样本稀疏时，必须在报告开头显式标注置信度。"
        )
        user = (
            f"项目：{project['brand_name']} ({project['category']})\n"
            f"统计窗口：{meta['window_start']} 到 {meta['window_end']}\n"
            f"数据来源覆盖度：{meta.get('sample_count', 0)}/{meta.get('total_data_sources', 0)} 个数据源有数据\n"
            f"元数据：{_json_dump(meta)}\n\n"
            f"=== 完整事实包（来自所有智能体的采集结果）===\n{_json_dump(facts)}"
        )
        return system, user

    # periodic / agent
    system = (
        f"{system_common}"
        "输出 Markdown，保持像给执行 Agent 的周度行动简报。结构固定为：\n"
        "1. 项目与置信度\n"
        "2. 本周关键指标快照\n"
        "3. 下周重点目标\n"
        "4. 优先方向与 Agent 分工\n"
        "5. 护栏与禁止事项"
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
    used_fallback = False
    used_pipeline = False
    llm_error = None
    model = await _get_report_model()
    content = ""

    # Human reports use the deep multi-agent pipeline;
    # Agent briefs stay single-call (they need to be concise).
    if audience == "human":
        try:
            from opencmo.report_pipeline import run_deep_report_pipeline

            content = await run_deep_report_pipeline(
                facts, meta, previous_exists, kind=kind,
            )
            used_pipeline = True
            if not content.strip():
                raise RuntimeError("Pipeline returned empty report.")
        except Exception as pipeline_exc:
            logger.warning(
                "Deep pipeline failed for %s/%s, falling back to single-call: %s",
                kind, audience, pipeline_exc,
            )
            # Fallback to single-call LLM
            try:
                system_prompt, user_prompt = _prompts(kind, audience, facts, meta, previous_exists)
                content = await _generate_llm_markdown(system_prompt, user_prompt)
                if not content.strip():
                    raise RuntimeError("LLM returned empty report content.")
            except Exception as exc:
                used_fallback = True
                llm_error = str(exc) or exc.__class__.__name__
                logger.exception("Report generation fell back to template for %s/%s", kind, audience)
                content = _fallback_markdown(kind, audience, facts, meta, previous_exists)
    else:
        # Agent brief — single-call path
        system_prompt, user_prompt = _prompts(kind, audience, facts, meta, previous_exists)
        try:
            content = await _generate_llm_markdown(system_prompt, user_prompt)
            if not content.strip():
                raise RuntimeError("LLM returned empty report content.")
        except Exception as exc:
            used_fallback = True
            llm_error = str(exc) or exc.__class__.__name__
            logger.exception("Report generation fell back to template for %s/%s", kind, audience)
            content = _fallback_markdown(kind, audience, facts, meta, previous_exists)

    record_meta = {
        **meta,
        "used_fallback": used_fallback,
        "used_pipeline": used_pipeline,
        "model": model,
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

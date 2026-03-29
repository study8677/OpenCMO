"""Multi-agent deep report pipeline.

Replaces the single-LLM-call report generation with a 6-phase pipeline:
  Phase 1  Reflection Agent    — per-dimension quality auditors (parallel) + aggregator
  Phase 2  Insight Distiller   — per-dimension insight agents (parallel) + cross-cutter
  Phase 3  Outline Planner     — narrative structure with per-section briefs
  Phase 4  Section Writers     — parallel per-section authoring
  Phase 5  Section Grader      — review loop (max 2 retries)
  Phase 6  Report Synthesizer  — per-section summarizers (parallel) + intro/exec/strategy writers

KEY DESIGN: Phases 1, 2, and 6 use MULTIPLE sub-agents per dimension/section
instead of a single monolithic LLM call.  This prevents context overflow when
data is large (e.g. 1000+ keywords, 28 competitors).

Only used for ``audience="human"`` reports.  Agent briefs stay single-call.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Maximum retry count for the grader loop (Phase 5)
_MAX_GRADER_RETRIES = 2
# Minimum average score to pass the grader
_GRADER_PASS_THRESHOLD = 3.8


def _json_dump(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


def _extract_json(text: str) -> dict | list:
    """Best-effort JSON extraction from LLM output that may contain markdown fences."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```\w*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
        cleaned = cleaned.strip()
    return json.loads(cleaned)


def _truncate_list(data: list | None, max_items: int, sort_key: str | None = None) -> list:
    """Truncate a list to max_items, optionally sorting first."""
    if not data:
        return []
    items = list(data)
    if sort_key:
        try:
            items.sort(key=lambda x: x.get(sort_key, 0), reverse=True)
        except Exception:
            pass
    return items[:max_items]


# ---------------------------------------------------------------------------
# LLM call helpers (import the shared infra from reports.py at call time)
# ---------------------------------------------------------------------------

async def _llm_text_call(system: str, user: str) -> str:
    """Single LLM call returning plain text / markdown."""
    from opencmo.reports import _generate_llm_markdown
    return await _generate_llm_markdown(system, user)


async def _llm_json_call(system: str, user: str) -> dict | list:
    """Single LLM call expecting JSON output."""
    raw = await _llm_text_call(system, user)
    return _extract_json(raw)


# ---------------------------------------------------------------------------
# Data dimension slicing — split facts into per-dimension chunks
# ---------------------------------------------------------------------------

_DIMENSIONS = [
    {
        "id": "seo_tech",
        "name": "SEO & 技术健康度",
        "keys": ["seo_latest", "ai_crawler_history"],
        "description": "网站 SEO 审计数据和 AI 爬虫可达性数据",
    },
    {
        "id": "search_visibility",
        "name": "搜索可见性 & 排名",
        "keys": ["serp_snapshots", "keywords"],
        "description": "SERP 关键词排名和搜索可见性数据",
        "truncate": {"keywords": 30, "serp_snapshots": 25},
    },
    {
        "id": "ai_visibility",
        "name": "AI 可见性 & 品牌引用",
        "keys": ["geo_latest", "citability_history", "brand_presence_history"],
        "description": "GEO 评分、AI 平台引文可信度和品牌存在感",
    },
    {
        "id": "community_market",
        "name": "社区 & 市场信号",
        "keys": ["community_latest", "discussions", "insights_history"],
        "description": "社区讨论、市场趋势和 AI 洞察告警",
        "truncate": {"discussions": 15, "insights_history": 10},
    },
    {
        "id": "competitive",
        "name": "竞品 & 生态定位",
        "keys": ["competitors", "graph_data", "approvals"],
        "description": "竞品信息、知识图谱关系和内容审批队列",
        "truncate": {"competitors": 20},
    },
]


def _slice_dimension(facts: dict, dimension: dict) -> dict:
    """Extract facts for one dimension, applying truncation rules."""
    sliced = {}
    truncate_rules = dimension.get("truncate", {})
    for key in dimension["keys"]:
        data = facts.get(key)
        if data is None:
            sliced[key] = None
            continue
        max_items = truncate_rules.get(key)
        if max_items and isinstance(data, list):
            sliced[key] = _truncate_list(data, max_items)
        else:
            sliced[key] = data
    return sliced


# ===================================================================
# Phase 1 — Reflection Agent (MULTI-AGENT: per-dimension auditors)
# ===================================================================

_REFLECT_DIM_SYSTEM = """\
你是一位专注于 {dim_name} 维度的数据质检专家。

请审计以下 {dim_name} 维度的数据：

1. **数据完整性**：数据是否完整？有无缺失字段或空值？样本量是否足够？
2. **数据质量**：数据是否有异常值？是否前后一致？
3. **可用性**：这些数据能否支撑高质量的分析？有哪些局限？

返回 JSON：
{{
  "dimension": "{dim_id}",
  "quality_score": 0到100的整数,
  "issues": ["问题描述"],
  "anomalies": ["异常描述"],
  "summary": "一句话总结本维度数据质量",
  "data_available": true/false
}}

必须返回合法 JSON，不要加 markdown 代码块。"""


_REFLECT_AGG_SYSTEM = """\
你是数据质量审计的总负责人。以下是 5 个维度质检专家各自的审计结果。

请汇总各维度的审计结论，完成交叉验证：

1. **交叉验证**：
   - SEO 审计结果与 SERP 排名数据是否一致？
   - GEO 评分趋势与 Brand Presence 数据是否矛盾？
   - Community 舆情与 Insights 告警是否存在信号冲突？
   - AI Crawler 放行状态与 Citability 评分是否协调？

2. **综合判断**：数据整体是否充足到能生成高质量报告？

返回 JSON：
{
  "data_quality_score": 加权平均后的0到100整数,
  "issues": ["汇总后的关键问题"],
  "anomalies": ["跨维度异常"],
  "cross_validation_notes": ["交叉验证发现"],
  "validated_summary": "一段话总结整体数据质量",
  "confidence_level": "high/medium/low",
  "dimension_scores": {"seo_tech": 80, "search_visibility": 60, ...}
}

必须返回合法 JSON，不要加 markdown 代码块。"""


async def _reflect_one_dimension(facts: dict, dim: dict, meta: dict) -> dict:
    """Run one dimension-specific quality auditor."""
    dim_data = _slice_dimension(facts, dim)
    project = facts.get("project", {})
    system = _REFLECT_DIM_SYSTEM.format(dim_name=dim["name"], dim_id=dim["id"])
    user = (
        f"项目：{project.get('brand_name', '?')} ({project.get('category', '?')})\n"
        f"维度：{dim['name']} — {dim['description']}\n\n"
        f"=== {dim['name']} 维度数据 ===\n{_json_dump(dim_data)}"
    )
    try:
        result = await _llm_json_call(system, user)
        if not isinstance(result, dict):
            result = {"dimension": dim["id"], "quality_score": 50, "issues": [], "summary": str(result), "data_available": True}
        result["dimension"] = dim["id"]
        return result
    except Exception as exc:
        logger.warning("[Phase 1] Dimension %s audit failed: %s", dim["id"], exc)
        return {"dimension": dim["id"], "quality_score": 50, "issues": [str(exc)], "summary": "审计失败", "data_available": True}


async def _phase_reflect(facts: dict, meta: dict) -> dict:
    """Phase 1: Run per-dimension auditors in parallel, then aggregate."""
    logger.info("[Pipeline Phase 1] Reflection — %d dimension auditors in parallel", len(_DIMENSIONS))

    # Run all dimension auditors in parallel
    dim_results = await asyncio.gather(
        *[_reflect_one_dimension(facts, dim, meta) for dim in _DIMENSIONS],
        return_exceptions=True,
    )

    # Collect results
    dim_reports = []
    for i, result in enumerate(dim_results):
        if isinstance(result, Exception):
            logger.warning("[Phase 1] Dimension %s failed: %s", _DIMENSIONS[i]["id"], result)
            dim_reports.append({"dimension": _DIMENSIONS[i]["id"], "quality_score": 50, "issues": [str(result)], "summary": "审计异常"})
        else:
            dim_reports.append(result)
            logger.info("[Phase 1] Dimension %s — score: %s", result.get("dimension", "?"), result.get("quality_score", "?"))

    # Aggregate with a separate agent
    logger.info("[Pipeline Phase 1] Aggregating %d dimension audits", len(dim_reports))
    project = facts.get("project", {})
    user = (
        f"项目：{project.get('brand_name', '?')} ({project.get('category', '?')})\n"
        f"数据覆盖度：{meta.get('sample_count', 0)}/{meta.get('total_data_sources', 0)} 个数据源有数据\n\n"
        f"=== 各维度审计结果 ===\n{_json_dump(dim_reports)}"
    )
    try:
        aggregated = await _llm_json_call(_REFLECT_AGG_SYSTEM, user)
        if not isinstance(aggregated, dict):
            aggregated = {"data_quality_score": 50, "validated_summary": str(aggregated), "confidence_level": "medium"}
        logger.info(
            "[Pipeline Phase 1] Aggregated quality: %s, confidence: %s",
            aggregated.get("data_quality_score", "?"), aggregated.get("confidence_level", "?"),
        )
        return aggregated
    except Exception as exc:
        logger.warning("[Pipeline Phase 1] Aggregation failed: %s — using simple average", exc)
        scores = [r.get("quality_score", 50) for r in dim_reports]
        avg = sum(scores) // max(len(scores), 1)
        return {
            "data_quality_score": avg,
            "issues": [iss for r in dim_reports for iss in r.get("issues", [])],
            "validated_summary": f"各维度平均质量 {avg}/100（聚合失败，使用简单平均）",
            "confidence_level": "low",
        }


# ===================================================================
# Phase 2 — Insight Distiller (MULTI-AGENT: per-dimension analysts)
# ===================================================================

_DISTILL_DIM_SYSTEM = """\
你是一位专注于 {dim_name} 的数字营销分析师。

基于以下 {dim_name} 维度的数据，提炼分析性发现（insights）。

规则：
1. **解读数据**：不要罗列数据，要回答"so what?"
2. **趋势判断**：如有历史数据，判断上升/下降/稳定 + 变化幅度
3. **量化表达**：用具体数字，避免模糊表述
4. **优先级排序**：按业务影响力排序

输出 JSON：
{{
  "dimension": "{dim_id}",
  "insights": [
    {{
      "id": "{dim_id}-INS-001",
      "title": "简短标题",
      "finding": "详细发现描述，包含具体数字...",
      "evidence": ["{dim_name}"],
      "impact_level": "critical/high/medium/low",
      "recommended_section": "建议放入报告的章节主题"
    }}
  ]
}}

要求：产出 2-4 条高质量 insights。
必须返回合法 JSON，不要加 markdown 代码块。"""


_DISTILL_CROSS_SYSTEM = """\
你是一位资深的跨维度商业分析师。以下是 5 个维度分析师各自提炼的 insights。

你的任务：

1. **发现跨维度关联**：
   - 例：SEO 分数高但 SERP 排名低 → 内容质量问题
   - 例：GEO 评分上升但 Brand Presence 无变化 → AI 引文为一次性
   - 例：社区热度高但 SERP 不变 → 社交信号未转化为搜索权重

2. **提炼贯穿主题**：识别 2-3 个跨多维度的战略主题

3. **生成执行摘要要点**：基于所有 insights 提炼 3-5 个一句话核心发现

4. **重新编号**：将所有 insights 统一编号为 INS-001, INS-002, ...

输出 JSON：
{
  "insights": [合并后的所有 insights，统一编号 INS-001...],
  "cross_cutting_themes": ["主题1", "主题2"],
  "executive_summary_points": ["核心发现1", "核心发现2"]
}

必须返回合法 JSON，不要加 markdown 代码块。"""


async def _distill_one_dimension(facts: dict, dim: dict, reflection: dict) -> dict:
    """Run one dimension-specific insight analyst."""
    dim_data = _slice_dimension(facts, dim)
    project = facts.get("project", {})
    dim_score = reflection.get("dimension_scores", {}).get(dim["id"], "?")

    system = _DISTILL_DIM_SYSTEM.format(dim_name=dim["name"], dim_id=dim["id"])
    user = (
        f"项目：{project.get('brand_name', '?')} ({project.get('category', '?')})\n"
        f"本维度质量评分：{dim_score}/100\n\n"
        f"=== {dim['name']} 维度数据 ===\n{_json_dump(dim_data)}"
    )
    try:
        result = await _llm_json_call(system, user)
        if not isinstance(result, dict):
            result = {"dimension": dim["id"], "insights": []}
        result["dimension"] = dim["id"]
        logger.info("[Phase 2] Dimension %s — %d insights", dim["id"], len(result.get("insights", [])))
        return result
    except Exception as exc:
        logger.warning("[Phase 2] Dimension %s distill failed: %s", dim["id"], exc)
        return {"dimension": dim["id"], "insights": []}


async def _phase_distill(facts: dict, meta: dict, reflection: dict) -> dict:
    """Phase 2: Run per-dimension insight analysts in parallel, then cross-cut."""
    logger.info("[Pipeline Phase 2] Insight Distiller — %d dimension analysts in parallel", len(_DIMENSIONS))

    dim_results = await asyncio.gather(
        *[_distill_one_dimension(facts, dim, reflection) for dim in _DIMENSIONS],
        return_exceptions=True,
    )

    # Collect all dimension insights
    all_dim_insights = []
    for i, result in enumerate(dim_results):
        if isinstance(result, Exception):
            logger.warning("[Phase 2] Dimension %s failed: %s", _DIMENSIONS[i]["id"], result)
            continue
        all_dim_insights.append(result)

    total_insights = sum(len(r.get("insights", [])) for r in all_dim_insights)
    logger.info("[Pipeline Phase 2] Collected %d insights from %d dimensions", total_insights, len(all_dim_insights))

    if total_insights == 0:
        raise RuntimeError("All dimension distillers produced 0 insights")

    # Cross-cutting synthesis
    logger.info("[Pipeline Phase 2] Cross-cutting synthesis")
    project = facts.get("project", {})
    user = (
        f"项目：{project.get('brand_name', '?')} ({project.get('category', '?')})\n"
        f"数据整体质量：{reflection.get('data_quality_score', '?')}/100\n\n"
        f"=== 各维度分析师的 Insights ===\n{_json_dump(all_dim_insights)}"
    )
    try:
        result = await _llm_json_call(_DISTILL_CROSS_SYSTEM, user)
        if not isinstance(result, dict):
            raise ValueError("Cross-cutter did not return a dict")
        insights = result.get("insights", [])
        logger.info("[Pipeline Phase 2] Final: %d insights, %d themes",
                     len(insights), len(result.get("cross_cutting_themes", [])))
        return result
    except Exception as exc:
        logger.warning("[Pipeline Phase 2] Cross-cutting failed: %s — using raw dimension insights", exc)
        # Fallback: merge all dimension insights with sequential numbering
        merged = []
        idx = 1
        for dim_result in all_dim_insights:
            for ins in dim_result.get("insights", []):
                ins["id"] = f"INS-{idx:03d}"
                merged.append(ins)
                idx += 1
        return {
            "insights": merged,
            "cross_cutting_themes": [],
            "executive_summary_points": [ins["title"] for ins in merged[:5]],
        }


# ===================================================================
# Phase 3 — Outline Planner (narrative structure)
# ===================================================================

_PLAN_SYSTEM = """\
你是一位资深的商业报告主编。基于以下分析发现，请规划一份深度商业分析报告的大纲。

要求：
1. 报告总字数目标：3000-5000字
2. 每个章节必须有明确的**核心论点**（不是描述性标题）
3. 每个章节必须指定使用哪些 insights (用 id 引用) 作为论据
4. 章节数量：4-6 个主体章节
5. 引言和战略建议章节标记为 is_final_section: true（它们最后写）

输出 JSON 格式：
{
  "report_title": "报告标题",
  "executive_summary_thesis": "一句话概括报告核心发现",
  "sections": [
    {
      "id": "sec-1",
      "title": "论点驱动的章节标题",
      "thesis": "本节核心论点：...",
      "insight_ids": ["INS-001", "INS-003"],
      "word_budget": 600,
      "is_final_section": false,
      "writing_guidance": "以数据趋势开头，用竞品对比佐证..."
    }
  ],
  "narrative_arc": "报告的叙事线索：从问题诊断 → 根因分析 → 机会识别 → 行动路线图"
}

注意：主体章节 is_final_section 设为 false，引言和战略建议设为 true。
必须返回合法 JSON，不要加 markdown 代码块。"""


async def _phase_plan_outline(
    facts: dict, distilled: dict, reflection: dict
) -> dict:
    """Phase 3: Plan the report outline with per-section briefs."""
    logger.info("[Pipeline Phase 3] Outline Planner — designing narrative")
    project = facts["project"]
    user = (
        f"品牌/业务上下文：\n"
        f"  品牌名：{project['brand_name']}\n"
        f"  类别：{project['category']}\n"
        f"  网址：{project['url']}\n"
        f"  数据质量：{reflection.get('data_quality_score', '?')}/100\n\n"
        f"分析发现（共 {len(distilled.get('insights', []))} 条）：\n"
        f"{_json_dump(distilled)}"
    )
    try:
        result = await _llm_json_call(_PLAN_SYSTEM, user)
        if not isinstance(result, dict):
            raise ValueError("Planner did not return a dict")
        sections = result.get("sections", [])
        logger.info(
            "[Pipeline Phase 3] Planned %d sections, arc: %s",
            len(sections),
            result.get("narrative_arc", "?")[:80],
        )
        return result
    except Exception as exc:
        logger.warning("[Pipeline Phase 3] Plan failed: %s", exc)
        raise


# ===================================================================
# Phase 4 — Section Writer (per-section authoring)
# ===================================================================

_WRITE_SECTION_SYSTEM = """\
你是一位资深的商业分析撰稿人。请为报告的一个章节撰写深度内容。

写作要求：
1. 以核心论点为纲，用数据和洞察论证
2. 不要罗列数据，要**解读**数据——回答"so what?"
3. 每个关键论断都要有数据支撑，引用数据来源用 [来源：Agent名称] 标注
4. 使用具体数字，避免模糊表述（不要用"较大""不错"这类词）
5. 段落之间要有逻辑递进，不是平铺
6. 每段 3-5 句话
7. 结尾要自然过渡到下一节的主题
8. 语气：专业但不晦涩，像 McKinsey 的行业报告
9. 必须包含至少一个"反直觉发现"或"深层洞察"

输出纯 Markdown 文本（不要 JSON，不要代码块包裹）。
以 ## 开头写章节标题，然后是正文段落。"""


async def _phase_write_section(
    outline: dict,
    section: dict,
    insights_map: dict[str, dict],
    completed_summaries: list[str] | None = None,
) -> str:
    """Phase 4: Write one report section."""
    section_id = section.get("id", "?")
    logger.info("[Pipeline Phase 4] Writing section: %s", section.get("title", section_id))

    relevant_insights = [
        insights_map[iid]
        for iid in section.get("insight_ids", [])
        if iid in insights_map
    ]

    user = (
        f"报告主题：{outline.get('report_title', '深度分析报告')}\n"
        f"报告叙事线索：{outline.get('narrative_arc', '无')}\n\n"
        f"== 本节任务 ==\n"
        f"标题：{section['title']}\n"
        f"核心论点：{section.get('thesis', '无')}\n"
        f"字数预算：{section.get('word_budget', 600)} 字\n"
        f"写作指导：{section.get('writing_guidance', '按论点展开论证')}\n\n"
        f"== 本节可用洞察（共 {len(relevant_insights)} 条）==\n"
        f"{_json_dump(relevant_insights)}\n"
    )
    if completed_summaries:
        user += (
            f"\n== 已完成的其他章节摘要 ==\n"
            + "\n".join(f"- {s}" for s in completed_summaries)
        )

    return await _llm_text_call(_WRITE_SECTION_SYSTEM, user)


# ===================================================================
# Phase 5 — Section Grader (review loop)
# ===================================================================

_GRADE_SECTION_SYSTEM = """\
你是一位严格的商业报告审稿人。请评审以下报告章节。

按以下维度评分（1-5分）：
1. **论点清晰度 (clarity)**：核心论点是否明确？论证是否围绕论点展开？
2. **数据深度 (depth)**：是否充分使用了可用数据？有"so what"分析而非简单罗列？
3. **洞察独特性 (originality)**：有超越表面的深层分析？有反直觉的发现？
4. **逻辑连贯性 (coherence)**：段落之间逻辑递进？论证链条完整？
5. **可操作性 (actionability)**：分析是否指向具体的行动建议？

返回 JSON：
{
  "scores": {"clarity": 4, "depth": 3, "originality": 3, "coherence": 4, "actionability": 4},
  "average_score": 3.6,
  "pass": false,
  "revision_instructions": "需要改进的具体说明...",
  "specific_fixes": ["具体修改建议1", "具体修改建议2"]
}

average_score >= 3.8 则 pass 设为 true。
必须返回合法 JSON，不要加 markdown 代码块。"""


async def _phase_grade_section(section: dict, content: str) -> dict:
    """Phase 5: Grade a written section. Returns scores + pass/fail."""
    section_id = section.get("id", "?")
    logger.info("[Pipeline Phase 5] Grading section: %s", section.get("title", section_id))
    user = (
        f"== 章节要求 ==\n"
        f"核心论点：{section.get('thesis', '无')}\n"
        f"字数预算：{section.get('word_budget', 600)}\n"
        f"可用洞察 IDs：{section.get('insight_ids', [])}\n\n"
        f"== 章节内容 ==\n{content}"
    )
    try:
        result = await _llm_json_call(_GRADE_SECTION_SYSTEM, user)
        if not isinstance(result, dict):
            result = {"average_score": 4.0, "pass": True, "revision_instructions": ""}
        avg = result.get("average_score", 4.0)
        result["pass"] = avg >= _GRADER_PASS_THRESHOLD
        logger.info(
            "[Pipeline Phase 5] Section %s score: %.1f — %s",
            section_id, avg, "PASS" if result["pass"] else "NEEDS REVISION",
        )
        return result
    except Exception as exc:
        logger.warning("[Pipeline Phase 5] Grading failed for %s: %s — auto-pass", section_id, exc)
        return {"average_score": 4.0, "pass": True, "revision_instructions": ""}


_REVISE_SECTION_SYSTEM = """\
你是一位资深的商业分析撰稿人。审稿人对你的章节给出了修改意见，请据此修订内容。

修改要求：
1. 保持原有论点和结构不变
2. 按审稿人的具体修改建议逐一改进
3. 加强数据深度和洞察独特性
4. 确保每个论断都有数据支撑

输出修订后的纯 Markdown 文本（不要 JSON，不要代码块包裹）。"""


async def _phase_revise_section(
    section: dict, original_content: str, grade: dict
) -> str:
    """Revise a section based on grader feedback."""
    logger.info("[Pipeline Phase 5] Revising section: %s", section.get("title", "?"))
    user = (
        f"== 原始章节 ==\n{original_content}\n\n"
        f"== 审稿人评分 ==\n{_json_dump(grade.get('scores', {}))}\n"
        f"总分：{grade.get('average_score', '?')}\n\n"
        f"== 修改指令 ==\n{grade.get('revision_instructions', '提升深度')}\n\n"
        f"== 具体修改建议 ==\n"
        + "\n".join(f"- {fix}" for fix in grade.get("specific_fixes", []))
    )
    return await _llm_text_call(_REVISE_SECTION_SYSTEM, user)


# ===================================================================
# Phase 6 — Report Synthesizer (MULTI-AGENT: summarizers + writers)
# ===================================================================

_SUMMARIZE_SECTION_SYSTEM = """\
你是一位报告编辑助手。请为以下报告章节生成一段精炼摘要。

要求：
1. 3-5 句话概括章节核心内容
2. 保留最关键的数据点
3. 提炼主要结论

输出纯文本摘要（不要 JSON，不要 Markdown 标题）。"""

_WRITE_EXEC_SUMMARY_SYSTEM = """\
你是一位面向高管的报告编辑。基于以下各章节摘要和核心发现，撰写执行摘要。

要求：
1. 200-300 字
2. 3-5 句话概括最关键的发现和建议
3. 面向高管，30 秒内让人抓住核心
4. 用一个引人注目的数据点或判断作为开头

输出纯 Markdown（以 ## 执行摘要 开头）。"""

_WRITE_INTRO_SYSTEM = """\
你是一位战略报告编辑。基于以下上下文信息，撰写报告引言。

要求：
1. 200-300 字
2. 不要用"本报告旨在"这类废话
3. 快速建立上下文：品牌定位、面对什么市场环境、为什么现在需要关注
4. 语调专业且有紧迫感

输出纯 Markdown（以 ## 引言 开头）。"""

_WRITE_STRATEGY_SYSTEM = """\
你是一位 CMO 级战略顾问。基于以下各章节分析摘要，提出战略建议。

要求：
1. 400-600 字
2. 基于所有章节的发现，提出 3-5 条优先行动建议
3. 每条建议标注优先级(P0/P1/P2)和预期影响
4. 建议之间有逻辑关系（先做什么、后做什么）
5. 标明可由 Agent 自动执行的动作 vs 需要人工决策的动作

输出纯 Markdown（以 ## 战略建议与行动路线图 开头）。"""


async def _summarize_one_section(section: dict, content: str) -> str:
    """Summarize one section into 3-5 sentences."""
    user = (
        f"章节标题：{section.get('title', '?')}\n"
        f"核心论点：{section.get('thesis', '?')}\n\n"
        f"== 章节内容 ==\n{content}"
    )
    try:
        return await _llm_text_call(_SUMMARIZE_SECTION_SYSTEM, user)
    except Exception as exc:
        logger.warning("[Phase 6] Summarize failed for %s: %s", section.get("id", "?"), exc)
        # Return first 200 chars as fallback summary
        return content[:200] + "..."


async def _phase_synthesize(
    outline: dict,
    section_contents: list[tuple[dict, str]],
    distilled: dict,
    facts: dict,
) -> str:
    """Phase 6: Multi-agent synthesis — parallel summarizers, then 3 specialist writers."""
    logger.info("[Pipeline Phase 6] Report Synthesizer — %d sub-agents", len(section_contents) + 3)

    project = facts["project"]

    # Step 1: Parallel per-section summarizers
    logger.info("[Pipeline Phase 6.1] Summarizing %d sections in parallel", len(section_contents))
    summary_tasks = [_summarize_one_section(sec, content) for sec, content in section_contents]
    summaries = await asyncio.gather(*summary_tasks, return_exceptions=True)

    section_summaries = []
    for i, (sec, _) in enumerate(section_contents):
        summary = summaries[i] if not isinstance(summaries[i], Exception) else f"(摘要失败: {sec.get('title', '?')})"
        section_summaries.append({"title": sec.get("title", "?"), "summary": summary})

    summaries_text = "\n\n".join(
        f"### {s['title']}\n{s['summary']}" for s in section_summaries
    )

    # Context for all synthesis writers (small — just summaries, not full content)
    synthesis_context = (
        f"品牌：{project['brand_name']} ({project['category']})\n"
        f"网址：{project['url']}\n"
        f"报告标题：{outline.get('report_title', '深度分析报告')}\n"
        f"叙事线索：{outline.get('narrative_arc', '无')}\n\n"
        f"核心发现要点：\n"
        + "\n".join(f"- {p}" for p in distilled.get("executive_summary_points", []))
        + f"\n\n贯穿主题：{', '.join(distilled.get('cross_cutting_themes', []))}\n\n"
        f"=== 各章节摘要 ===\n{summaries_text}"
    )

    # Step 2: Run exec summary + intro + strategy writers in parallel
    logger.info("[Pipeline Phase 6.2] Running 3 synthesis writers in parallel")

    exec_task = _llm_text_call(_WRITE_EXEC_SUMMARY_SYSTEM, synthesis_context)
    intro_task = _llm_text_call(_WRITE_INTRO_SYSTEM, synthesis_context)
    strategy_task = _llm_text_call(_WRITE_STRATEGY_SYSTEM, synthesis_context)

    exec_summary, intro, strategy = await asyncio.gather(
        exec_task, intro_task, strategy_task,
        return_exceptions=True,
    )

    # Handle failures gracefully
    if isinstance(exec_summary, Exception):
        logger.warning("[Phase 6] Exec summary failed: %s", exec_summary)
        exec_summary = "## 执行摘要\n\n（执行摘要生成失败，请查看各章节内容。）\n"
    if isinstance(intro, Exception):
        logger.warning("[Phase 6] Intro failed: %s", intro)
        intro = "## 引言\n\n（引言生成失败。）\n"
    if isinstance(strategy, Exception):
        logger.warning("[Phase 6] Strategy failed: %s", strategy)
        strategy = "## 战略建议与行动路线图\n\n（战略建议生成失败，请参考各章节分析。）\n"

    # Step 3: Assemble final report (no LLM needed — just concatenation)
    logger.info("[Pipeline Phase 6.3] Assembling final report")
    report_title = outline.get("report_title", f"{project['brand_name']} 深度战略分析")
    sections_md = "\n\n".join(content for _, content in section_contents)

    final_report = (
        f"# {report_title}\n\n"
        f"{exec_summary}\n\n"
        f"{intro}\n\n"
        f"{sections_md}\n\n"
        f"{strategy}"
    )

    return final_report


# ===================================================================
# Pipeline orchestrator
# ===================================================================

async def run_deep_report_pipeline(
    facts: dict,
    meta: dict,
    previous_exists: bool,
    *,
    kind: str = "strategic",
) -> str:
    """Run the full 6-phase deep report pipeline.

    Returns the final Markdown report content.
    Raises on unrecoverable errors (caller should fallback).
    """
    logger.info(
        "=== Deep Report Pipeline START (%s) for %s ===",
        kind, facts["project"]["brand_name"],
    )

    # ── Phase 1: Reflection (parallel per-dimension) ──
    reflection = await _phase_reflect(facts, meta)

    # ── Phase 2: Distill insights (parallel per-dimension) ──
    distilled = await _phase_distill(facts, meta, reflection)

    # ── Phase 3: Plan outline ──
    outline = await _phase_plan_outline(facts, distilled, reflection)

    # Build insight lookup map
    insights_list = distilled.get("insights", [])
    insights_map: dict[str, dict] = {ins["id"]: ins for ins in insights_list if "id" in ins}

    # Separate main sections from final sections (intro/conclusion)
    sections = outline.get("sections", [])
    main_sections = [s for s in sections if not s.get("is_final_section", False)]

    if not main_sections:
        raise RuntimeError("Outline planner returned no main sections")

    # ── Phase 4 + 5: Write & Grade (with retry loop) ──
    async def _write_and_grade(section: dict) -> tuple[dict, str]:
        """Write a section, grade it, revise if needed."""
        content = await _phase_write_section(outline, section, insights_map)

        for attempt in range(_MAX_GRADER_RETRIES + 1):
            grade = await _phase_grade_section(section, content)
            if grade.get("pass", False):
                return section, content
            if attempt < _MAX_GRADER_RETRIES:
                logger.info(
                    "[Pipeline] Section %s failed grading (attempt %d/%d), revising...",
                    section.get("id", "?"), attempt + 1, _MAX_GRADER_RETRIES,
                )
                content = await _phase_revise_section(section, content, grade)
            else:
                logger.warning(
                    "[Pipeline] Section %s exhausted retries, using last version",
                    section.get("id", "?"),
                )

        return section, content

    # Run all main sections in parallel
    logger.info("[Pipeline] Writing %d main sections in parallel...", len(main_sections))
    section_results = await asyncio.gather(
        *[_write_and_grade(sec) for sec in main_sections],
        return_exceptions=True,
    )

    # Collect successful sections, skip failures
    completed_sections: list[tuple[dict, str]] = []
    for i, result in enumerate(section_results):
        if isinstance(result, Exception):
            logger.error("[Pipeline] Section %d failed: %s — skipping", i, result)
            continue
        completed_sections.append(result)

    if not completed_sections:
        raise RuntimeError("All section writers failed")

    # ── Phase 6: Synthesize (parallel summarizers + parallel writers) ──
    final_report = await _phase_synthesize(outline, completed_sections, distilled, facts)

    logger.info(
        "=== Deep Report Pipeline COMPLETE — %d chars, %d sections ===",
        len(final_report), len(completed_sections),
    )
    return final_report

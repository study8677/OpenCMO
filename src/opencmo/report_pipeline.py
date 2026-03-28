"""Multi-agent deep report pipeline.

Replaces the single-LLM-call report generation with a 6-phase pipeline:
  Phase 1  Reflection Agent    — data quality audit & cross-validation
  Phase 2  Insight Distiller   — raw facts → analytical insights
  Phase 3  Outline Planner     — narrative structure with per-section briefs
  Phase 4  Section Writers     — parallel per-section authoring
  Phase 5  Section Grader      — review loop (max 2 retries)
  Phase 6  Report Synthesizer  — intro + conclusion + unified editing

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
# Maximum number of rescan attempts in reflection (Phase 1)
_MAX_RESCAN_ROUNDS = 1


def _json_dump(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


def _extract_json(text: str) -> dict | list:
    """Best-effort JSON extraction from LLM output that may contain markdown fences."""
    cleaned = text.strip()
    # Strip markdown code fences
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```\w*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
        cleaned = cleaned.strip()
    return json.loads(cleaned)


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


# ===================================================================
# Phase 1 — Reflection Agent (data quality audit)
# ===================================================================

_REFLECT_SYSTEM = """\
你是一位资深的商业分析质检专家。你的任务是审计以下来自 9 个数据采集 Agent 的产出汇总。

请执行以下分析：

1. **数据完整性检查**：
   - 哪些维度的数据缺失或样本量不足？
   - 有没有 Agent 返回了空结果或错误？

2. **交叉验证**：
   - SEO 审计结果与 SERP 排名数据是否一致？（如 SEO 分高但排名低，说明内容质量可能有问题）
   - GEO 评分趋势与 Brand Presence 数据是否矛盾？
   - Community 舆情与 Insights 告警是否存在信号冲突？
   - AI Crawler 放行状态与 Citability 评分是否协调？

3. **异常检测**：
   - 标记任何看起来异常的数据点（如排名突然跳变、评分与历史偏差 >30%）
   - 判断这些异常是真实变化还是数据采集问题

4. **缺口判断**：
   - 基于以上分析，数据是否充足到能生成高质量报告？

返回 JSON 格式：
{
  "data_quality_score": 0到100的整数,
  "issues": ["问题描述1", "问题描述2"],
  "anomalies": ["异常描述1"],
  "cross_validation_notes": ["交叉验证发现1"],
  "validated_summary": "一段话总结数据质量状况",
  "confidence_level": "high/medium/low"
}

必须返回合法 JSON，不要加 markdown 代码块。"""


async def _phase_reflect(facts: dict, meta: dict) -> dict:
    """Phase 1: Audit data quality across all agent outputs."""
    logger.info("[Pipeline Phase 1] Reflection Agent — data quality audit")
    user = (
        f"项目：{facts['project']['brand_name']} ({facts['project']['category']})\n"
        f"数据覆盖度：{meta.get('sample_count', 0)}/{meta.get('total_data_sources', 0)} 个数据源有数据\n\n"
        f"=== 全部 Agent 数据汇总 ===\n{_json_dump(facts)}"
    )
    try:
        result = await _llm_json_call(_REFLECT_SYSTEM, user)
        if not isinstance(result, dict):
            result = {"data_quality_score": 50, "issues": [], "validated_summary": str(result), "confidence_level": "medium"}
        logger.info(
            "[Pipeline Phase 1] Quality score: %s, confidence: %s",
            result.get("data_quality_score", "?"),
            result.get("confidence_level", "?"),
        )
        return result
    except Exception as exc:
        logger.warning("[Pipeline Phase 1] Reflection failed, continuing: %s", exc)
        return {
            "data_quality_score": 50,
            "issues": [f"Reflection phase error: {exc}"],
            "validated_summary": "数据质量审计未完成，以原始数据继续。",
            "confidence_level": "low",
        }


# ===================================================================
# Phase 2 — Insight Distiller (raw data → analytical insights)
# ===================================================================

_DISTILL_SYSTEM = """\
你是一位资深的数字营销分析师。以下是经过质量验证的多维度数据。

请将原始数据转化为**分析性发现**，遵循以下规则：

1. **关联分析**：找出跨维度的相关性
   - 例：页面加载速度 → SERP 排名 → 转化率 的连锁影响
   - 例：AI 引文出现频率 → GEO 评分 → 品牌权威度
   - 例：社区讨论热度 → Brand Presence 提升 → GEO 可见性

2. **趋势判断**：对比历史数据，给出趋势方向
   - 上升/下降/稳定 + 变化幅度 + 可能原因

3. **竞争定位**：如有竞品数据，进行相对定位
   - 在哪些维度领先/落后？差距多大？

4. **优先级排序**：按业务影响力排序发现
   - 每条发现标注 impact_level: critical/high/medium/low

输出 JSON 格式：
{
  "insights": [
    {
      "id": "INS-001",
      "title": "简短标题",
      "finding": "详细发现描述，包含具体数字...",
      "evidence": ["数据来源1", "数据来源2"],
      "impact_level": "critical/high/medium/low",
      "recommended_section": "建议放入报告的哪个章节"
    }
  ],
  "cross_cutting_themes": ["贯穿多个维度的主题1", "主题2"],
  "executive_summary_points": ["核心发现1（一句话）", "核心发现2"]
}

要求：至少产出 5 条 insights，涵盖 SEO/GEO/社区/品牌/竞品等多个维度。
必须返回合法 JSON，不要加 markdown 代码块。"""


async def _phase_distill(facts: dict, meta: dict, reflection: dict) -> dict:
    """Phase 2: Distill raw facts into analytical insights."""
    logger.info("[Pipeline Phase 2] Insight Distiller — extracting insights")
    user = (
        f"项目：{facts['project']['brand_name']} ({facts['project']['category']})\n"
        f"数据质量评分：{reflection.get('data_quality_score', '未知')}/100\n"
        f"置信度：{reflection.get('confidence_level', '未知')}\n"
        f"质量审计摘要：{reflection.get('validated_summary', '无')}\n"
        f"已识别问题：{_json_dump(reflection.get('issues', []))}\n\n"
        f"=== 验证后的完整数据 ===\n{_json_dump(facts)}"
    )
    try:
        result = await _llm_json_call(_DISTILL_SYSTEM, user)
        if not isinstance(result, dict):
            raise ValueError("Distiller did not return a dict")
        insights = result.get("insights", [])
        logger.info("[Pipeline Phase 2] Extracted %d insights", len(insights))
        return result
    except Exception as exc:
        logger.warning("[Pipeline Phase 2] Distill failed: %s", exc)
        raise


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

    # Gather only the insights relevant to this section
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
        # Ensure pass field is correctly set
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
# Phase 6 — Report Synthesizer (final assembly)
# ===================================================================

_SYNTHESIZE_SYSTEM = """\
你是一位资深的报告总编辑。以下是已通过评审的各章节内容。请完成最终合成。

你的任务：

1. **撰写执行摘要**（200-300字）：
   - 写在报告最前面
   - 3-5 句话概括最关键的发现和建议
   - 面向高管，30 秒内让人抓住核心
   - 用一个引人注目的数据点或判断作为开头

2. **撰写引言**（200-300字）：
   - 不要用"本报告旨在"这类废话
   - 快速建立上下文：我们是谁、面对什么市场环境、为什么现在需要关注

3. **撰写战略建议**（400-600字）：
   - 基于所有章节的发现，提出 3-5 条优先行动建议
   - 每条建议标注优先级(P0/P1/P2)和预期影响
   - 建议之间有逻辑关系（先做什么、后做什么）
   - 标明可由 Agent 自动执行的动作 vs 需要人工决策的动作

4. **统一编辑**：
   - 确保跨章节叙事流畅，没有重复或矛盾
   - 统一术语和数据引用格式
   - 添加必要的章节过渡语

输出完整的 Markdown 报告，包含：
# 报告标题
## 执行摘要
## 引言
## [各主体章节 — 直接使用已写好的内容，必要时微调过渡]
## 战略建议与行动路线图

输出纯 Markdown，不要代码块包裹。"""


async def _phase_synthesize(
    outline: dict,
    section_contents: list[tuple[dict, str]],
    distilled: dict,
    facts: dict,
) -> str:
    """Phase 6: Final synthesis — intro, conclusion, unified editing."""
    logger.info("[Pipeline Phase 6] Report Synthesizer — final assembly")
    sections_md = "\n\n---\n\n".join(
        f"### 章节：{sec.get('title', '?')}\n\n{content}"
        for sec, content in section_contents
    )
    user = (
        f"报告标题：{outline.get('report_title', '深度分析报告')}\n"
        f"叙事线索：{outline.get('narrative_arc', '无')}\n"
        f"核心发现要点：\n"
        + "\n".join(f"- {p}" for p in distilled.get("executive_summary_points", []))
        + f"\n\n贯穿主题：{', '.join(distilled.get('cross_cutting_themes', []))}\n\n"
        f"品牌：{facts['project']['brand_name']} ({facts['project']['category']})\n"
        f"网址：{facts['project']['url']}\n\n"
        f"=== 已通过评审的各章节内容 ===\n\n{sections_md}"
    )
    return await _llm_text_call(_SYNTHESIZE_SYSTEM, user)


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

    # ── Phase 1: Reflection ──
    reflection = await _phase_reflect(facts, meta)

    # ── Phase 2: Distill insights ──
    distilled = await _phase_distill(facts, meta, reflection)

    # ── Phase 3: Plan outline ──
    outline = await _phase_plan_outline(facts, distilled, reflection)

    # Build insight lookup map
    insights_list = distilled.get("insights", [])
    insights_map: dict[str, dict] = {ins["id"]: ins for ins in insights_list if "id" in ins}

    # Separate main sections from final sections (intro/conclusion)
    sections = outline.get("sections", [])
    main_sections = [s for s in sections if not s.get("is_final_section", False)]
    # final_sections are handled by the synthesizer

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
            logger.error(
                "[Pipeline] Section %d failed: %s — skipping",
                i, result,
            )
            continue
        completed_sections.append(result)

    if not completed_sections:
        raise RuntimeError("All section writers failed")

    # ── Phase 6: Synthesize ──
    final_report = await _phase_synthesize(outline, completed_sections, distilled, facts)

    logger.info(
        "=== Deep Report Pipeline COMPLETE — %d chars, %d sections ===",
        len(final_report), len(completed_sections),
    )
    return final_report

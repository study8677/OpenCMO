"""Tests for the multi-agent deep report pipeline."""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from opencmo import storage


@pytest.fixture(autouse=True)
def _db(tmp_path):
    db_path = tmp_path / "test.db"
    with patch.object(storage, "_DB_PATH", db_path):
        yield


def run(coro):
    return asyncio.run(coro)


async def _seed_project():
    project_id = await storage.ensure_project("TestBrand", "https://test.example", "saas")
    await storage.add_tracked_keyword(project_id, "test keyword")
    await storage.save_seo_scan(
        project_id, "https://test.example", "{}",
        score_performance=0.85, score_lcp=2100, score_cls=0.03, score_tbt=180,
        has_robots_txt=True, has_sitemap=True, has_schema_org=True,
    )
    await storage.save_geo_scan(
        project_id, 72,
        visibility_score=28, position_score=30, sentiment_score=14,
        platform_results_json='{"chatgpt": {"mentioned": true}}',
    )
    await storage.save_community_scan(project_id, 5, '{"hits": []}')
    await storage.save_serp_snapshot(project_id, "test keyword", 3, "https://test.example", "mock", None)
    return project_id


# ── Fixtures for mock LLM responses ──

MOCK_REFLECTION = json.dumps({
    "data_quality_score": 78,
    "issues": ["GEO 样本偏少"],
    "anomalies": [],
    "cross_validation_notes": ["SEO 与 SERP 数据一致"],
    "validated_summary": "数据质量中等偏上。",
    "confidence_level": "medium",
})

MOCK_DISTILLED = json.dumps({
    "insights": [
        {
            "id": "INS-001",
            "title": "SEO 基础稳健",
            "finding": "SEO 得分 85%，SERP 排名 #3，两者一致。",
            "evidence": ["seo_audit", "serp_tracking"],
            "impact_level": "high",
            "recommended_section": "技术健康度",
        },
        {
            "id": "INS-002",
            "title": "GEO 可见性待提升",
            "finding": "GEO 评分 72/100，AI 平台认知初步建立。",
            "evidence": ["geo_scan"],
            "impact_level": "medium",
            "recommended_section": "AI 可见性",
        },
        {
            "id": "INS-003",
            "title": "社区讨论稳定",
            "finding": "社区命中数 5 条，舆情平稳。",
            "evidence": ["community_scan"],
            "impact_level": "low",
            "recommended_section": "社区分析",
        },
        {
            "id": "INS-004",
            "title": "搜索排名领先",
            "finding": "核心关键词排名 #3。",
            "evidence": ["serp_tracking"],
            "impact_level": "high",
            "recommended_section": "竞争定位",
        },
        {
            "id": "INS-005",
            "title": "品牌基础已建立",
            "finding": "品牌在多个维度有存在感。",
            "evidence": ["brand_presence"],
            "impact_level": "medium",
            "recommended_section": "品牌分析",
        },
    ],
    "cross_cutting_themes": ["技术实力与市场认知的匹配度"],
    "executive_summary_points": ["SEO 体质良好", "GEO 需加速"],
})

MOCK_OUTLINE = json.dumps({
    "report_title": "TestBrand 深度战略分析",
    "executive_summary_thesis": "技术基础稳健但 AI 可见性仍有提升空间",
    "sections": [
        {
            "id": "sec-1",
            "title": "技术健康度与搜索表现",
            "thesis": "SEO 基础稳健，但需注意长期维护",
            "insight_ids": ["INS-001", "INS-004"],
            "word_budget": 600,
            "is_final_section": False,
            "writing_guidance": "以数据趋势开头",
        },
        {
            "id": "sec-2",
            "title": "AI 可见性与品牌定位",
            "thesis": "GEO 分数已具基础但提升空间大",
            "insight_ids": ["INS-002", "INS-005"],
            "word_budget": 500,
            "is_final_section": False,
            "writing_guidance": "强调 AI 搜索的重要性趋势",
        },
    ],
    "narrative_arc": "从技术基础 → AI 定位 → 行动路线图",
})

MOCK_SECTION_1 = "## 技术健康度与搜索表现\n\nSEO 基础分 85% 表现出色..."
MOCK_SECTION_2 = "## AI 可见性与品牌定位\n\nGEO 评分 72/100 意味着..."

MOCK_GRADE_PASS = json.dumps({
    "scores": {"clarity": 4, "depth": 4, "originality": 4, "coherence": 4, "actionability": 4},
    "average_score": 4.0,
    "pass": True,
    "revision_instructions": "",
    "specific_fixes": [],
})

MOCK_GRADE_FAIL = json.dumps({
    "scores": {"clarity": 3, "depth": 2, "originality": 3, "coherence": 3, "actionability": 3},
    "average_score": 2.8,
    "pass": False,
    "revision_instructions": "数据深度不足，需要更多具体数字。",
    "specific_fixes": ["第二段缺少数据支撑", "缺少竞品对比"],
})

MOCK_REVISED_SECTION = "## 技术健康度与搜索表现\n\nSEO 基础分 85%（竞品平均 72%）..."

MOCK_FINAL_REPORT = """# TestBrand 深度战略分析

## 执行摘要

TestBrand 的 SEO 基础分达 85%，搜索健康度位于行业前列...

## 引言

在 AI 搜索日益重要的今天...

## 技术健康度与搜索表现

SEO 基础分 85% 表现出色...

## AI 可见性与品牌定位

GEO 评分 72/100 意味着...

## 战略建议与行动路线图

1. **P0: 提升 AI 引文可信度**...
2. **P1: 扩展社区影响**...
"""


@pytest.mark.asyncio
async def test_pipeline_phases_called_in_order():
    """Verify that all 6 phases run in the correct sequence."""
    project_id = await _seed_project()

    from opencmo.reports import _build_strategic_facts

    facts, meta = await _build_strategic_facts(project_id)

    call_order = []

    async def mock_text_call(system, user):
        if "总编辑" in system:
            call_order.append("synthesize")
            return MOCK_FINAL_REPORT
        if "撰稿人" in system:
            call_order.append("write")
            if "修订" in system or "审稿人" in system:
                call_order[-1] = "revise"
                return MOCK_REVISED_SECTION
            return MOCK_SECTION_1 if "sec-1" in user else MOCK_SECTION_2
        return ""

    async def mock_json_call(system, user):
        if "质检" in system:
            call_order.append("reflect")
            return json.loads(MOCK_REFLECTION)
        if "分析师" in system or "营销分析" in system:
            call_order.append("distill")
            return json.loads(MOCK_DISTILLED)
        if "主编" in system:
            call_order.append("plan")
            return json.loads(MOCK_OUTLINE)
        if "审稿人" in system:
            call_order.append("grade")
            return json.loads(MOCK_GRADE_PASS)
        return {}

    with patch("opencmo.report_pipeline._llm_text_call", side_effect=mock_text_call), \
         patch("opencmo.report_pipeline._llm_json_call", side_effect=mock_json_call):
        from opencmo.report_pipeline import run_deep_report_pipeline

        result = await run_deep_report_pipeline(facts, meta, False, kind="strategic")

    # Check ordering: reflect → distill → plan → write(s) → grade(s) → synthesize
    assert call_order[0] == "reflect"
    assert call_order[1] == "distill"
    assert call_order[2] == "plan"
    assert "write" in call_order
    assert "grade" in call_order
    assert call_order[-1] == "synthesize"
    assert "TestBrand" in result


@pytest.mark.asyncio
async def test_pipeline_grader_retries_on_failure():
    """Verify the grader retry loop works correctly."""
    project_id = await _seed_project()

    from opencmo.reports import _build_strategic_facts

    facts, meta = await _build_strategic_facts(project_id)

    write_count = 0
    grade_count = 0

    async def mock_text_call(system, user):
        nonlocal write_count
        if "总编辑" in system:
            return MOCK_FINAL_REPORT
        if "修订" in system or "审稿人对你" in system:
            write_count += 1
            return MOCK_REVISED_SECTION
        write_count += 1
        return MOCK_SECTION_1

    async def mock_json_call(system, user):
        nonlocal grade_count
        if "质检" in system:
            return json.loads(MOCK_REFLECTION)
        if "分析师" in system or "营销分析" in system:
            return json.loads(MOCK_DISTILLED)
        if "主编" in system:
            # Only 1 section to simplify tracking
            outline = json.loads(MOCK_OUTLINE)
            outline["sections"] = [outline["sections"][0]]
            return outline
        if "审稿人" in system:
            grade_count += 1
            # First call fails, second passes
            if grade_count == 1:
                return json.loads(MOCK_GRADE_FAIL)
            return json.loads(MOCK_GRADE_PASS)
        return {}

    with patch("opencmo.report_pipeline._llm_text_call", side_effect=mock_text_call), \
         patch("opencmo.report_pipeline._llm_json_call", side_effect=mock_json_call):
        from opencmo.report_pipeline import run_deep_report_pipeline

        result = await run_deep_report_pipeline(facts, meta, False)

    # Should have graded twice (fail then pass) and written once + revised once
    assert grade_count == 2
    assert write_count >= 2  # original write + revision
    assert "TestBrand" in result


@pytest.mark.asyncio
async def test_pipeline_fallback_on_error():
    """Verify that pipeline failure falls back to single-call in reports.py."""
    project_id = await _seed_project()

    with patch("opencmo.report_pipeline.run_deep_report_pipeline", new_callable=AsyncMock) as mock_pipeline, \
         patch("opencmo.reports._generate_llm_markdown", new_callable=AsyncMock) as mock_llm:
        # Pipeline fails
        mock_pipeline.side_effect = RuntimeError("Pipeline exploded")
        # Single-call works for both human and agent
        mock_llm.side_effect = [
            "# Fallback Human Report\n\n## 优势\n- 好",
            "# Agent Brief\n\n- objective: test",
        ]

        from opencmo import service

        result = await service.regenerate_project_report(project_id, "strategic")

    assert result["kind"] == "strategic"
    assert result["human"]["meta"]["used_pipeline"] is False
    assert result["human"]["meta"]["used_fallback"] is False  # single-call succeeded
    assert "Fallback Human" in result["human"]["content"]
    assert result["agent"]["meta"]["used_pipeline"] is False


@pytest.mark.asyncio
async def test_pipeline_full_fallback_to_template():
    """Verify that if both pipeline AND single-call fail, template is used."""
    project_id = await _seed_project()

    with patch("opencmo.report_pipeline.run_deep_report_pipeline", new_callable=AsyncMock) as mock_pipeline, \
         patch("opencmo.reports._generate_llm_markdown", new_callable=AsyncMock) as mock_llm:
        # Everything fails
        mock_pipeline.side_effect = RuntimeError("Pipeline exploded")
        mock_llm.side_effect = RuntimeError("LLM is down")

        from opencmo import service

        result = await service.regenerate_project_report(project_id, "strategic")

    assert result["kind"] == "strategic"
    assert result["human"]["meta"]["used_fallback"] is True
    assert result["human"]["meta"]["used_pipeline"] is False
    assert "AI CMO 战略报告" in result["human"]["content"]  # fallback template


@pytest.mark.asyncio
async def test_agent_brief_skips_pipeline():
    """Agent audience should NOT use the pipeline."""
    project_id = await _seed_project()

    with patch("opencmo.report_pipeline.run_deep_report_pipeline", new_callable=AsyncMock) as mock_pipeline, \
         patch("opencmo.reports._generate_llm_markdown", new_callable=AsyncMock) as mock_llm:
        # Pipeline handles human report
        mock_pipeline.return_value = "# Pipeline Human\n\n## Section\n- pipeline content"
        # Single-call handles agent brief
        mock_llm.return_value = "# Agent Brief\n\n- objective: test"

        from opencmo import service

        result = await service.regenerate_project_report(project_id, "strategic")

    # Pipeline should be called once for human
    assert mock_pipeline.await_count == 1
    # Single-call should be called once for agent
    assert mock_llm.await_count == 1
    assert "Pipeline Human" in result["human"]["content"]
    assert result["human"]["meta"]["used_pipeline"] is True
    assert "Agent Brief" in result["agent"]["content"]
    assert result["agent"]["meta"]["used_pipeline"] is False

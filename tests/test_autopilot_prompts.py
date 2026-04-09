"""Regression tests for autopilot prompt quality."""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_autopilot_uses_expert_grade_prompt_contract_for_blog():
    from opencmo.autopilot import _build_generation_agent

    agent = await _build_generation_agent("blog_expert")

    assert agent.name == "Blog SEO Expert"
    assert "Facts over fluent invention" in agent.instructions
    assert "Only make claims that can be supported" in agent.instructions
    assert "The default sequence is: thesis, evidence, takeaway, next move" in agent.instructions


@pytest.mark.asyncio
async def test_autopilot_applies_brand_overlay_without_losing_truth_rules():
    from opencmo.autopilot import _build_generation_agent

    with patch(
        "opencmo.storage.brand_kit.build_brand_kit_prompt",
        AsyncMock(return_value="## Brand Overlay\n- This overlay is lower priority than truth, evidence, and channel-native rules.\n- Tone: calm"),
    ):
        agent = await _build_generation_agent("blog_expert", project_id=42)

    assert "## Brand Overlay" in agent.instructions
    assert "Facts over fluent invention" in agent.instructions
    assert agent.instructions.index("## Truth Contract") < agent.instructions.index("## Brand Overlay")

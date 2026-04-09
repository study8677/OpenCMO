"""Shared marketing prompt building blocks for growth-oriented agents."""

from __future__ import annotations

from opencmo.agents import prompt_contracts as _prompt_contracts

build_prompt = _prompt_contracts.build_prompt
MARKETING_DECISION_FRAMEWORK = _prompt_contracts.MARKETING_DECISION_FRAMEWORK
MARKETING_OUTPUT_REQUIREMENTS = _prompt_contracts.MARKETING_OUTPUT_REQUIREMENTS
MARKETING_WRITING_RULES = _prompt_contracts.ANTI_SLOP_GUARDRAILS


def marketing_prompt(base_instructions: str) -> str:
    """Append shared marketing guardrails to agent-specific instructions."""
    return build_prompt(
        base_instructions=base_instructions,
    )

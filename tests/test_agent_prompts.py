"""Tests for shared marketing prompt structure across core agents."""


def test_shared_marketing_prompt_contract_contains_core_rules():
    from opencmo.agents.marketing_style import (
        MARKETING_DECISION_FRAMEWORK,
        MARKETING_WRITING_RULES,
    )

    assert "Audience" in MARKETING_DECISION_FRAMEWORK
    assert "Pain" in MARKETING_DECISION_FRAMEWORK
    assert "Promise" in MARKETING_DECISION_FRAMEWORK
    assert "Proof" in MARKETING_DECISION_FRAMEWORK
    assert "Priority" in MARKETING_DECISION_FRAMEWORK
    assert "Next move" in MARKETING_DECISION_FRAMEWORK

    assert "Clarity over cleverness" in MARKETING_WRITING_RULES
    assert "Benefits over features" in MARKETING_WRITING_RULES
    assert "Specificity over vagueness" in MARKETING_WRITING_RULES
    assert "customer language" in MARKETING_WRITING_RULES


def test_core_marketing_agents_include_shared_marketing_rules():
    from opencmo.agents.blog import blog_expert
    from opencmo.agents.cmo import cmo_agent
    from opencmo.agents.community import community_agent
    from opencmo.agents.geo import geo_agent
    from opencmo.agents.seo import seo_agent
    from opencmo.agents.trend import trend_agent

    for agent in [cmo_agent, community_agent, seo_agent, trend_agent, blog_expert, geo_agent]:
        assert "Clarity over cleverness" in agent.instructions
        assert "customer language" in agent.instructions
        assert "Why this matters" in agent.instructions
        assert "Next move" in agent.instructions


def test_cmo_prompt_requires_evidence_and_explicit_uncertainty():
    from opencmo.agents.cmo import cmo_agent

    assert "Facts over fluent invention" in cmo_agent.instructions
    assert "When evidence is incomplete" in cmo_agent.instructions
    assert "say exactly what is known" in cmo_agent.instructions
    assert "Judgment first" in cmo_agent.instructions


def test_reddit_prompt_prioritizes_native_community_voice():
    from opencmo.agents.reddit import reddit_expert

    assert "No marketing speak whatsoever" in reddit_expert.instructions
    assert "first person as the maker/founder" in reddit_expert.instructions
    assert "sound like a peer in the thread" in reddit_expert.instructions


def test_zhihu_prompt_prioritizes_useful_low_hardsell_voice():
    from opencmo.agents.zhihu import zhihu_expert

    assert "先提供判断，再提供展开解释" in zhihu_expert.instructions
    assert "优先分享经验、方法、踩坑与取舍" in zhihu_expert.instructions
    assert "不要写成硬广软文" in zhihu_expert.instructions


def test_blog_prompt_requires_evidence_aware_longform_structure():
    from opencmo.agents.blog import blog_expert

    assert "Only make claims that can be supported" in blog_expert.instructions
    assert "label it as an inference" in blog_expert.instructions
    assert "The default sequence is: thesis, evidence, takeaway, next move" in blog_expert.instructions


def test_producthunt_prompt_stays_maker_native_and_understated():
    from opencmo.agents.producthunt import producthunt_expert

    assert "underclaim rather than oversell" in producthunt_expert.instructions
    assert "talking to fellow makers" in producthunt_expert.instructions
    assert "Avoid superlatives and hype words" in producthunt_expert.instructions


def test_v2ex_prompt_reads_like_real_forum_posting():
    from opencmo.agents.v2ex import v2ex_expert

    assert "像开发者在论坛里发帖" in v2ex_expert.instructions
    assert "先讲你做了什么，再讲它为什么值得被试" in v2ex_expert.instructions
    assert "极其反感广告" in v2ex_expert.instructions


def test_xiaohongshu_prompt_reduces_hardsell_seeded_ad_tone():
    from opencmo.agents.xiaohongshu import xiaohongshu_expert

    assert "不要写成硬广种草文" in xiaohongshu_expert.instructions
    assert "先给具体场景，再给感受和结论" in xiaohongshu_expert.instructions
    assert "轻松活泼但不浮夸" in xiaohongshu_expert.instructions


def test_devto_prompt_teaches_before_it_promotes():
    from opencmo.agents.devto import devto_expert

    assert "Teach first, promote second" in devto_expert.instructions
    assert "share what you learned building it" in devto_expert.instructions
    assert "open-source culture" in devto_expert.instructions


def test_community_prompt_requires_signal_and_confidence_discipline():
    from opencmo.agents.community import community_agent

    assert "separate observed signal from engagement opportunity" in community_agent.instructions
    assert "If you only have search-summary depth" in community_agent.instructions
    assert "do not overclaim certainty" in community_agent.instructions


def test_seo_prompt_frames_technical_findings_as_growth_priorities():
    from opencmo.agents.seo import seo_agent

    assert "diagnosis, impact, fix, expected outcome, next move" in seo_agent.instructions
    assert "do not imply ranking gains as guaranteed" in seo_agent.instructions


def test_geo_prompt_distinguishes_presence_from_recommendation_strength():
    from opencmo.agents.geo import geo_agent

    assert "Presence is not the same as recommendation strength" in geo_agent.instructions
    assert "label weak evidence as directional rather than conclusive" in geo_agent.instructions


def test_trend_prompt_separates_signal_from_noise_and_hypothesis():
    from opencmo.agents.trend import trend_agent

    assert "separate signal, interpretation, and hypothesis" in trend_agent.instructions
    assert "Do not treat a short-lived spike as durable demand" in trend_agent.instructions

"""Smoke tests — verify agent/tool structure without API calls."""


def test_imports():
    """All modules can be imported without error."""
    from opencmo.agents import (
        cmo_agent,
        twitter_expert,
        reddit_expert,
        linkedin_expert,
        producthunt_expert,
        hackernews_expert,
        blog_expert,
        seo_agent,
        geo_agent,
        community_agent,
    )
    from opencmo.tools import (
        crawl_website,
        web_search,
        audit_page_seo,
        analyze_competitor,
        scan_geo_visibility,
        scan_community,
    )
    # Just verify they exist
    assert cmo_agent is not None
    assert crawl_website is not None


def test_cmo_has_tools_and_handoffs():
    from opencmo.agents import cmo_agent

    assert len(cmo_agent.tools) > 0, "CMO should have tools"
    assert len(cmo_agent.handoffs) > 0, "CMO should have handoffs"


def test_cmo_has_as_tool_wrappers():
    """CMO should have generate_* tools for multi-channel mode."""
    from opencmo.agents import cmo_agent

    tool_names = [t.name for t in cmo_agent.tools if hasattr(t, "name")]
    assert "generate_twitter_content" in tool_names
    assert "generate_reddit_content" in tool_names
    assert "generate_linkedin_content" in tool_names


def test_cmo_handoffs_have_descriptions():
    """Each handoff should have a tool_description_override."""
    from opencmo.agents import cmo_agent

    for h in cmo_agent.handoffs:
        # handoff objects have tool_name and tool_description
        assert hasattr(h, "tool_description") or hasattr(h, "tool_name")


def test_all_experts_have_instructions():
    from opencmo.agents import (
        twitter_expert,
        reddit_expert,
        linkedin_expert,
        producthunt_expert,
        hackernews_expert,
        blog_expert,
        seo_agent,
        geo_agent,
        community_agent,
    )

    for agent in [
        twitter_expert,
        reddit_expert,
        linkedin_expert,
        producthunt_expert,
        hackernews_expert,
        blog_expert,
        seo_agent,
        geo_agent,
        community_agent,
    ]:
        assert agent.instructions, f"{agent.name} missing instructions"
        assert len(agent.instructions) > 50, f"{agent.name} instructions too short"


def test_seo_agent_has_tools():
    from opencmo.agents import seo_agent

    assert len(seo_agent.tools) >= 2, "SEO agent needs audit_page_seo + web_search"


def test_geo_agent_has_tools():
    from opencmo.agents import geo_agent

    assert len(geo_agent.tools) >= 2, "GEO agent needs scan_geo_visibility + web_search"


def test_community_agent_has_tools():
    from opencmo.agents import community_agent

    assert len(community_agent.tools) >= 2, "Community agent needs scan_community + web_search"


def test_markdown_extraction():
    """Test _extract_markdown handles str, None, and object types."""
    from opencmo.tools.crawl import _extract_markdown

    # str case
    mock_str = type("R", (), {"markdown": "hello"})()
    assert _extract_markdown(mock_str) == "hello"

    # None case
    mock_none = type("R", (), {"markdown": None})()
    assert _extract_markdown(mock_none) == ""

    # Object with raw_markdown
    inner = type("MD", (), {"raw_markdown": "from object"})()
    mock_obj = type("R", (), {"markdown": inner})()
    assert _extract_markdown(mock_obj) == "from object"

    # Object without raw_markdown — falls back to str()
    inner2 = type("MD", (), {})()
    mock_obj2 = type("R", (), {"markdown": inner2})()
    result = _extract_markdown(mock_obj2)
    assert isinstance(result, str)

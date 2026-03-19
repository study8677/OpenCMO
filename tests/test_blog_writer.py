"""Tests for blog writer — research tool + agent structure."""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_research_topic():
    """research_blog_topic returns structured JSON with competing articles."""
    from opencmo.tools.blog_writer import _research_topic_impl

    # Mock httpx search
    mock_resp = MagicMock()
    mock_resp.text = '''
    <a href="/url?q=https://blog.example.com/article1">Article 1</a>
    <a href="/url?q=https://blog.example.com/article2">Article 2</a>
    '''
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    # Mock crawl4ai
    mock_crawler = AsyncMock()
    mock_crawl_result = MagicMock()
    mock_crawl_result.markdown = "# Test Article\n\n## Section 1\nSome content here with 50% improvement\n\n## Section 2\nMore content"
    mock_crawler.arun = AsyncMock(return_value=mock_crawl_result)
    mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
    mock_crawler.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_client), \
         patch("crawl4ai.AsyncWebCrawler", return_value=mock_crawler):
        result = await _research_topic_impl("web scraping tools", "web scraping,python")

    data = json.loads(result)
    assert "competing_articles" in data
    assert "data_points" in data
    assert data["topic"] == "web scraping tools"
    assert len(data["keywords"]) == 2


@pytest.mark.asyncio
async def test_research_crawl_failure():
    """Partial crawl failure still returns valid data."""
    from opencmo.tools.blog_writer import _research_topic_impl

    mock_resp = MagicMock()
    mock_resp.text = '<a href="/url?q=https://example.com/a">A</a>'
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    # Crawl fails
    mock_crawler = AsyncMock()
    mock_crawler.arun = AsyncMock(side_effect=Exception("Crawl timeout"))
    mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
    mock_crawler.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_client), \
         patch("crawl4ai.AsyncWebCrawler", return_value=mock_crawler):
        result = await _research_topic_impl("test topic", "kw1")

    data = json.loads(result)
    assert "competing_articles" in data
    assert data["search_urls_found"] >= 0


def test_blog_expert_has_tools():
    """Blog expert should have research + search + crawl tools."""
    from opencmo.agents.blog import blog_expert

    tool_names = [t.name for t in blog_expert.tools if hasattr(t, "name")]
    assert "research_blog_topic" in tool_names
    assert "web_search" in tool_names
    assert "crawl_website" in tool_names


def test_blog_expert_instructions_mention_full_article():
    """Blog expert instructions should mention full article mode."""
    from opencmo.agents.blog import blog_expert

    assert "Full Article" in blog_expert.instructions
    assert "2000" in blog_expert.instructions

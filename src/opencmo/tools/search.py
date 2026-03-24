"""Web search tool — uses OpenAI WebSearchTool when available, falls back to crawl-based search."""

from opencmo.config import is_custom_provider

if not is_custom_provider():
    # OpenAI native — use built-in WebSearchTool (Responses API)
    from agents import WebSearchTool

    web_search = WebSearchTool()
else:
    # Custom provider (NVIDIA, DeepSeek, etc.) — WebSearchTool not available.
    # Prefer Tavily when TAVILY_API_KEY is set; otherwise fall back to crawl4ai Google search.
    import os
    from agents import function_tool

    if os.environ.get("TAVILY_API_KEY"):

        @function_tool
        async def web_search(query: str) -> str:
            """Search the web for real-time information.

            Args:
                query: The search query string.
            """
            try:
                from tavily import TavilyClient

                client = TavilyClient()
                response = client.search(query=query, max_results=5, search_depth="basic")
                results = response.get("results", [])
                if not results:
                    return "No search results found."
                parts = []
                for r in results:
                    title = r.get("title", "")
                    url = r.get("url", "")
                    content = r.get("content", "")
                    parts.append(f"### {title}\n{url}\n\n{content}")
                return "\n\n---\n\n".join(parts)
            except Exception as e:
                return f"Web search failed: {e}. Try using other available tools instead."

    else:

        @function_tool
        async def web_search(query: str) -> str:
            """Search the web for real-time information.

            Args:
                query: The search query string.
            """
            try:
                from crawl4ai import AsyncWebCrawler
                from opencmo.tools.crawl import _extract_markdown

                url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num=5"
                async with AsyncWebCrawler() as crawler:
                    result = await crawler.arun(url=url)
                content = _extract_markdown(result)
                return content[:4000] if content else "No search results found."
            except Exception as e:
                return f"Web search failed: {e}. Try using other available tools instead."

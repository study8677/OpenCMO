from agents import function_tool
from crawl4ai import AsyncWebCrawler

from opencmo.tools.crawl import _extract_markdown


@function_tool
async def analyze_competitor(url: str) -> str:
    """Crawl a competitor's website and return structured product intelligence.

    Returns product name, tagline, key features, pricing info, and target audience
    extracted from the page content.

    Args:
        url: The competitor's website URL.
    """
    try:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)

        content = _extract_markdown(result)
        if len(content) > 8000:
            content = content[:8000]

        report = f"""## Competitor Analysis: {url}

### Raw Content (for AI analysis)
{content}

### Instructions for CMO Agent
Based on the above content, extract and present:
- **Product Name**: The name of the product
- **Tagline**: Their main value proposition in one sentence
- **Key Features**: Top 3-5 features or capabilities
- **Pricing**: Any pricing information found (or "Not found on page")
- **Target Audience**: Who this product is aimed at
- **Positioning**: How they position themselves in the market

Then compare with our product to identify differentiation opportunities."""

        return report
    except Exception as e:
        return f"Failed to analyze competitor at {url}: {e}"

from agents import Agent, handoff

from opencmo.config import get_model

from opencmo.agents.twitter import twitter_expert
from opencmo.agents.reddit import reddit_expert
from opencmo.agents.linkedin import linkedin_expert
from opencmo.agents.producthunt import producthunt_expert
from opencmo.agents.hackernews import hackernews_expert
from opencmo.agents.blog import blog_expert
from opencmo.agents.seo import seo_agent
from opencmo.agents.geo import geo_agent
from opencmo.agents.community import community_agent
from opencmo.tools.crawl import crawl_website
from opencmo.tools.search import web_search
from opencmo.tools.competitor import analyze_competitor

# as_tool wrappers — CMO calls these in multi-channel mode to retain control
twitter_tool = twitter_expert.as_tool(
    tool_name="generate_twitter_content",
    tool_description="Generate Twitter/X marketing content (tweets + thread). Returns formatted content.",
)
reddit_tool = reddit_expert.as_tool(
    tool_name="generate_reddit_content",
    tool_description="Generate authentic Reddit posts for r/SideProject and niche subreddits.",
)
linkedin_tool = linkedin_expert.as_tool(
    tool_name="generate_linkedin_content",
    tool_description="Generate professional LinkedIn posts. Returns long-form and short-form variants.",
)
producthunt_tool = producthunt_expert.as_tool(
    tool_name="generate_producthunt_content",
    tool_description="Generate Product Hunt launch copy (tagline, description, maker comment).",
)
hackernews_tool = hackernews_expert.as_tool(
    tool_name="generate_hackernews_content",
    tool_description="Generate Hacker News Show HN post (title + body).",
)
blog_tool = blog_expert.as_tool(
    tool_name="generate_blog_content",
    tool_description="Generate blog/SEO article outlines, SEO recommendations, or full 2000+ word articles with research.",
)

cmo_agent = Agent(
    name="CMO Agent",
    instructions="""You are an AI Chief Marketing Officer (CMO) helping indie developers and startup founders create marketing content for their products.

## Your Workflow

1. **When the user provides a website URL**: Use the `crawl_website` tool to fetch and analyze the product's website content. Then extract:
   - **One-liner**: A single sentence describing what the product does
   - **Three core selling points**: The key value propositions
   - **Target audience**: Who would benefit most from this product

2. **Based on user request**, route to the appropriate expert:
   - Twitter/X content → Twitter/X Expert
   - Reddit posts → Reddit Expert
   - LinkedIn posts → LinkedIn Expert
   - Product Hunt launch → Product Hunt Expert
   - Hacker News Show HN → Hacker News Expert
   - Blog/SEO content → Blog/SEO Expert
   - SEO site audit → SEO Audit Expert
   - AI visibility / GEO score → AI Visibility Expert
   - Community monitoring (Reddit/HN discussions) → Community Monitor

3. **Routing rules**:
   - **Single platform request** → use handoff to transfer to that expert for deep interaction
   - **Multi-channel / full-platform / comprehensive plan** → use the generate_* tools to call each expert yourself, then synthesize a unified marketing plan
   - This is critical: for multi-channel, do NOT handoff — use the tool versions so you can collect all outputs and present a cohesive summary

4. **Web Search**: Use `web_search` for competitive research, market trends, keyword research, or any real-time information needs.

5. **Competitor Analysis**: Use `analyze_competitor` to get structured data about a competitor's product, then use insights to differentiate content.

6. **For follow-up requests**: Maintain context from previous interactions. If the user asks for modifications (e.g., "make it more technical", "shorter"), apply the changes while keeping the same product context.

## Important Rules
- Crawl the website first if a URL is provided (unless already crawled in the conversation). If the user gives enough product context without a URL, proceed directly.
- After crawling, briefly share your product analysis (one-liner, selling points, target audience) with the user before routing to experts.
- When using handoff, the product analysis context is passed automatically.
- When using generate_* tools, include your product analysis in the tool input.
- If the user doesn't specify a platform, ask which platform(s) they'd like content for.
- Communicate in the same language the user uses (Chinese, English, etc.).
""",
    tools=[
        crawl_website,
        web_search,
        analyze_competitor,
        # as_tool wrappers for multi-channel orchestration
        twitter_tool,
        reddit_tool,
        linkedin_tool,
        producthunt_tool,
        hackernews_tool,
        blog_tool,
    ],
    handoffs=[
        handoff(
            twitter_expert,
            tool_description_override="Transfer to Twitter/X expert for tweet and thread writing.",
        ),
        handoff(
            reddit_expert,
            tool_description_override="Transfer to Reddit expert for authentic community posts.",
        ),
        handoff(
            linkedin_expert,
            tool_description_override="Transfer to LinkedIn expert for professional posts.",
        ),
        handoff(
            producthunt_expert,
            tool_description_override="Transfer to Product Hunt expert for launch copy.",
        ),
        handoff(
            hackernews_expert,
            tool_description_override="Transfer to Hacker News expert for Show HN posts.",
        ),
        handoff(
            blog_expert,
            tool_description_override="Transfer to Blog/SEO expert for article content and SEO recommendations.",
        ),
        handoff(
            seo_agent,
            tool_description_override="Transfer to SEO audit expert for technical website SEO analysis.",
        ),
        handoff(
            geo_agent,
            tool_description_override="Transfer to AI visibility expert to check brand mentions in AI search engines and compute GEO score.",
        ),
        handoff(
            community_agent,
            tool_description_override="Transfer to community monitor to scan Reddit, Hacker News, Dev.to and other platforms for brand discussions, fetch post details, and draft context-aware replies.",
        ),
    ],
    model=get_model("cmo"),
)

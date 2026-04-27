"""FastAPI web dashboard for OpenCMO — Jinja2 SSR + REST API + SPA mount.

This module creates the ``app`` instance, registers auth middleware,
includes all domain routers, and provides the SPA catch-all route and
server entry point.
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from html import escape
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import StreamingResponse

from opencmo import storage

_HERE = Path(__file__).parent
_SPA_DIR = _HERE.parent.parent.parent / "frontend" / "dist"  # <repo>/frontend/dist

app = FastAPI(title="OpenCMO Dashboard")
app.mount("/static", StaticFiles(directory=str(_HERE / "static")), name="static")
logger = logging.getLogger(__name__)

_SEO_PUBLIC_LOCALES = ("en", "zh")
_HREFLANG_BY_LOCALE = {
    "en": "en",
    "zh": "zh-CN",
}

_HOME_STATIC_SITE_COPY_BY_LOCALE = {
    "en": """
<main id="static-site-copy">
  <header>
    <p>aidCMO</p>
    <h1>Overseas B2B lead data and SEO/GEO growth services</h1>
    <p>
      aidCMO helps exporters, SaaS teams, manufacturers, and service companies
      find target overseas B2B customers by country, industry, role, and company
      type, then improves acquisition efficiency through SEO and GEO AI search
      visibility work.
    </p>
  </header>
  <section>
    <h2>Commercial services</h2>
    <ul>
      <li>Overseas B2B email leads filtered by country, region, industry, role, company size, website, and company domain.</li>
      <li>Email verification, deduplication, invalid-email cleanup, domain matching, risky-mailbox labels, and bounce-risk grading.</li>
      <li>SEO services for technical checks, keywords, landing pages, comparison pages, and overseas acquisition content.</li>
      <li>GEO and AI search visibility optimization for brand entity, citations, assistant summaries, competitors, and SERP analysis.</li>
    </ul>
  </section>
  <section>
    <h2>OpenCMO technical support</h2>
    <p>
      OpenCMO remains the open-source growth system behind the method. It analyzes
      SEO, GEO, SERP, community discussion, and AI visibility signals, and is kept
      as public proof of the operating approach.
    </p>
    <ul>
      <li>GitHub repository: https://github.com/study8677/OpenCMO</li>
      <li>License: Apache 2.0 — https://github.com/study8677/OpenCMO/blob/main/LICENSE</li>
      <li>Machine-readable summary: https://www.aidcmo.com/llms.txt</li>
    </ul>
  </section>
  <section>
    <h2>Data and compliance boundaries</h2>
    <p>
      aidCMO provides B2B commercial leads based on public business information,
      company websites, public directories, and public professional profiles. It
      does not support spam, fraud, phishing, illegal use, unlimited sending, or
      aggressive blast campaigns. Validation status, cleaning notes, and risk
      labels are used to keep data quality visible.
    </p>
    <ul>
      <li>B2B leads: https://www.aidcmo.com/en/b2b-leads</li>
      <li>SEO/GEO services: https://www.aidcmo.com/en/seo-geo</li>
      <li>Sample data request: https://www.aidcmo.com/en/sample-data</li>
      <li>Data policy: https://www.aidcmo.com/en/data-policy</li>
    </ul>
  </section>
</main>
""".strip(),
    "zh": """
<main id="static-site-copy">
  <header>
    <p>aidCMO</p>
    <h1>海外 B2B 线索数据与 SEO/GEO 增长服务</h1>
    <p>
      aidCMO 帮助外贸、SaaS、制造业和服务型企业按国家、行业、职位和公司类型
      找到目标海外客户，并通过搜索和 AI 可见度提升获客效率。
    </p>
  </header>
  <section>
    <h2>商业服务</h2>
    <ul>
      <li>海外 B2B 邮箱线索，可按国家、地区、行业、职位、公司规模、官网和企业域名筛选。</li>
      <li>邮箱验证、去重、无效邮箱清理、企业域名匹配、风险邮箱标记和退信风险分级。</li>
      <li>SEO 服务，覆盖技术检查、关键词、落地页、竞品对比页和海外获客内容。</li>
      <li>GEO / AI 搜索可见度优化，覆盖品牌实体、引用、AI 摘要、竞品和 SERP 分析。</li>
    </ul>
  </section>
  <section>
    <h2>OpenCMO 技术支持</h2>
    <p>
      OpenCMO 保留为背后的开源增长系统，用于分析 SEO、GEO、SERP、社区讨论和
      AI 可见度，并作为方法论的技术支持。
    </p>
    <ul>
      <li>GitHub 仓库: https://github.com/study8677/OpenCMO</li>
      <li>许可证: Apache 2.0 — https://github.com/study8677/OpenCMO/blob/main/LICENSE</li>
      <li>机器可读摘要: https://www.aidcmo.com/llms.txt</li>
    </ul>
  </section>
  <section>
    <h2>数据来源与合规边界</h2>
    <p>
      aidCMO 只提供 B2B 商业线索，数据来源于公开商业信息、企业官网、公开目录和
      公开职业资料等。不支持垃圾邮件、欺诈、钓鱼、违法用途、无限群发或轰炸式活动。
      通过验证状态、清洗说明和风险标签让数据质量保持可见。
    </p>
    <ul>
      <li>B2B 线索: https://www.aidcmo.com/zh/b2b-leads</li>
      <li>SEO/GEO 服务: https://www.aidcmo.com/zh/seo-geo</li>
      <li>样例数据申请: https://www.aidcmo.com/zh/sample-data</li>
      <li>数据合规说明: https://www.aidcmo.com/zh/data-policy</li>
    </ul>
  </section>
</main>
""".strip(),
}

_BLOG_STATIC_SITE_COPY_BY_LOCALE = {
    "en": """
<main id="static-site-copy">
  <header>
    <p>OpenCMO Blog</p>
    <h1>A public field guide to what OpenCMO is, how it fits the stack, and how teams should use it</h1>
    <p>
      The OpenCMO blog explains product fit, self-hosted adoption, architecture,
      comparisons with adjacent tools, and the technical choices that make the
      public site readable to both people and machines.
    </p>
  </header>
  <section>
    <h2>Start with these notes</h2>
    <ul>
      <li><a href="https://www.aidcmo.com/en/blog/opencmo-vs-mautic-posthog">OpenCMO vs Mautic and PostHog: which visibility problem each tool actually solves</a></li>
      <li><a href="https://www.aidcmo.com/en/blog/who-should-use-opencmo">Who should use OpenCMO, and when it starts paying for itself</a></li>
      <li><a href="https://www.aidcmo.com/en/blog/first-30-days-with-opencmo">Your first 30 days with OpenCMO: a practical rollout plan</a></li>
      <li><a href="https://www.aidcmo.com/en/blog/inside-opencmo-workspace">Inside OpenCMO: what the workspace actually contains</a></li>
      <li><a href="https://www.aidcmo.com/en/blog/what-is-a-cmo">What does a CMO do? Responsibilities, metrics, and why AI changes the role</a></li>
      <li><a href="https://www.aidcmo.com/en/blog/what-is-product-marketing">What is product marketing? Responsibilities, examples, and where it fits</a></li>
    </ul>
  </section>
  <section>
    <h2>Why this page exists</h2>
    <p>
      The blog is part of the public product surface. It gives buyers, operators,
      search engines, and AI agents long-form pages about positioning, adoption,
      and product comparisons without requiring the private workspace routes.
    </p>
  </section>
</main>
""".strip(),
    "zh": """
<main id="static-site-copy">
  <header>
    <p>OpenCMO Blog</p>
    <h1>一组公开文章：解释 OpenCMO 是什么、适合谁，以及它和相邻工具的边界</h1>
    <p>
      OpenCMO 的 blog 会持续解释适用场景、自部署落地、架构导览、
      和相邻工具的对比，以及这套站点为什么必须同时对人和机器可读。
    </p>
  </header>
  <section>
    <h2>先从这些文章开始</h2>
    <ul>
      <li><a href="https://www.aidcmo.com/zh/blog/opencmo-vs-mautic-posthog">OpenCMO vs Mautic vs PostHog：它们分别解决哪一层可见度问题</a></li>
      <li><a href="https://www.aidcmo.com/zh/blog/who-should-use-opencmo">谁应该用 OpenCMO，以及它从什么时候开始值得</a></li>
      <li><a href="https://www.aidcmo.com/zh/blog/first-30-days-with-opencmo">前 30 天怎么用 OpenCMO：一份可执行的上手路线</a></li>
      <li><a href="https://www.aidcmo.com/zh/blog/inside-opencmo-workspace">OpenCMO 里到底有什么：从监控、报告到增长执行的完整链路</a></li>
      <li><a href="https://www.aidcmo.com/zh/blog/what-is-a-cmo">CMO 是做什么的？职责、核心指标，以及 AI 为什么会改变这个角色</a></li>
      <li><a href="https://www.aidcmo.com/zh/blog/what-is-product-marketing">什么是产品营销？职责、典型工作，以及它到底放在哪一层</a></li>
    </ul>
  </section>
  <section>
    <h2>为什么这个页面需要公开存在</h2>
    <p>
      Blog 是公开产品 surface 的一部分。它帮助买家、操盘手、搜索引擎和 AI agent
      在不进入私有 workspace 的情况下，直接理解 OpenCMO 的定位、适用场景、
      对比对象和工作方式。
    </p>
  </section>
</main>
""".strip(),
}

_BLOG_ARTICLE_METADATA = [
    {
        "slug": "what-is-a-cmo",
        "path": "/blog/what-is-a-cmo",
        "title": "What does a CMO do? Responsibilities, metrics, and why AI changes the role",
        "title_zh": "CMO 是做什么的？职责、核心指标，以及 AI 为什么会改变这个角色",
        "summary": (
            "CMO is one of the most overloaded titles in a company. In some teams it means "
            "brand leadership. In others it also covers positioning, demand generation, "
            "growth systems, and market intelligence."
        ),
        "summary_zh": (
            "CMO 可能是公司里最容易被误解的职位之一。对有些团队它等于品牌负责人，"
            "对另一些团队它又同时覆盖定位、需求获取、增长系统和市场情报。"
        ),
        "thesis": (
            "The core CMO job is to connect market insight, brand narrative, demand creation, "
            "and organizational execution. AI changes the speed and surface area of that work, "
            "but not the need for judgment."
        ),
        "thesis_zh": "CMO 的核心工作，是把市场洞察、品牌叙事、需求创造和组织执行连起来。AI 改变的是速度和覆盖面，不会消灭判断本身。",
    },
    {
        "slug": "what-is-product-marketing",
        "path": "/blog/what-is-product-marketing",
        "title": "What is product marketing? Responsibilities, examples, and where it fits",
        "title_zh": "什么是产品营销？职责、典型工作，以及它到底放在哪一层",
        "summary": (
            "Product marketing usually gets confused with content, launch support, or sales "
            "enablement alone. In reality, the role connects customer insight, positioning, "
            "messaging, launch execution, and market feedback."
        ),
        "summary_zh": (
            "很多团队会把产品营销理解成写发布文案、做 launch 配合或给销售做材料，"
            "但真正的产品营销，是把客户洞察、定位、信息架构、发布执行和市场反馈接成一条线。"
        ),
        "thesis": (
            "Product marketing sits between product reality and market understanding. Its job "
            "is to make sure the right people understand why the product matters and how it is different."
        ),
        "thesis_zh": "产品营销站在“产品真实能力”和“市场实际理解”之间，它的任务是确保正确的人真正理解产品为什么重要、又为什么和别家不同。",
    },
    {
        "slug": "what-is-go-to-market-strategy",
        "path": "/blog/what-is-go-to-market-strategy",
        "title": "What is go-to-market strategy? GTM, marketing strategy, and execution explained",
        "title_zh": "什么是 Go-to-Market Strategy？GTM、营销战略和执行到底怎么区分",
        "summary": (
            "Go-to-market strategy is often reduced to a launch checklist. A real GTM strategy "
            "decides which customers matter, what promise the company will make, which channels "
            "carry that promise, and how teams turn that plan into repeatable revenue."
        ),
        "summary_zh": (
            "很多人把 GTM 理解成一张 launch 清单，但真正的 GTM 策略，是决定先服务谁、"
            "向市场承诺什么、通过哪些渠道交付这个承诺，以及团队如何把这套计划变成可重复收入。"
        ),
        "thesis": (
            "A GTM strategy is not a slide about launch day. It is the operating choice about "
            "who you serve first, how you frame the offer, and how the organization turns that framing into pipeline."
        ),
        "thesis_zh": "GTM 策略不是 launch 当天的幻灯片，而是关于“先服务谁、怎样 framing 这个 offer、组织如何把它变成 pipeline”的经营选择。",
    },
    {
        "slug": "what-is-brand-positioning",
        "path": "/blog/what-is-brand-positioning",
        "title": "What is brand positioning? How teams define the story the market remembers",
        "title_zh": "什么是品牌定位？团队如何定义市场真正记住的那句话",
        "summary": (
            "Brand positioning is not a slogan workshop. It is the decision about what role "
            "your company should play in a buyer's mind, which alternatives you are compared with, "
            "and which idea you want the market to associate with your name."
        ),
        "summary_zh": (
            "品牌定位不是一次 slogan workshop。它真正决定的是：你的公司在买家脑子里"
            "应该扮演什么角色、默认会被拿来和谁比较，以及市场最终想起你时会联想到哪一个概念。"
        ),
        "thesis": (
            "Brand positioning is the strategic choice of the narrative territory you want to own. "
            "Messaging, content, and campaigns only work cleanly when that choice is coherent."
        ),
        "thesis_zh": "品牌定位是你选择想占据哪块叙事领地。只有这个选择清楚了，后面的 messaging、内容和 campaign 才会变得干净。",
    },
    {
        "slug": "demand-generation-vs-lead-generation",
        "path": "/blog/demand-generation-vs-lead-generation",
        "title": "Demand generation vs lead generation: what B2B teams should actually optimize",
        "title_zh": "Demand Generation 和 Lead Generation 有什么区别？B2B 团队到底该优化什么",
        "summary": (
            "Demand generation and lead generation are often used interchangeably, but they solve "
            "different problems. Demand generation creates awareness, education, and buying intent "
            "before a form fill. Lead generation captures that intent once it exists."
        ),
        "summary_zh": (
            "Demand generation 和 lead generation 经常被混着说，但它们解决的不是同一个问题。"
            "Demand generation 负责在表单提交之前创造认知、教育和购买意图；lead generation 负责在意图已经出现后把它捕获下来。"
        ),
        "thesis": (
            "Demand generation is about creating and shaping buying intent across time. "
            "Lead generation is about converting some of that intent into identifiable pipeline."
        ),
        "thesis_zh": "Demand generation 是持续塑造购买意图，lead generation 是把其中一部分意图转成可识别 pipeline。",
    },
    {
        "slug": "ai-cmo-workspace",
        "path": "/blog/ai-cmo-workspace",
        "title": "Why we refused to build another marketing dashboard",
        "title_zh": "为什么我们拒绝再做一个营销仪表盘",
        "summary": (
            "OpenCMO started with a simple frustration: teams had data, but not continuity. "
            "Every tool could show a slice of the truth, but almost none could carry that truth "
            "into the next decision."
        ),
        "summary_zh": "OpenCMO 的起点并不是“把更多数据放到一个页面里”，而是一种更深的挫败感：团队明明已经拿到了很多信息，却依然很难把同一份真相带进下一次判断和下一步动作。",
        "thesis": (
            "A real AI CMO layer should reduce context loss between monitoring, interpretation, "
            "coordination, and execution."
        ),
        "thesis_zh": "真正的 AI CMO 层，应该减少监控、解释、协同和执行之间的上下文损耗，而不是只多做一个总览页。",
    },
    {
        "slug": "visibility-operating-system",
        "path": "/blog/visibility-operating-system",
        "title": "Why SEO, GEO, SERP, and community signals belong in the same war room",
        "title_zh": "为什么 SEO、GEO、SERP 和社区信号必须放进同一个战情室",
        "summary": (
            "A modern prospect does not move through one neat funnel. They bounce between Google, "
            "AI assistants, social proof, public threads, and your site. If those surfaces tell "
            "different stories, trust erodes before conversion even begins."
        ),
        "summary_zh": "今天的潜在客户不会沿着一条整齐的漏斗前进。他们会在 Google、AI 助手、公开讨论和你的网站之间来回跳。如果这些表面讲的是不同的故事，信任会在转化开始前就先流失。",
        "thesis": (
            "You cannot manage perception with one channel's metrics when the user's understanding "
            "is formed across several channels at once."
        ),
        "thesis_zh": "当用户的认知是在多个渠道同时形成时，你不可能只靠某一个渠道的指标来管理整体感知。",
    },
    {
        "slug": "crawler-readable-brand-surface",
        "path": "/blog/crawler-readable-brand-surface",
        "title": "How to make one site readable to Google, AI agents, and humans",
        "title_zh": "怎样让 Google、AI agent 和真实用户读到同一个品牌故事",
        "summary": (
            "A public site is no longer just a conversion page. It is also the place where "
            "search engines and AI systems learn what the product is, which routes matter, "
            "and how to retell the brand to someone else."
        ),
        "summary_zh": "今天的公开站点已经不只是转化页，它同时也是搜索引擎和 AI 系统学习你是什么、哪些路由重要、以及该如何复述你的品牌的地方。",
        "thesis": (
            "Readable public surfaces require both strong copy and strong crawl signals; one "
            "without the other leaves the system guessing."
        ),
        "thesis_zh": "想让公开 surface 真正可读，强文案和强 crawl 信号缺一不可；缺任何一边，系统都只能靠猜。",
    },
    {
        "slug": "inside-opencmo-workspace",
        "path": "/blog/inside-opencmo-workspace",
        "title": "Inside OpenCMO: what the workspace actually contains",
        "title_zh": "OpenCMO 里到底有什么：从监控、报告到增长执行的完整链路",
        "summary": (
            "The philosophy matters, but operators still need to know what is in the product. "
            "OpenCMO is built as a chain: collect signals, review them, preserve brand context, "
            "and turn them into actions the team can ship."
        ),
        "summary_zh": "理念重要，但操盘手仍然需要知道产品里到底有什么。OpenCMO 不是一堆散页拼起来的 UI，而是一条完整链路：收集信号、复核问题、保存品牌上下文，再把它们变成团队真正能执行的动作。",
        "thesis": (
            "OpenCMO modules are valuable because they close loops together, not because any "
            "single page is novel in isolation."
        ),
        "thesis_zh": "OpenCMO 的价值不在单个页面有多新奇，而在于这些模块能一起闭环。",
    },
    {
        "slug": "opencmo-vs-mautic-posthog",
        "path": "/blog/opencmo-vs-mautic-posthog",
        "title": "OpenCMO vs Mautic and PostHog: which visibility problem each tool actually solves",
        "title_zh": "OpenCMO vs Mautic vs PostHog：它们分别解决哪一层可见度问题",
        "summary": (
            "Mautic automates lifecycle messaging. PostHog explains product behavior. "
            "OpenCMO monitors how the market discovers and narrates the product across "
            "search, AI answers, and community threads."
        ),
        "summary_zh": (
            "Mautic 负责生命周期自动化，PostHog 负责产品行为分析，OpenCMO "
            "负责搜索、AI 回答和社区里的公开可见度与叙事监控。"
        ),
        "thesis": (
            "Use OpenCMO when the problem is discoverability and narrative drift before "
            "the click, Mautic when the problem is lifecycle orchestration after capture, "
            "and PostHog when the problem is product understanding after activation."
        ),
        "thesis_zh": (
            "如果问题发生在点击之前的可发现性和叙事偏移，用 OpenCMO；如果问题"
            "发生在获客之后的生命周期编排，用 Mautic；如果问题发生在激活之后"
            "的产品理解，用 PostHog。"
        ),
    },
    {
        "slug": "who-should-use-opencmo",
        "path": "/blog/who-should-use-opencmo",
        "title": "Who should use OpenCMO, and when it starts paying for itself",
        "title_zh": "谁应该用 OpenCMO，以及它从什么时候开始值得",
        "summary": (
            "OpenCMO is not for every website. It becomes valuable when visibility work is "
            "already spread across search, AI answers, community discussion, and internal team handoffs."
        ),
        "summary_zh": "OpenCMO 不是给所有网站准备的。当搜索、AI 回答、社区讨论和团队协作已经分散成多个表面时，它的价值才会真正出现。",
        "thesis": (
            "OpenCMO fits teams whose public narrative now changes across several surfaces faster "
            "than the team can track and act on it manually."
        ),
        "thesis_zh": "当品牌叙事已经在多个表面上变化得比团队手工跟进更快时，OpenCMO 才真正适配。",
    },
    {
        "slug": "first-30-days-with-opencmo",
        "path": "/blog/first-30-days-with-opencmo",
        "title": "Your first 30 days with OpenCMO: a practical rollout plan",
        "title_zh": "前 30 天怎么用 OpenCMO：一份可执行的上手路线",
        "summary": (
            "The fastest way to get value is not to click every page. It is to establish a baseline, "
            "identify one narrative gap, and ship one response loop the team will actually keep using."
        ),
        "summary_zh": "最快起效的方法不是把每个页面都点一遍，而是先建立基线，找出一个关键叙事缺口，再做出一个团队真的会持续执行的响应闭环。",
        "thesis": (
            "The right onboarding sequence is baseline, narrative review, prioritization, and execution; "
            "everything else is secondary in month one."
        ),
        "thesis_zh": "第一个月最有效的顺序是：基线、叙事复核、优先级判断、执行闭环；其余都是第二位。",
    },
]

_BLOG_ARTICLE_METADATA_BY_SLUG = {article["slug"]: article for article in _BLOG_ARTICLE_METADATA}

def _localized_article_value(article: dict[str, object], field: str, locale: str) -> str:
    if locale == "zh":
        localized = article.get(f"{field}_zh")
        if isinstance(localized, str) and localized.strip():
            return localized
    return str(article[field])


def _public_path(path: str, locale: str | None = None) -> str:
    normalized = path.strip("/")
    if locale:
        return f"/{locale}" if not normalized else f"/{locale}/{normalized}"
    return "/" if not normalized else f"/{normalized}"


def _public_url(path: str, locale: str | None = None) -> str:
    return f'https://www.aidcmo.com{_public_path(path, locale)}'


def _build_blog_json_ld(locale: str | None = None) -> str:
    localized = locale or "en"
    return json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "Blog",
            "name": "OpenCMO Blog" if localized == "en" else "OpenCMO 博客",
            "description": (
                "A public field guide to OpenCMO positioning, adoption, architecture, "
                "comparisons, and the technical foundations that make the site machine-readable."
                if localized == "en"
                else "一组公开文章，解释 OpenCMO 的定位、适用场景、架构导览、工具对比，以及站点机器可读性的技术基础。"
            ),
            "url": _public_url("/blog", locale),
            "publisher": {
                "@type": "Organization",
                "name": "OpenCMO",
                "url": "https://www.aidcmo.com/",
            },
            "blogPost": [
                {
                    "@type": "BlogPosting",
                    "headline": _localized_article_value(article, "title", localized),
                    "url": _public_url(str(article["path"]), locale),
                    "description": _localized_article_value(article, "summary", localized),
                }
                for article in _BLOG_ARTICLE_METADATA
            ],
        },
        separators=(",", ":"),
    )


def _build_blog_article_json_ld(article: dict[str, object], locale: str | None = None) -> str:
    localized = locale or "en"
    article_url = _public_url(str(article["path"]), locale)
    return json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": _localized_article_value(article, "title", localized),
            "description": _localized_article_value(article, "summary", localized),
            "url": article_url,
            "mainEntityOfPage": article_url,
            "publisher": {
                "@type": "Organization",
                "name": "OpenCMO",
                "url": "https://www.aidcmo.com/",
            },
            "isPartOf": {
                "@type": "Blog",
                "name": "OpenCMO Blog" if localized == "en" else "OpenCMO 博客",
                "url": _public_url("/blog", locale),
            },
        },
        separators=(",", ":"),
    )


def _render_blog_article_static_site_copy(article: dict[str, object], locale: str | None = None) -> str:
    localized = locale or "en"
    title = escape(_localized_article_value(article, "title", localized))
    summary = escape(_localized_article_value(article, "summary", localized))
    thesis = escape(_localized_article_value(article, "thesis", localized))
    url = escape(_public_url(str(article["path"]), locale))
    thesis_title = "Core thesis" if localized == "en" else "核心观点"
    canonical_title = "Canonical article URL" if localized == "en" else "规范文章地址"
    return f"""
<main id="static-site-copy">
  <article>
    <header>
      <p>OpenCMO Blog</p>
      <h1>{title}</h1>
      <p>{summary}</p>
    </header>
    <section>
      <h2>{thesis_title}</h2>
      <p>{thesis}</p>
    </section>
    <section>
      <h2>{canonical_title}</h2>
      <p><a href="{url}">{url}</a></p>
    </section>
  </article>
</main>
""".strip()

_SAMPLE_AUDIT_STATIC_SITE_COPY_BY_LOCALE = {
    "en": """
<main id="static-site-copy">
  <header>
    <p>OpenCMO Sample Audit</p>
    <h1>A public walkthrough of how OpenCMO turns visibility signals into next actions</h1>
    <p>
      This sample audit shows the shape of an OpenCMO review: what changed across SEO,
      AI search, community discussion, competitors, and which actions are ready to ship.
    </p>
  </header>
  <section>
    <h2>What this public page includes</h2>
    <ul>
      <li>SEO findings that explain crawl, metadata, and site-health gaps</li>
      <li>AI visibility notes that show how assistants currently frame the brand</li>
      <li>Community and competitor signals that influence the public narrative</li>
      <li>Prioritized next actions that operators can actually ship</li>
    </ul>
  </section>
  <section>
    <h2>Why this page is public</h2>
    <p>
      It gives search engines, buyers, and AI agents a concrete example of the
      product output without exposing the private workspace routes.
    </p>
  </section>
</main>
""".strip(),
    "zh": """
<main id="static-site-copy">
  <header>
    <p>OpenCMO 示例审计</p>
    <h1>一份公开示例：OpenCMO 怎样把可见度信号变成下一步动作</h1>
    <p>
      这份 sample audit 展示了一次 OpenCMO 复核的大致形状：SEO、AI 搜索、
      社区讨论、竞品和哪些动作已经可以进入执行。
    </p>
  </header>
  <section>
    <h2>这个公开页面包含什么</h2>
    <ul>
      <li>解释抓取、元数据和站点健康缺口的 SEO 发现</li>
      <li>展示 AI 助手当前如何概括品牌的 AI 可见度说明</li>
      <li>影响公开叙事的社区和竞品信号</li>
      <li>操盘手可以真正推进的优先级动作</li>
    </ul>
  </section>
  <section>
    <h2>为什么它需要公开</h2>
    <p>
      它给搜索引擎、买家和 AI agent 一个具体样本，让外部系统不用进入私有 workspace
      也能理解产品输出长什么样。
    </p>
  </section>
</main>
""".strip(),
}


_SERVICE_PAGE_METADATA_BY_PATH = {
    "b2b-leads": {
        "title": "Overseas B2B Lead Data | aidCMO",
        "title_zh": "海外 B2B 线索数据 | aidCMO",
        "description": (
            "Request overseas B2B lead data filtered by country, industry, role, "
            "company size, website, domain, and validation status."
        ),
        "description_zh": "按国家、行业、职位、公司规模、官网、域名和验证状态筛选海外 B2B 线索数据。",
        "heading": "Overseas B2B lead data",
        "heading_zh": "海外 B2B 线索数据",
        "bullets": [
            "Country, region, industry, role, company-size, website, and company-domain filters.",
            "Delivery fields can include company, website, contact, role, business email, LinkedIn, region, and validation status.",
            "Email verification, deduplication, risky-mailbox labels, bounce-risk grading, and replacement rules can be included.",
            "Built for legitimate B2B business development and market research, not indiscriminate bulk sending.",
        ],
        "bullets_zh": [
            "支持国家、地区、行业、职位、公司规模、官网和企业域名筛选。",
            "交付字段可包含公司、官网、联系人、职位、企业邮箱、LinkedIn、地区和验证状态。",
            "可包含邮箱验证、去重、风险邮箱标记、退信风险分级和替换规则。",
            "面向合法 B2B 商业开发和市场研究，不是无差别群发服务。",
        ],
    },
    "seo-geo": {
        "title": "SEO and GEO AI Search Optimization | aidCMO",
        "title_zh": "SEO 与 GEO/AI 搜索优化 | aidCMO",
        "description": (
            "SEO, GEO, AI search visibility, brand entity optimization, SERP analysis, "
            "content strategy, and monthly execution recommendations."
        ),
        "description_zh": "提供 SEO、GEO、AI 搜索可见度、品牌实体优化、SERP 分析、内容策略和月度执行建议。",
        "heading": "SEO and GEO growth services",
        "heading_zh": "SEO/GEO 增长服务",
        "bullets": [
            "Technical SEO checks for crawlability, metadata, structure, performance, and page quality.",
            "Keyword and content strategy for overseas acquisition pages, industry terms, and comparison pages.",
            "AI search and GEO review for assistant summaries, citations, brand entities, and answer quality.",
            "Competitor and SERP analysis with monthly reports and execution recommendations.",
        ],
        "bullets_zh": [
            "技术 SEO 检查，覆盖抓取、元数据、结构、性能和页面质量。",
            "面向海外获客页、行业关键词和竞品对比页的关键词与内容策略。",
            "AI 搜索与 GEO 复核，覆盖助手摘要、引用、品牌实体和回答质量。",
            "竞品与 SERP 分析，并提供月度报告和执行建议。",
        ],
    },
    "open-source": {
        "title": "OpenCMO Open-Source Growth System | aidCMO",
        "title_zh": "OpenCMO 开源增长系统 | aidCMO",
        "description": (
            "OpenCMO is the open-source system behind aidCMO's SEO, GEO, SERP, "
            "community, and AI visibility methodology."
        ),
        "description_zh": "OpenCMO 是 aidCMO SEO、GEO、SERP、社区和 AI 可见度方法论背后的开源系统。",
        "heading": "OpenCMO technical support",
        "heading_zh": "OpenCMO 技术支持",
        "bullets": [
            "OpenCMO remains a public Apache 2.0 open-source project.",
            "It analyzes SEO, GEO, SERP, community discussion, and AI visibility signals.",
            "aidCMO uses this method in overseas acquisition diagnosis, content strategy, and growth execution.",
            "The homepage now sells commercial services first while keeping OpenCMO as technical support.",
        ],
        "bullets_zh": [
            "OpenCMO 保留为 Apache 2.0 开源项目。",
            "它用于分析 SEO、GEO、SERP、社区讨论和 AI 可见度信号。",
            "aidCMO 将这套方法用于海外获客诊断、内容策略和增长执行。",
            "首页优先销售商业服务，同时保留 OpenCMO 作为技术支持。",
        ],
    },
    "sample-data": {
        "title": "Request Sample B2B Lead Data | aidCMO",
        "title_zh": "申请 B2B 线索样例数据 | aidCMO",
        "description": "Request a sample B2B lead-data structure with fields, validation status, cleaning notes, and risk labels.",
        "description_zh": "申请包含字段、验证状态、清洗说明和风险标记的 B2B 线索样例数据。",
        "heading": "Sample data request",
        "heading_zh": "样例数据申请",
        "bullets": [
            "Provide target countries, industries, company types, roles, and preferred delivery format.",
            "Review fields, validation labels, risky-email notes, and replacement assumptions before scaling.",
            "Use the sample to evaluate fit, field structure, validation labels, and risk notes before scaling.",
        ],
        "bullets_zh": [
            "提供目标国家、行业、公司类型、职位和偏好交付格式。",
            "放大规模前先复核字段、验证标签、风险邮箱说明和替换假设。",
            "样例用于评估匹配度，不代表无限供应或完美送达。",
        ],
    },
    "contact": {
        "title": "Contact aidCMO | B2B Leads and SEO/GEO Services",
        "title_zh": "联系 aidCMO | B2B 线索与 SEO/GEO 服务",
        "description": "Contact aidCMO for overseas B2B lead data, sample data, email verification, SEO services, and GEO AI search optimization.",
        "description_zh": "联系 aidCMO 咨询海外 B2B 线索、样例数据、邮箱验证、SEO 服务和 GEO/AI 搜索优化。",
        "heading": "Contact aidCMO",
        "heading_zh": "联系 aidCMO",
        "bullets": [
            "Email: hello@aidcmo.com",
            "For lead data, prepare country, industry, role, company type, volume, and delivery format.",
            "For SEO/GEO, share the website, target market, competitors, and current content problem.",
            "aidCMO does not support spam, fraud, phishing, illegal use, or high-risk blast campaigns.",
        ],
        "bullets_zh": [
            "邮箱: hello@aidcmo.com",
            "线索需求请准备国家、行业、职位、公司类型、数量和交付格式。",
            "SEO/GEO 需求请提供网站、目标市场、竞品和当前内容问题。",
            "aidCMO 不支持垃圾邮件、欺诈、钓鱼、违法用途或高风险群发活动。",
        ],
    },
    "data-policy": {
        "title": "Data Sources and Compliance Notes | aidCMO",
        "title_zh": "数据来源与合规说明 | aidCMO",
        "description": (
            "aidCMO data policy: B2B commercial leads, public business sources, "
            "email validation, removal support, and acceptable-use boundaries."
        ),
        "description_zh": "aidCMO 数据政策：B2B 商业线索、公开商业来源、邮箱验证、移除支持、可接受用途边界和数据质量说明。",
        "heading": "Data sources and compliance notes",
        "heading_zh": "数据来源与合规说明",
        "bullets": [
            "Only B2B commercial leads are provided.",
            "Sources can include public business information, company websites, public directories, and public professional profiles.",
            "Removal, suppression, or deletion requests can be supported where applicable.",
            "Validation status, cleaning notes, and risk labels should remain visible.",
            "Spam, fraud, phishing, illegal use, unlimited sending, and blast campaigns are not supported.",
        ],
        "bullets_zh": [
            "只提供 B2B 商业线索。",
            "来源可包括公开商业信息、企业官网、公开目录和公开职业资料。",
            "在适用情况下支持移除、抑制或删除请求。",
            "验证状态、清洗说明和风险标签应保持可见。",
            "不支持垃圾邮件、欺诈、钓鱼、违法用途、无限群发和轰炸式活动。",
        ],
    },
}


def _localized_service_value(page: dict[str, object], field: str, locale: str) -> str:
    if locale == "zh":
        localized = page.get(f"{field}_zh")
        if isinstance(localized, str) and localized.strip():
            return localized
    return str(page[field])


def _localized_service_bullets(page: dict[str, object], locale: str) -> list[str]:
    if locale == "zh" and isinstance(page.get("bullets_zh"), list):
        return [str(item) for item in page["bullets_zh"]]
    return [str(item) for item in page["bullets"]]


def _render_service_static_site_copy(route: str, page: dict[str, object], locale: str | None = None) -> str:
    localized = locale or "en"
    heading = escape(_localized_service_value(page, "heading", localized))
    description = escape(_localized_service_value(page, "description", localized))
    url = escape(_public_url(f"/{route}", locale))
    bullets = "\n".join(f"      <li>{escape(item)}</li>" for item in _localized_service_bullets(page, localized))
    section_title = "What this page covers" if localized == "en" else "这个页面包含什么"
    canonical_title = "Canonical URL" if localized == "en" else "规范页面地址"
    return f"""
<main id="static-site-copy">
  <article>
    <header>
      <p>aidCMO</p>
      <h1>{heading}</h1>
      <p>{description}</p>
    </header>
    <section>
      <h2>{section_title}</h2>
      <ul>
{bullets}
      </ul>
    </section>
    <section>
      <h2>{canonical_title}</h2>
      <p><a href="{url}">{url}</a></p>
    </section>
  </article>
</main>
""".strip()


def _build_service_json_ld(route: str, page: dict[str, object], locale: str | None = None) -> str:
    localized = locale or "en"
    service_url = _public_url(f"/{route}", locale)
    return json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "Service",
            "name": _localized_service_value(page, "heading", localized),
            "description": _localized_service_value(page, "description", localized),
            "url": service_url,
            "provider": {
                "@type": "Organization",
                "name": "aidCMO",
                "url": _public_url("/", locale),
                "sameAs": ["https://github.com/study8677/OpenCMO"],
            },
            "areaServed": "International",
            "serviceType": _localized_service_value(page, "heading", localized),
        },
        separators=(",", ":"),
    )


def _build_home_json_ld(locale: str | None = None) -> str:
    localized = locale or "en"
    return json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "ProfessionalService",
            "name": "aidCMO",
            "url": _public_url("/", locale),
            "image": "https://www.aidcmo.com/logo.png",
            "description": (
                "aidCMO provides compliant overseas B2B lead data, email verification, "
                "data cleaning, SEO services, and GEO AI search visibility optimization."
                if localized == "en"
                else "aidCMO 提供合规的海外 B2B 邮箱线索、邮箱验证、数据清洗、SEO 服务与 GEO/AI 搜索可见度优化。"
            ),
            "serviceType": [
                "Overseas B2B lead data",
                "Email verification and data cleaning",
                "SEO services",
                "GEO and AI search visibility optimization",
            ],
            "areaServed": "International",
            "sameAs": [
                "https://github.com/study8677/OpenCMO",
            ],
            "hasOfferCatalog": {
                "@type": "OfferCatalog",
                "name": "aidCMO B2B growth services",
                "itemListElement": [
                    {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "Overseas B2B lead data"}},
                    {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "SEO and GEO optimization"}},
                ],
            },
        },
        separators=(",", ":"),
    )


def _build_sample_audit_json_ld(locale: str | None = None) -> str:
    localized = locale or "en"
    return json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": "OpenCMO Sample Audit" if localized == "en" else "OpenCMO 示例审计",
            "description": (
                "A public walkthrough of a sample OpenCMO visibility audit covering SEO, "
                "AI search, community signal review, competitors, and next actions."
                if localized == "en"
                else "一份公开示例，展示 OpenCMO 如何复核 SEO、AI 搜索、社区信号、竞品和后续动作。"
            ),
            "url": _public_url("/sample-audit", locale),
            "isPartOf": {
                "@type": "WebSite",
                "name": "OpenCMO",
                "url": _public_url("/", locale),
            },
            "about": {
                "@type": "SoftwareApplication",
                "name": "OpenCMO",
                "url": _public_url("/", locale),
                "applicationCategory": "BusinessApplication",
                "operatingSystem": "Web",
            },
        },
        separators=(",", ":"),
    )

_APP_STATIC_SITE_COPY = """
<main id="static-site-copy">
  <header>
    <p>OpenCMO Workspace</p>
    <h1>Private application surface</h1>
    <p>
      This route belongs to the operator workspace for projects, approvals,
      reports, and AI-assisted review. Use the public homepage and blog for
      product overview and machine-readable discovery.
    </p>
  </header>
  <section>
    <h2>Public product resources</h2>
    <ul>
      <li>Homepage: https://www.aidcmo.com/</li>
      <li>Blog: https://www.aidcmo.com/blog</li>
      <li>Machine-readable summary: https://www.aidcmo.com/llms.txt</li>
    </ul>
  </section>
</main>
""".strip()


_CANONICAL_HOST_REDIRECTS = {
    "aidcmo.com": "www.aidcmo.com",
}


def _replace_metadata(rendered: str, replacements: list[tuple[str, str]]) -> str:
    for pattern, replacement in replacements:
        rendered = re.sub(
            pattern,
            lambda _match, replacement=replacement: replacement,
            rendered,
            count=1,
            flags=re.IGNORECASE | re.DOTALL,
        )
    return rendered


def _replace_static_site_copy(rendered: str, static_copy: str) -> str:
    return re.sub(
        r'<main id="static-site-copy">.*?</main>',
        static_copy,
        rendered,
        count=1,
        flags=re.DOTALL,
    )


def _replace_html_lang(rendered: str, locale: str | None) -> str:
    lang = _HREFLANG_BY_LOCALE.get(locale or "en", "en")
    return re.sub(r'<html\s+lang="[^"]*">', f'<html lang="{lang}">', rendered, count=1, flags=re.IGNORECASE)


def _build_alternate_link_tags(path: str) -> str:
    return "".join(
        f'<link rel="alternate" hreflang="{href_lang}" href="{_public_url(path, locale)}" />'
        for href_lang, locale in [
            ("x-default", None),
            (_HREFLANG_BY_LOCALE["en"], "en"),
            (_HREFLANG_BY_LOCALE["zh"], "zh"),
        ]
    )


def _replace_canonical_and_alternates(rendered: str, canonical_url: str, path: str) -> str:
    replacement = f'<link rel="canonical" href="{canonical_url}" />{_build_alternate_link_tags(path)}'
    return re.sub(
        r'<link\s+rel="canonical"\s+href="[^"]*"\s*/?>',
        replacement,
        rendered,
        count=1,
        flags=re.IGNORECASE,
    )


def _split_public_locale(full_path: str) -> tuple[str | None, str]:
    normalized = full_path.strip("/")
    if not normalized:
        return None, ""
    first, *rest = normalized.split("/", 1)
    if first in _SEO_PUBLIC_LOCALES:
        return first, rest[0] if rest else ""
    return None, normalized


def _is_app_surface(full_path: str) -> bool:
    normalized = full_path.strip("/")
    if not normalized:
        return False
    return (
        normalized in {"workspace", "approvals", "chat"}
        or normalized.startswith("projects/")
        or normalized == "projects"
    )


def _apply_public_route_metadata(html: str, full_path: str) -> str:
    route_locale, normalized = _split_public_locale(full_path)
    locale_key = route_locale or "en"
    rendered = _replace_html_lang(html, route_locale)

    if _is_app_surface(normalized):
        canonical_url = f"https://www.aidcmo.com/{normalized}" if normalized else "https://www.aidcmo.com/"
        replacements = [
            (
                r"<title>.*?</title>",
                "<title>OpenCMO Workspace | Private application surface</title>",
            ),
            (
                r'<meta\s+name="description"\s+content="[^"]*"\s*/?>',
                '<meta name="description" content="Private OpenCMO workspace route for operators. Use the homepage and blog for the public product overview." />',
            ),
            (
                r'<meta\s+name="robots"\s+content="[^"]*"\s*/?>',
                '<meta name="robots" content="noindex,nofollow,noarchive,nosnippet" />',
            ),
            (
                r'<meta\s+property="og:title"\s+content="[^"]*"\s*/?>',
                '<meta property="og:title" content="OpenCMO Workspace | Private application surface" />',
            ),
            (
                r'<meta\s+property="og:description"\s+content="[^"]*"\s*/?>',
                '<meta property="og:description" content="Private OpenCMO workspace route for projects, approvals, reports, and operator workflows." />',
            ),
            (
                r'<meta\s+property="og:url"\s+content="[^"]*"\s*/?>',
                f'<meta property="og:url" content="{canonical_url}" />',
            ),
            (
                r'<meta\s+name="twitter:title"\s+content="[^"]*"\s*/?>',
                '<meta name="twitter:title" content="OpenCMO Workspace | Private application surface" />',
            ),
            (
                r'<meta\s+name="twitter:description"\s+content="[^"]*"\s*/?>',
                '<meta name="twitter:description" content="Private OpenCMO workspace route for projects, approvals, reports, and operator workflows." />',
            ),
        ]

        rendered = _replace_metadata(rendered, replacements)
        rendered = re.sub(
            r'<link\s+rel="canonical"\s+href="[^"]*"\s*/?>',
            f'<link rel="canonical" href="{canonical_url}" />',
            rendered,
            count=1,
            flags=re.IGNORECASE,
        )
        return _replace_static_site_copy(rendered, _APP_STATIC_SITE_COPY)

    service_page = _SERVICE_PAGE_METADATA_BY_PATH.get(normalized)
    if service_page:
        title = _localized_service_value(service_page, "title", locale_key)
        description = _localized_service_value(service_page, "description", locale_key)
        canonical_url = _public_url(f"/{normalized}", route_locale)
        replacements = [
            (r"<title>.*?</title>", f"<title>{title}</title>"),
            (r'<meta\s+name="description"\s+content="[^"]*"\s*/?>', f'<meta name="description" content="{description}" />'),
            (r'<meta\s+property="og:title"\s+content="[^"]*"\s*/?>', f'<meta property="og:title" content="{title}" />'),
            (r'<meta\s+property="og:description"\s+content="[^"]*"\s*/?>', f'<meta property="og:description" content="{description}" />'),
            (r'<meta\s+property="og:url"\s+content="[^"]*"\s*/?>', f'<meta property="og:url" content="{canonical_url}" />'),
            (r'<meta\s+name="twitter:title"\s+content="[^"]*"\s*/?>', f'<meta name="twitter:title" content="{title}" />'),
            (r'<meta\s+name="twitter:description"\s+content="[^"]*"\s*/?>', f'<meta name="twitter:description" content="{description}" />'),
            (
                r'<script\s+type="application/ld\+json">.*?</script>',
                f'<script type="application/ld+json">{_build_service_json_ld(normalized, service_page, route_locale)}</script>',
            ),
        ]
        rendered = _replace_metadata(rendered, replacements)
        rendered = _replace_canonical_and_alternates(rendered, canonical_url, f"/{normalized}")
        return _replace_static_site_copy(rendered, _render_service_static_site_copy(normalized, service_page, route_locale))

    if normalized.startswith("blog/"):
        slug = normalized.split("/", 1)[1]
        article = _BLOG_ARTICLE_METADATA_BY_SLUG.get(slug)
        if not article:
            return rendered

        article_title = _localized_article_value(article, "title", locale_key)
        article_summary = _localized_article_value(article, "summary", locale_key)
        article_url = _public_url(str(article["path"]), route_locale)
        article_json_ld = _build_blog_article_json_ld(article, route_locale)
        replacements = [
            (
                r"<title>.*?</title>",
                f"<title>{article_title} | OpenCMO Blog</title>",
            ),
            (
                r'<meta\s+name="description"\s+content="[^"]*"\s*/?>',
                f'<meta name="description" content="{article_summary}" />',
            ),
            (
                r'<meta\s+property="og:type"\s+content="[^"]*"\s*/?>',
                '<meta property="og:type" content="article" />',
            ),
            (
                r'<meta\s+property="og:title"\s+content="[^"]*"\s*/?>',
                f'<meta property="og:title" content="{article_title} | OpenCMO Blog" />',
            ),
            (
                r'<meta\s+property="og:description"\s+content="[^"]*"\s*/?>',
                f'<meta property="og:description" content="{article_summary}" />',
            ),
            (
                r'<meta\s+property="og:url"\s+content="[^"]*"\s*/?>',
                f'<meta property="og:url" content="{article_url}" />',
            ),
            (
                r'<meta\s+name="twitter:title"\s+content="[^"]*"\s*/?>',
                f'<meta name="twitter:title" content="{article_title} | OpenCMO Blog" />',
            ),
            (
                r'<meta\s+name="twitter:description"\s+content="[^"]*"\s*/?>',
                f'<meta name="twitter:description" content="{article_summary}" />',
            ),
            (
                r'<script\s+type="application/ld\+json">.*?</script>',
                f'<script type="application/ld+json">{article_json_ld}</script>',
            ),
        ]

        rendered = _replace_metadata(rendered, replacements)
        rendered = _replace_canonical_and_alternates(rendered, article_url, str(article["path"]))
        return _replace_static_site_copy(rendered, _render_blog_article_static_site_copy(article, route_locale))

    if normalized == "":
        title = (
            "aidCMO | Overseas B2B Leads and SEO/GEO Growth Services"
            if locale_key == "en"
            else "aidCMO | 海外 B2B 线索数据与 SEO/GEO 增长服务"
        )
        description = (
            "aidCMO provides compliant overseas B2B lead data, email verification, data cleaning, SEO services, and GEO AI search visibility optimization backed by OpenCMO."
            if locale_key == "en"
            else "aidCMO 提供合规的海外 B2B 邮箱线索、邮箱验证、数据清洗、SEO 服务与 GEO/AI 搜索可见度优化，并由 OpenCMO 方法论技术支持。"
        )
        canonical_url = _public_url("/", route_locale)
        replacements = [
            (r"<title>.*?</title>", f"<title>{title}</title>"),
            (r'<meta\s+name="description"\s+content="[^"]*"\s*/?>', f'<meta name="description" content="{description}" />'),
            (r'<meta\s+property="og:title"\s+content="[^"]*"\s*/?>', f'<meta property="og:title" content="{title}" />'),
            (r'<meta\s+property="og:description"\s+content="[^"]*"\s*/?>', f'<meta property="og:description" content="{description}" />'),
            (r'<meta\s+property="og:url"\s+content="[^"]*"\s*/?>', f'<meta property="og:url" content="{canonical_url}" />'),
            (r'<meta\s+name="twitter:title"\s+content="[^"]*"\s*/?>', f'<meta name="twitter:title" content="{title}" />'),
            (r'<meta\s+name="twitter:description"\s+content="[^"]*"\s*/?>', f'<meta name="twitter:description" content="{description}" />'),
            (r'<script\s+type="application/ld\+json">.*?</script>', f'<script type="application/ld+json">{_build_home_json_ld(route_locale)}</script>'),
        ]
        rendered = _replace_metadata(rendered, replacements)
        rendered = _replace_canonical_and_alternates(rendered, canonical_url, "/")
        return _replace_static_site_copy(rendered, _HOME_STATIC_SITE_COPY_BY_LOCALE[locale_key])

    if normalized == "blog":
        title = (
            "OpenCMO Blog | CMO, Product Marketing, GTM, and AI CMO Field Guide"
            if locale_key == "en"
            else "OpenCMO Blog | CMO、产品营销、GTM 与 AI CMO 公开说明"
        )
        description = (
            "Read the public OpenCMO field guide on CMO work, product marketing, GTM strategy, brand positioning, demand generation, AI CMO workflows, and crawler-readable public surfaces."
            if locale_key == "en"
            else "阅读 OpenCMO 的公开文章，了解 CMO、产品营销、GTM、品牌定位、需求生成、AI CMO 工作方式，以及站点机器可读性。"
        )
        canonical_url = _public_url("/blog", route_locale)
        replacements = [
            (r"<title>.*?</title>", f"<title>{title}</title>"),
            (r'<meta\s+name="description"\s+content="[^"]*"\s*/?>', f'<meta name="description" content="{description}" />'),
            (r'<meta\s+property="og:title"\s+content="[^"]*"\s*/?>', f'<meta property="og:title" content="{title}" />'),
            (r'<meta\s+property="og:description"\s+content="[^"]*"\s*/?>', f'<meta property="og:description" content="{description}" />'),
            (r'<meta\s+property="og:url"\s+content="[^"]*"\s*/?>', f'<meta property="og:url" content="{canonical_url}" />'),
            (r'<meta\s+name="twitter:title"\s+content="[^"]*"\s*/?>', f'<meta name="twitter:title" content="{title}" />'),
            (r'<meta\s+name="twitter:description"\s+content="[^"]*"\s*/?>', f'<meta name="twitter:description" content="{description}" />'),
            (r'<script\s+type="application/ld\+json">.*?</script>', f'<script type="application/ld+json">{_build_blog_json_ld(route_locale)}</script>'),
        ]
        rendered = _replace_metadata(rendered, replacements)
        rendered = _replace_canonical_and_alternates(rendered, canonical_url, "/blog")
        return _replace_static_site_copy(rendered, _BLOG_STATIC_SITE_COPY_BY_LOCALE[locale_key])

    if normalized == "sample-audit":
        title = (
            "OpenCMO Sample Audit | Public walkthrough of a visibility operating report"
            if locale_key == "en"
            else "OpenCMO 示例审计 | 一份公开的可见度报告 walkthrough"
        )
        description = (
            "See a public OpenCMO sample audit covering SEO, AI visibility, community signals, competitors, and the next actions an operator would ship."
            if locale_key == "en"
            else "查看一份公开的 OpenCMO 示例审计，了解 SEO、AI 可见度、社区信号、竞品和下一步动作。"
        )
        canonical_url = _public_url("/sample-audit", route_locale)
        replacements = [
            (r"<title>.*?</title>", f"<title>{title}</title>"),
            (r'<meta\s+name="description"\s+content="[^"]*"\s*/?>', f'<meta name="description" content="{description}" />'),
            (r'<meta\s+property="og:title"\s+content="[^"]*"\s*/?>', f'<meta property="og:title" content="{title}" />'),
            (r'<meta\s+property="og:description"\s+content="[^"]*"\s*/?>', f'<meta property="og:description" content="{description}" />'),
            (r'<meta\s+property="og:url"\s+content="[^"]*"\s*/?>', f'<meta property="og:url" content="{canonical_url}" />'),
            (r'<meta\s+name="twitter:title"\s+content="[^"]*"\s*/?>', f'<meta name="twitter:title" content="{title}" />'),
            (r'<meta\s+name="twitter:description"\s+content="[^"]*"\s*/?>', f'<meta name="twitter:description" content="{description}" />'),
            (r'<script\s+type="application/ld\+json">.*?</script>', f'<script type="application/ld+json">{_build_sample_audit_json_ld(route_locale)}</script>'),
        ]
        rendered = _replace_metadata(rendered, replacements)
        rendered = _replace_canonical_and_alternates(rendered, canonical_url, "/sample-audit")
        return _replace_static_site_copy(rendered, _SAMPLE_AUDIT_STATIC_SITE_COPY_BY_LOCALE[locale_key])

    return rendered


# ---------------------------------------------------------------------------
# Lifecycle hooks
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def _startup_fix_stale_expansions():
    """Mark any stale 'running' expansions as interrupted (from previous process)."""
    await storage.ensure_db()
    try:
        fixed = await storage.fix_stale_expansions(timeout_seconds=60)
        if fixed:
            logger.info("Fixed %d stale expansion(s) on startup", fixed)
    except Exception:
        pass  # table may not exist yet on first run

    # Load DB-stored API settings into os.environ so background workers can read them.
    from opencmo.config import apply_runtime_settings, configure_agent_tracing
    await apply_runtime_settings()
    logger.info("Runtime settings loaded from DB into environment")
    tracing_disabled = configure_agent_tracing()
    logger.info("Agents tracing %s", "disabled for custom provider" if tracing_disabled else "enabled")


@app.on_event("startup")
async def _startup_runtime_services():
    """Start optional runtime services after DB bootstrap."""
    from opencmo import scheduler
    from opencmo.background.executors import (
        run_blog_generation_executor,
        run_github_enrich_executor,
        run_graph_expansion_executor,
        run_report_executor,
        run_scan_executor,
    )
    from opencmo.background.worker import get_background_worker

    worker = get_background_worker()
    worker.register_executor("scan", run_scan_executor)
    worker.register_executor("report", run_report_executor)
    worker.register_executor("graph_expansion", run_graph_expansion_executor)
    worker.register_executor("github_enrich", run_github_enrich_executor)
    worker.register_executor("blog_generation", run_blog_generation_executor)
    await worker.start()

    if not scheduler.is_scheduler_enabled():
        logger.info("Scheduler disabled by OPENCMO_ENABLE_SCHEDULER; timed monitors will remain inactive.")
        return

    if not scheduler.is_scheduler_available():
        logger.info("APScheduler not installed; scheduled monitors will remain inactive.")
        return

    loaded_jobs = await scheduler.load_jobs_from_db()
    scheduler.start_scheduler()
    logger.info("Scheduler started with %d enabled monitor job(s)", loaded_jobs)


@app.on_event("shutdown")
async def _shutdown_runtime_services():
    """Stop optional runtime services cleanly."""
    from opencmo import scheduler
    from opencmo.background.worker import get_background_worker

    await get_background_worker().stop()
    scheduler.stop_scheduler()
    logger.info("Scheduler stopped")


# ---------------------------------------------------------------------------
# BYOK middleware — per-user API key isolation
# ---------------------------------------------------------------------------

# Keys that can be injected from the X-User-Keys header
_INJECTABLE_KEYS = frozenset({
    "OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENCMO_MODEL_DEFAULT",
    "TAVILY_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_AI_API_KEY",
    "PAGESPEED_API_KEY",
})


@app.middleware("http")
async def canonical_host_middleware(request: Request, call_next):
    """Redirect production traffic to the canonical public host."""
    host_header = request.headers.get("host", "")
    incoming_host = host_header.split(":", 1)[0].lower()
    redirect_host = _CANONICAL_HOST_REDIRECTS.get(incoming_host)
    if redirect_host:
        forwarded_proto = request.headers.get("x-forwarded-proto", "https")
        scheme = forwarded_proto.split(",", 1)[0].strip() or request.url.scheme
        target_url = request.url.replace(scheme=scheme, netloc=redirect_host)
        return RedirectResponse(str(target_url), status_code=308)
    return await call_next(request)


@app.middleware("http")
async def byok_middleware(request: Request, call_next):
    """Read per-user API keys from X-User-Keys header and inject via ContextVar.

    Uses ContextVar instead of os.environ for per-request key isolation,
    preventing race conditions where concurrent requests could overwrite
    each other's API keys.
    """
    raw = request.headers.get("X-User-Keys")
    if not raw:
        return await call_next(request)

    import base64
    import json as _json

    try:
        decoded = base64.b64decode(raw).decode()
        user_keys: dict = _json.loads(decoded)
    except Exception:
        return await call_next(request)

    # Filter to allowed keys only
    filtered = {
        k: v for k, v in user_keys.items()
        if k in _INJECTABLE_KEYS and isinstance(v, str) and v.strip()
    }
    if not filtered:
        return await call_next(request)

    # Inject into ContextVar (Task-local, no race condition)
    from opencmo import llm
    token = llm.set_request_keys(filtered)
    try:
        response = await call_next(request)
    finally:
        llm.reset_request_keys(token)

    return response


@app.get("/api/v1/health")
async def api_v1_health():
    from opencmo import scheduler

    return JSONResponse({
        "ok": True,
        "scheduler": scheduler.scheduler_status(),
    })


# ---------------------------------------------------------------------------
# Include domain routers
# ---------------------------------------------------------------------------

from opencmo.web.routers.approvals import router as approvals_router
from opencmo.web.routers.blog_gen import router as blog_gen_router
from opencmo.web.routers.brand_kit import router as brand_kit_router
from opencmo.web.routers.campaigns import router as campaigns_router
from opencmo.web.routers.chat import router as chat_router
from opencmo.web.routers.events import router as events_router
from opencmo.web.routers.github import router as github_router
from opencmo.web.routers.graph import router as graph_router
from opencmo.web.routers.insights import router as insights_router
from opencmo.web.routers.keywords import router as keywords_router
from opencmo.web.routers.legacy import router as legacy_router
from opencmo.web.routers.monitors import router as monitors_router
from opencmo.web.routers.performance import router as performance_router
from opencmo.web.routers.projects import router as projects_router
from opencmo.web.routers.quick_actions import router as quick_actions_router
from opencmo.web.routers.report import router as report_router
from opencmo.web.routers.settings import router as settings_router
from opencmo.web.routers.site import router as site_router
from opencmo.web.routers.tasks import router as tasks_router

app.include_router(legacy_router, prefix="/legacy")
app.include_router(projects_router)
app.include_router(graph_router)
app.include_router(insights_router)
app.include_router(keywords_router)
app.include_router(monitors_router)
app.include_router(campaigns_router)
app.include_router(approvals_router)
app.include_router(tasks_router)
app.include_router(chat_router)
app.include_router(settings_router)
app.include_router(site_router)
app.include_router(report_router)
app.include_router(events_router)
app.include_router(brand_kit_router)
app.include_router(performance_router)
app.include_router(quick_actions_router)
app.include_router(github_router)
app.include_router(blog_gen_router)


# ---------------------------------------------------------------------------
# SPA mount — /app/ serves React frontend
# ---------------------------------------------------------------------------


@app.get("/")
@app.head("/")
@app.get("/{full_path:path}")
@app.head("/{full_path:path}")
async def spa_catchall(request: Request, full_path: str = ""):
    spa_root = _SPA_DIR.resolve()
    index = spa_root / "index.html"
    if not index.exists():
        return HTMLResponse(
            "<h1>Frontend not built</h1><p>Run <code>cd frontend && npm run build</code> to build the SPA.</p>",
            status_code=404,
        )
    # Serve static assets from dist
    if full_path and not full_path.startswith("index.html"):
        asset = (spa_root / full_path).resolve()
        if spa_root in asset.parents and asset.exists() and asset.is_file():
            import mimetypes
            ct = mimetypes.guess_type(str(asset))[0] or "application/octet-stream"
            return StreamingResponse(open(asset, "rb"), media_type=ct)

    new_visitor_id: str | None = None
    try:
        await storage.increment_site_counter("total_visits")
        if not request.cookies.get("opencmo_visitor_id"):
            new_visitor_id = uuid.uuid4().hex
            await storage.increment_site_counter("unique_visitors")
    except Exception:
        logger.exception("Failed to record site visit counters")

    rendered_html = _apply_public_route_metadata(index.read_text(), full_path)

    # SPA fallback — always return index.html
    response = HTMLResponse(rendered_html)
    if _is_app_surface(full_path):
        response.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive, nosnippet"
    if new_visitor_id:
        response.set_cookie(
            "opencmo_visitor_id",
            new_visitor_id,
            max_age=60 * 60 * 24 * 365,
            httponly=True,
            samesite="lax",
            secure=request.url.scheme == "https",
        )
    return response


# ---------------------------------------------------------------------------
# Server entry point
# ---------------------------------------------------------------------------


def run_server(port: int = 8080):
    import uvicorn

    load_dotenv()
    host = os.environ.get("OPENCMO_WEB_HOST", "127.0.0.1")
    uvicorn.run(app, host=host, port=port)

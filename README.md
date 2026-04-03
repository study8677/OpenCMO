<div align="center">
  <img src="assets/logo.png" alt="OpenCMO Logo" width="120" />
</div>

<h1 align="center">OpenCMO</h1>

<p align="center">
  <strong>OpenCMO is an open-source growth system that unifies SEO, GEO, SERP, and community monitoring.</strong><br/>
  <sub>Built for open-source projects and developer products. See where your project is discovered, discussed, and compared — then turn those signals into reports, briefs, approvals, and actions.</sub>
</p>

<div align="center">
  <a href="README.md">English</a> | <a href="README_zh.md">中文</a> | <a href="README_ja.md">日本語</a> | <a href="README_ko.md">한국어</a> | <a href="README_es.md">Español</a>
</div>

<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg?style=for-the-badge&logo=python" alt="Python 3.10+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-green.svg?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/study8677/OpenCMO/stargazers"><img src="https://img.shields.io/github/stars/study8677/OpenCMO?style=for-the-badge&color=yellow&logo=github" alt="Stars"></a>
  <img src="https://img.shields.io/badge/react-SPA-61DAFB.svg?style=for-the-badge&logo=react" alt="React SPA">
</p>

<div align="center">
  <h3>
    <a href="https://www.bilibili.com/video/BV1T5AMzoEKV/">Watch Demo Video</a>
  </h3>
  <sub>Currently using OpenRouter's free qwen3.5free model.</sub>
</div>

---

<div align="center">
  <img src="assets/screenshots/knowledge-graph-demo.gif" alt="OpenCMO in action" width="850" />
  <p><i>Turn visibility signals into growth decisions from one open-source workspace.</i></p>
</div>

---

## Showcase: Real-World Example

See OpenCMO in action with a **real scan of [Cursor.com](https://cursor.com)** — 176 community discussions discovered across Reddit, Hacker News, Bilibili, Dev.to, and V2EX, with a 177-node knowledge graph.

**[View the Cursor showcase with full data](docs/showcase/cursor/)**

---

## What Makes OpenCMO Different

- **It treats growth as a system, not a checklist**: SEO, GEO, SERP, community discussion, competitors, reports, and approvals live in one loop.
- **It is built for open-source reality**: before you have a marketing team, you still need discovery, discussion, and credibility.
- **It helps you act on signals**: not just dashboards, but next actions, briefs, drafts, and human-in-the-loop approvals grounded in project context.

## What OpenCMO Helps You Do

- **See where your project is visible**: monitor search rankings, AI-search presence, community mentions, and crawler accessibility.
- **Understand who you are competing with**: map competitors, keyword overlap, and community context in the knowledge graph.
- **Prioritize what to do next**: identify the discussions to join, the keywords to push, and the content gaps worth closing.
- **Keep execution grounded**: generate reports, agent briefs, and approval-ready drafts from the same project context.

## The Growth Loop

1. **Scan a project URL** to extract brand, category, keywords, and early competitive context.
2. **Monitor SEO, GEO, SERP, and community signals** in one workspace.
3. **Turn raw signals into context** with reports, graph exploration, and AI chat grounded in project data.
4. **Move to execution** with drafts, approvals, and prioritized next actions.

## Core Capabilities

- **SEO Audit**: Core Web Vitals, `llms.txt`, AI crawler detection, and technical site health.
- **GEO Visibility**: monitor how your brand appears in AI-native search surfaces such as ChatGPT, Claude, Gemini, Perplexity, and You.com.
- **SERP Tracking**: track keyword rankings over time with crawl-based or provider-based checks.
- **Community Monitoring**: watch Reddit, Hacker News, Dev.to, YouTube, Bluesky, Twitter/X, plus Chinese platforms such as V2EX, Weibo, Bilibili, and XueQiu.
- **Knowledge Graph**: explore competitors, keywords, and community connections in one visual map.
- **Reports**: generate versioned strategic and weekly reports, with human readouts, agent briefs, PDF export, and email delivery.
- **Approvals and AI Chat**: keep humans in the loop while using project-aware AI agents to reason, summarize, and draft.

## Deep Reports

OpenCMO includes a report system inside each project workspace. Open the **Reports** tab or visit `/app/projects/<id>/reports`.

- **Strategic reports**: full-scan analysis with positioning, competitor context, risks, and recommendations.
- **Weekly reports**: 7-day monitoring summaries with trend changes, risks, wins, and next actions.
- **Dual outputs**: every report is stored as both a **Human Readout** and an **Agent Brief**.
- **Multi-agent pipeline**: human-facing reports use a 6-phase pipeline instead of a single prompt.
- **Graceful fallback**: if the deep pipeline fails, OpenCMO falls back to simpler generation paths so reports stay available.

## Quick Start

OpenCMO works with OpenAI-compatible APIs, including OpenAI, DeepSeek, NVIDIA NIM, Kimi-compatible gateways, and Ollama.

```bash
git clone https://github.com/study8677/OpenCMO.git
cd OpenCMO
pip install -e ".[all]"
crawl4ai-setup

cp .env.example .env
opencmo-web
```

Then open `http://localhost:8080/app`.

> Tip: you can also configure API keys from the web dashboard's **Settings** panel.

<details>
<summary>Frontend development (optional)</summary>

```bash
cd frontend
npm install
npm run dev
npm run build
```

The dev app runs at `http://localhost:5173/app` and proxies API traffic to `:8080`.

</details>

## Integrations

| Capability | Platforms | Auth |
| :--- | :--- | :--- |
| Monitoring | SEO, GEO, SERP, Community | Optional provider keys |
| Community sources (EN) | Reddit, HN, Dev.to, Bluesky, YouTube, Twitter/X | Optional |
| Community sources (CN) | V2EX, Weibo, Bilibili, XueQiu | Free (XueQiu needs cookie) |
| Community sources (stub) | XiaoHongShu, WeChat, Douyin | Pending (MCP/Docker) |
| Publishing | Reddit, Twitter/X | Required |
| Reports | Web + Email + PDF | SMTP for email |
| LLM providers | OpenAI-compatible APIs | Required |

## Roadmap

- [x] AI CMO strategic scan
- [x] SEO / GEO / SERP / community monitoring
- [x] Versioned strategic and weekly reports
- [x] Multi-agent deep report pipeline (6-phase)
- [x] PDF export with branded header/footer
- [x] 3D knowledge graph
- [x] Approval queue and controlled publishing
- [x] Chinese platform community monitoring (V2EX, Weibo, Bilibili, XueQiu)
- [x] Full i18n (English, Chinese, Japanese, Korean, Spanish)
- [x] Locale-aware AI responses (LLM follows UI language setting)
- [x] LLM retry with exponential backoff for unreliable providers
- [ ] More publishing targets
- [ ] Brand voice controls
- [ ] Deeper enterprise SEO crawls

## Contributors

- [study8677](https://github.com/study8677) - Creator and maintainer
- [ParakhJaggi](https://github.com/ParakhJaggi) - Tavily integration ([#2](https://github.com/study8677/OpenCMO/pull/2), [#3](https://github.com/study8677/OpenCMO/pull/3))
- See [CONTRIBUTORS.md](CONTRIBUTORS.md) for the full contributor list

## Acknowledgments

- [geo-seo-claude](https://github.com/zubair-trabzada/geo-seo-claude) by [@zubair-trabzada](https://github.com/zubair-trabzada)
- [last30days-skill](https://github.com/mvanhorn/last30days-skill) by [@mvanhorn](https://github.com/mvanhorn)
- [Agent-Reach](https://github.com/Panniantong/Agent-Reach) by [@Panniantong](https://github.com/Panniantong) — Chinese platform integration inspiration

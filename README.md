<div align="center">
  <img src="assets/logo.png" alt="OpenCMO Logo" width="120" />
</div>

<h1 align="center">OpenCMO</h1>

<p align="center">
  <strong>Paste your URL → get an AI CMO brief, continuous monitoring, and agent-ready marketing actions.</strong><br/>
  <sub>Open-source AI CMO for founders and lean teams. Monitor SEO, GEO, SERP, and community signals, understand competitors, brief your agents, and publish with approval.</sub>
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
    <a href="https://724claw.icu/app/">Try the Live Demo</a> · <a href="https://www.bilibili.com/video/BV1T5AMzoEKV/">Watch Demo Video</a>
  </h3>
  <sub>BYOK (Bring Your Own Key) — no login, and your API keys stay in your browser.</sub>
</div>

---

<div align="center">
  <img src="assets/screenshots/knowledge-graph-demo.gif" alt="OpenCMO in action" width="850" />
  <p><i>One workspace for monitoring, reporting, approvals, and competitive context.</i></p>
</div>

---

## Why OpenCMO

- **Start with a URL, not a setup project**: scan a site and get a CMO-level read on positioning, strengths, weaknesses, and competitive context.
- **Keep the signal loop running**: monitor SEO, GEO, SERP, and community changes in one place.
- **Turn insight into execution**: generate agent briefs, approval-ready content drafts, and weekly summaries without switching tools.

## What You Get

- **AI CMO strategy**: an initial strategic read after a full scan.
- **Continuous monitoring**: SEO health, AI-search visibility, keyword rankings, and community mentions.
- **Competitive context**: a live 3D knowledge graph connecting competitors, keywords, and communities.
- **Execution surface**: AI chat, approval queue, and publishable drafts for multiple platforms.

## AI CMO Reports

OpenCMO now includes a formal report system inside each project workspace. Open the **Reports** tab or visit `/app/projects/<id>/reports`.

### Multi-Agent Deep Report Pipeline

Human-facing reports are generated through a **6-phase multi-agent pipeline** (~14 LLM calls) instead of a single prompt. This produces McKinsey-grade analysis with cross-validated data, evidence-based reasoning, and iterative quality control.

| Phase | Role | What it does |
| :--- | :--- | :--- |
| 1. Reflection Agent | Quality Auditor | Cross-validates all agent data, flags anomalies and gaps |
| 2. Insight Distiller | Analyst | Extracts analytical insights with cross-dimensional correlations |
| 3. Outline Planner | Editor-in-Chief | Plans narrative arc with per-section thesis and evidence mapping |
| 4. Section Writers | Authors (parallel) | Write each section concurrently with focused context |
| 5. Section Grader | Reviewer | Scores each section 1-5, rejects and retries below threshold |
| 6. Report Synthesizer | Managing Editor | Writes executive summary, intro, strategic recommendations |

- **Strategic Report**: generated after a full scan — deep competitive analysis, risk assessment, and CMO-level strategic recommendations.
- **Weekly Report**: generated from the latest 7-day monitoring window — trend analysis, risk/win highlights, and next-week action plan.
- **Dual outputs**: every report is stored as both a **Human Readout** (deep analysis) and an **Agent Brief** (concise action items).
- **PDF export**: download branded PDF reports with logo header and footer.
- **Version history**: reports are retained and viewable as historical versions.
- **Email delivery**: weekly email uses the same persisted report content you see in the product.
- **Graceful fallback**: pipeline failures automatically fall back to single-call → template generation.

## Core Product Surface

- **SEO Audit**: Core Web Vitals, llms.txt validation, AI crawler detection, technical site health.
- **GEO Visibility**: track how your brand appears in AI-native search surfaces such as ChatGPT, Claude, Gemini, Perplexity, and You.com.
- **SERP Tracking**: monitor rankings over time with crawler-based or DataForSEO-based checks.
- **Community Monitoring**: watch Reddit, Hacker News, Dev.to, YouTube, Bluesky, and Twitter/X for relevant mentions and discussions.
- **AI Chat**: talk to 25+ specialist agents with project-aware context.
- **Approval Queue**: review exact publishing payloads before anything goes live.
- **3D Knowledge Graph**: explore competitors, keywords, and communities in one visual map.

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
| Community sources | Reddit, HN, Dev.to, Bluesky, YouTube, Twitter/X | Optional |
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

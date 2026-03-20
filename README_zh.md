<div align="center">
  <img src="assets/logo.png" alt="OpenCMO Logo" width="120" />
</div>

<h1 align="center">OpenCMO</h1>

<p align="center">
  <strong>开源 AI CMO —— 一个工具就是你的整个营销团队。</strong><br/>
  <sub>10 个 AI 专家智能体、实时监控、现代化 Web 仪表盘。</sub>
</p>

<div align="center">
  <a href="README.md">🇺🇸 English</a> | <a href="README_zh.md">🇨🇳 中文</a> | <a href="README_ja.md">🇯🇵 日本語</a> | <a href="README_ko.md">🇰🇷 한국어</a> | <a href="README_es.md">🇪🇸 Español</a>
</div>

<div align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg?style=flat-square" alt="Python 3.10+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-green.svg?style=flat-square" alt="License"></a>
  <a href="https://github.com/study8677/OpenCMO/stargazers"><img src="https://img.shields.io/github/stars/study8677/OpenCMO?style=flat-square&color=yellow" alt="Stars"></a>
</div>

---

## 截图

<div align="center">
  <img src="assets/screenshots/dashboard.svg" alt="仪表盘" width="700" />
  <br/><sub>项目仪表盘 — SEO、GEO、社区和 SERP 评分一览</sub>
</div>
<br/>
<div align="center">
  <img src="assets/screenshots/chat-agents.svg" alt="AI 对话与智能体选择" width="700" />
  <br/><sub>与 10 个 AI 专家对话 — 选一个或让 CMO 自动分配</sub>
</div>
<br/>
<div align="center">
  <img src="assets/screenshots/monitor-analysis.svg" alt="多智能体分析" width="700" />
  <br/><sub>多智能体策略讨论：3 角色 × 3 轮 → 关键词和监控方案</sub>
</div>

---

## OpenCMO 是什么？

OpenCMO 是一个**多智能体 AI 营销系统**，专为独立开发者和小团队设计。输入一个 URL，系统会爬取网站、运行多智能体策略讨论，自动设置 SEO、AI 可见度和社区讨论的监控。

### 核心能力

- **10 个 AI 专家智能体** — Twitter/X、Reddit、LinkedIn、Product Hunt、Hacker News、博客/SEO、SEO 审计、GEO（AI 可见度）、社区监控、CMO 总管
- **智能 URL 分析** — 粘贴任意 URL，3 个 AI 角色（产品分析师、SEO 专家、社区运营）进行 3 轮讨论，提取品牌名、分类和监控关键词
- **实时 Web 仪表盘** — React SPA，暗色侧边栏、项目卡片、趋势图表、中英双语
- **与专家对话** — ChatGPT 风格界面，支持历史记录；选择特定智能体或让 CMO 自动路由
- **持续监控** — 基于 Cron 的定时扫描 SEO、GEO 和社区指标
- **任意 LLM 供应商** — OpenAI、NVIDIA NIM、DeepSeek、Ollama 或任何 OpenAI 兼容 API

## 快速开始

### 1. 安装

```bash
git clone https://github.com/study8677/OpenCMO.git
cd OpenCMO
pip install -e ".[all]"
crawl4ai-setup
```

### 2. 配置

```bash
cp .env.example .env
# 编辑 .env — 设置 API 密钥（见 .env.example 中的示例）
```

### 3. 运行

```bash
opencmo-web                # Web 仪表盘 → http://localhost:8080/app
opencmo                    # 命令行交互模式
```

### 4. 使用

1. 进入 **监控** → 粘贴 URL → 点击 **开始监控**
2. 实时观看 AI 多智能体讨论分析
3. 系统自动提取品牌名、分类和关键词
4. 自动运行全面扫描（SEO + GEO + 社区）
5. 在 **仪表盘** 查看结果

## 🤖 10 个 AI 专家智能体

| 智能体 | 功能 |
|--------|------|
| **CMO 总管** | 总体协调，自动路由到合适的专家 |
| **Twitter/X** | 推文、话题串和互动策略 |
| **Reddit** | 社区风格的真实帖子 |
| **LinkedIn** | 专业的行业领导力内容 |
| **Product Hunt** | 上线文案、标语和制作者评论 |
| **Hacker News** | 技术向的 Show HN 帖子 |
| **博客/SEO** | SEO 优化长文（2000+ 字） |
| **SEO 审计** | 核心 Web 指标、Schema.org、robots/sitemap |
| **GEO** | Perplexity、You.com、ChatGPT、Claude、Gemini 品牌提及 |
| **社区监控** | Reddit、HN、Dev.to 讨论扫描 |

## 🎯 智能 URL 分析

| 轮次 | 内容 |
|------|------|
| **第一轮** | 各角色初步分析（产品定位、SEO 关键词、社区话题） |
| **第二轮** | 基于其他角色的分析完善建议 |
| **第三轮** | 策略总监汇总 → 品牌名 + 分类 + 5-8 个关键词 |

## 🔧 灵活配置

支持 OpenAI、NVIDIA NIM、DeepSeek、Ollama 等任意 OpenAI 兼容 API。详见 `.env.example`。

## 许可证

Apache License 2.0

---

<div align="center">
  <sub>如果 OpenCMO 对你有帮助，给个 ⭐ 吧！</sub>
</div>

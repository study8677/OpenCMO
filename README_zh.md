<div align="center">
  <img src="assets/logo.png" alt="OpenCMO Logo" width="120" />
</div>

<h1 align="center">OpenCMO</h1>

<p align="center">
  <strong>OpenCMO 是把 SEO、GEO、SERP 和社区监控整合在一起的开源增长系统。</strong><br/>
  <sub>面向开源项目和开发者产品。让你看清项目在哪里被发现、被讨论、被比较，然后把这些信号转成报告、Brief、审批和行动。</sub>
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
    <a href="https://www.bilibili.com/video/BV1T5AMzoEKV/">观看演示视频</a>
  </h3>
  <sub>当前使用的是 OpenRouter 免费的 qwen3.5free 模型。</sub>
</div>

---

<div align="center">
  <img src="assets/screenshots/knowledge-graph-demo.gif" alt="OpenCMO 实战演示" width="850" />
  <p><i>在一个开源工作区里，把可见性信号变成增长决策。</i></p>
</div>

---

## 实战展示：真实案例

通过一次**对 [Cursor.com](https://cursor.com) 的真实扫描**，体验 OpenCMO 的实际效果：在 Reddit、Hacker News、Bilibili、Dev.to 和 V2EX 上发现了 176 条社区讨论，并生成了 177 节点的知识图谱。

**[查看 Cursor 完整数据展示](docs/showcase/cursor/)**

---

## OpenCMO 有什么不一样

- **它把增长当成系统，而不是零散任务**：SEO、GEO、SERP、社区讨论、竞品、报告和审批都在同一个闭环里。
- **它是为开源项目的现实处境设计的**：在你拥有营销团队之前，你已经需要被发现、被讨论、被建立信任。
- **它不只展示数据，还帮你行动**：把信号变成下一步动作、Brief、草稿和 human-in-the-loop 审批。

## OpenCMO 实际帮你做什么

- **看清项目的可见性**：监控搜索排名、AI 搜索表现、社区提及和爬虫可达性。
- **理解竞争格局**：在知识图谱里查看竞品、关键词重叠和社区上下文。
- **判断下一步该做什么**：找到最值得参与的讨论、最值得打的关键词和最该补的内容空白。
- **让执行建立在真实上下文之上**：从同一套项目上下文生成报告、Agent Brief 和待审批草稿。

## 增长闭环

1. **扫描项目 URL**，提取品牌、类别、关键词和初始竞品上下文。
2. **持续监控 SEO、GEO、SERP 和社区信号**。
3. **把原始信号转成上下文**，通过报告、知识图谱和项目感知 AI 对话理解发生了什么。
4. **进入执行环节**，产出草稿、审批项和优先级明确的下一步动作。

## 核心能力

- **SEO 审计**：Core Web Vitals、`llms.txt`、AI 爬虫检测、技术健康度。
- **GEO 可见度**：监控品牌在 ChatGPT、Claude、Gemini、Perplexity、You.com 等 AI 搜索场景中的表现。
- **SERP 追踪**：持续追踪关键词排名变化。
- **社区监控**：覆盖 Reddit、Hacker News、Dev.to、YouTube、Bluesky、Twitter/X，以及 V2EX、微博、B 站、雪球等中文平台。
- **知识图谱**：在一个可视化界面里探索竞品、关键词和社区连接关系。
- **报告系统**：生成版本化战略报告和周报，支持 Human Readout、Agent Brief、PDF 导出和邮件发送。
- **审批与 AI 对话**：在保持人工审核的前提下，使用项目上下文驱动的 AI agent 做分析、总结和起草。

## 深度报告

OpenCMO 已经内置正式报告系统。你可以在项目中打开 **Reports** 标签页，或直接访问 `/app/projects/<id>/reports`。

- **战略报告**：完整扫描后的定位、竞品格局、风险和建议。
- **周报**：最近 7 天的监控变化、风险、亮点和下一步动作。
- **双版本输出**：每份报告同时保存为 **Human Readout** 和 **Agent Brief**。
- **多智能体管线**：面向人的报告使用 6 阶段管线，而不是单次 prompt。
- **优雅降级**：深度管线失败时，会自动回退到更简单的生成路径，确保报告始终可用。

## 快速开始

OpenCMO 兼容 OpenAI 协议 API，包括 OpenAI、DeepSeek、NVIDIA NIM、Kimi 兼容网关、Ollama 等。

```bash
git clone https://github.com/study8677/OpenCMO.git
cd OpenCMO
pip install -e ".[all]"
crawl4ai-setup

cp .env.example .env
opencmo-web
```

然后打开 `http://localhost:8080/app`。

> 提示：也可以直接在 Web 仪表盘的 **Settings** 面板里配置 API Key。

<details>
<summary>前端开发（可选）</summary>

```bash
cd frontend
npm install
npm run dev
npm run build
```

开发态地址为 `http://localhost:5173/app`，会自动把 API 代理到 `:8080`。

</details>

## 平台接入

| 能力 | 平台 | 认证 |
| :--- | :--- | :--- |
| 监控 | SEO、GEO、SERP、Community | 可选 provider key |
| 社区来源（英文） | Reddit、HN、Dev.to、Bluesky、YouTube、Twitter/X | 可选 |
| 社区来源（中文） | V2EX、微博、B 站、雪球 | 免费（雪球需 Cookie） |
| 社区来源（预留） | 小红书、微信公众号、抖音 | 待实现（需 MCP/Docker） |
| 发布 | Reddit、Twitter/X | 必需 |
| 报告 | Web + 邮件 + PDF | 邮件需要 SMTP |
| LLM | OpenAI 兼容 API | 必需 |

## 路线图

- [x] AI CMO 战略扫描
- [x] SEO / GEO / SERP / 社区监控
- [x] 版本化战略报告与周报
- [x] 多智能体深度报告管线（6 阶段）
- [x] 带品牌标识的 PDF 导出
- [x] 3D 知识图谱
- [x] 审批流与受控发布
- [x] 中文社区平台监控（V2EX、微博、B 站、雪球）
- [x] 完整国际化支持（英语、中文、日语、韩语、西班牙语）
- [x] 语言感知 AI 响应（LLM 跟随 UI 语言设置）
- [x] LLM 指数退避重试（适配不稳定 provider）
- [ ] 更多发布平台
- [ ] 品牌声音控制
- [ ] 更深度的企业级 SEO 爬取

## 贡献者

- [study8677](https://github.com/study8677) - 创建者与维护者
- [ParakhJaggi](https://github.com/ParakhJaggi) - Tavily 集成 ([#2](https://github.com/study8677/OpenCMO/pull/2), [#3](https://github.com/study8677/OpenCMO/pull/3))
- 完整名单见 [CONTRIBUTORS.md](CONTRIBUTORS.md)

## 致谢

- [geo-seo-claude](https://github.com/zubair-trabzada/geo-seo-claude) by [@zubair-trabzada](https://github.com/zubair-trabzada)
- [last30days-skill](https://github.com/mvanhorn/last30days-skill) by [@mvanhorn](https://github.com/mvanhorn)
- [Agent-Reach](https://github.com/Panniantong/Agent-Reach) by [@Panniantong](https://github.com/Panniantong) — 中文平台集成灵感来源

<div align="center">
  <img src="assets/logo.png" alt="OpenCMO Logo" width="120" />
</div>

<h1 align="center">OpenCMO</h1>

<p align="center">
  <strong>粘贴你的网址 → 直接拿到 AI CMO 战略判断、持续监控和可执行 Agent Brief。</strong><br/>
  <sub>面向创始人和精简团队的开源 AI CMO。统一管理 SEO、GEO、SERP、社区信号、竞品上下文、报告、审批和发布。</sub>
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
    <a href="https://724claw.icu/app/">在线体验</a> · <a href="https://www.bilibili.com/video/BV1T5AMzoEKV/">观看演示视频</a>
  </h3>
  <sub>BYOK（自带 Key）模式，无需注册，API 密钥仅保存在你的浏览器中。</sub>
</div>

---

<div align="center">
  <img src="assets/screenshots/knowledge-graph-demo.gif" alt="OpenCMO 实战演示" width="850" />
  <p><i>一个工作区看完监控、报告、审批和竞品关系。</i></p>
</div>

---

## 为什么是 OpenCMO

- **从网址直接开始**：一次完整扫描后，先拿到 CMO 级项目定位和市场判断，而不是先做一堆配置。
- **把信号放在一个闭环里**：SEO、GEO、SERP、社区动态统一监控。
- **把判断直接交给执行系统**：报告、Agent Brief、审批队列、发布草稿连成一体。

## 你实际会得到什么

- **战略判断**：项目定位、优势、短板、竞品格局、CMO 建议。
- **持续监控**：SEO 健康度、AI 搜索可见度、关键词排名、社区提及。
- **竞品上下文**：3D 知识图谱连接竞品、关键词、社区。
- **执行界面**：AI 对话、审批流、可发布内容草稿。

## AI CMO 报告系统

OpenCMO 现在已经内置正式报告系统。你可以在项目内打开 **Reports** 标签页，或直接访问 `/app/projects/<id>/reports`。

### 多智能体深度报告管线

面向人类读者的报告通过 **6 阶段多智能体管线**（约 14 次 LLM 调用）生成，而非单次 prompt。这会产出具有交叉验证、证据推理和迭代质控的深度商业分析。

| 阶段 | 角色 | 职责 |
| :--- | :--- | :--- |
| 1. Reflection Agent | 质检官 | 交叉验证所有 Agent 数据，标记异常和缺口 |
| 2. Insight Distiller | 分析师 | 提炼跨维度关联洞察 |
| 3. Outline Planner | 主编 | 规划叙事弧线，为每节分配论点和证据 |
| 4. Section Writers | 撰稿人（并行） | 并行写作各章节，上下文聚焦 |
| 5. Section Grader | 审稿人 | 1-5 分评审，低于阈值打回重写 |
| 6. Report Synthesizer | 总编 | 撰写执行摘要、引言和战略建议 |

- **战略报告**：完整扫描后生成——深度竞品分析、风险评估、CMO 级战略建议。
- **周报**：基于最近 7 天监控窗口——趋势分析、风险/亮点、下周行动计划。
- **双版本输出**：每份报告同时保存为 **Human Readout**（深度分析）和 **Agent Brief**（简明行动项）。
- **PDF 导出**：下载带有品牌 Logo 页眉和页脚的专业 PDF 报告。
- **版本历史**：所有报告保留历史版本，支持查看 latest 和历史记录。
- **邮件投递**：周报邮件直接复用系统内看到的那份周期报告内容。
- **优雅降级**：管线失败自动降级为单次调用 → 模板生成，确保报告永远可用。

## 核心产品面

- **SEO 审计**：Core Web Vitals、llms.txt、AI 爬虫检测、技术健康度。
- **GEO 可见度**：追踪品牌在 ChatGPT、Claude、Gemini、Perplexity、You.com 等 AI 搜索场景中的表现。
- **SERP 追踪**：长期监控关键词排名变化。
- **社区监控**：扫描 Reddit、Hacker News、Dev.to、YouTube、Bluesky、Twitter/X。
- **AI 对话**：与 25+ 专家智能体在项目上下文中协作。
- **审批队列**：任何内容发布前先审再发。
- **3D 知识图谱**：可视化探索竞品、关键词和社区关系。

## 快速开始

兼容 OpenAI 协议 API，包括 OpenAI、DeepSeek、NVIDIA NIM、Kimi 兼容网关、Ollama 等。

```bash
git clone https://github.com/study8677/OpenCMO.git
cd OpenCMO
pip install -e ".[all]"
crawl4ai-setup

cp .env.example .env
opencmo-web
```

然后打开 `http://localhost:8080/app`。

> 提示：也可以在 Web 仪表盘的 **Settings** 面板里直接配置 API Key。

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
| 社区来源 | Reddit、HN、Dev.to、Bluesky、YouTube、Twitter/X | 可选 |
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

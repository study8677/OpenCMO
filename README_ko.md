<div align="center">
  <img src="assets/logo.png" alt="OpenCMO Logo" width="120" />
</div>

<h1 align="center">OpenCMO</h1>

<p align="center">
  <strong>오픈소스 AI CMO — 하나의 도구로 전체 마케팅 팀을 대체합니다.</strong><br/>
  <sub>10개의 AI 전문가 에이전트, 실시간 모니터링, 모던 웹 대시보드.</sub>
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

## 스크린샷

<div align="center">
  <img src="assets/screenshots/dashboard.svg" alt="대시보드" width="700" />
  <br/><sub>프로젝트 대시보드 — SEO, GEO, 커뮤니티, SERP 점수</sub>
</div>
<br/>
<div align="center">
  <img src="assets/screenshots/chat-agents.svg" alt="AI 채팅" width="700" />
  <br/><sub>10명의 AI 전문가와 채팅 — 선택하거나 CMO가 자동 라우팅</sub>
</div>
<br/>
<div align="center">
  <img src="assets/screenshots/monitor-analysis.svg" alt="멀티 에이전트 분석" width="700" />
  <br/><sub>멀티 에이전트 전략 토론: 3역할 × 3라운드 → 키워드 및 모니터링 계획</sub>
</div>

---

## OpenCMO란?

인디 개발자와 소규모 팀을 위한 **멀티 에이전트 AI 마케팅 시스템**입니다. URL을 입력하면 사이트를 크롤링하고, 멀티 에이전트 전략 토론을 실행하며, SEO·AI 가시성·커뮤니티 모니터링을 자동 설정합니다.

## 빠른 시작

```bash
git clone https://github.com/study8677/OpenCMO.git
cd OpenCMO
pip install -e ".[all]"
crawl4ai-setup
cp .env.example .env  # API 키 설정
opencmo-web           # → http://localhost:8080/app
```

## 🤖 10개의 AI 전문가

| 에이전트 | 기능 |
|---------|------|
| **CMO Agent** | 전체 조율, 적절한 전문가에게 자동 라우팅 |
| **Twitter/X** | 트윗, 스레드 |
| **Reddit** | 커뮤니티 게시글 |
| **LinkedIn** | 전문 콘텐츠 |
| **Product Hunt** | 런칭 카피 |
| **Hacker News** | Show HN 게시글 |
| **Blog/SEO** | SEO 최적화 글 |
| **SEO 감사** | Core Web Vitals, Schema.org 분석 |
| **GEO** | AI 검색엔진 브랜드 언급 체크 |
| **커뮤니티** | Reddit/HN/Dev.to 토론 스캔 |

## 라이선스

Apache License 2.0

---

<div align="center">
  <sub>OpenCMO가 도움이 되셨다면 ⭐ 부탁드립니다!</sub>
</div>

<div align="center">
  <img src="assets/logo.png" alt="OpenCMO Logo" width="120" />
</div>

<h1 align="center">OpenCMO</h1>

<p align="center">
  <strong>URLを貼るだけ → AI CMOの戦略判断、継続監視、Agent Brief をすぐ取得。</strong><br/>
  <sub>Founder と少人数チーム向けのオープンソース AI CMO。SEO、GEO、SERP、コミュニティ、競合文脈、レポート、承認、公開を1つのワークスペースに集約します。</sub>
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
    <a href="https://724claw.icu/app/">ライブデモを試す</a> · <a href="https://www.bilibili.com/video/BV1T5AMzoEKV/">デモ動画を視聴</a>
  </h3>
  <sub>BYOK（Bring Your Own Key）対応。ログイン不要で、API キーはブラウザ内だけに保存されます。</sub>
</div>

---

<div align="center">
  <img src="assets/screenshots/knowledge-graph-demo.gif" alt="OpenCMO 実演" width="850" />
  <p><i>監視、レポート、承認、競合文脈を1つの画面で確認できます。</i></p>
</div>

---

## OpenCMO が分かりやすい理由

- **URL から始める**: full scan のあとに、まず CMO レベルの市場判断が返ってきます。
- **シグナルを一か所で回す**: SEO、GEO、SERP、コミュニティ変化を同時に監視します。
- **判断を実行に渡す**: レポート、Agent Brief、承認キュー、公開ドラフトまでつながっています。

## 何が手に入るか

- **戦略判断**: ポジショニング、強み、弱み、競争環境、CMO 提案。
- **継続監視**: SEO 健全性、AI 検索可視性、キーワード順位、コミュニティ言及。
- **競合文脈**: 競合、キーワード、コミュニティをつなぐ 3D ナレッジグラフ。
- **実行面**: AI Chat、承認フロー、公開可能なドラフト。

## AI CMO レポート

OpenCMO にはプロジェクトごとの正式なレポート機能があります。**Reports** タブ、または `/app/projects/<id>/reports` から確認できます。

### マルチエージェント深層レポートパイプライン

人間向けレポートは、単一プロンプトの代わりに **6 段階のマルチエージェントパイプライン**（約 14 回の LLM 呼び出し）で生成されます。

| 段階 | 役割 | 機能 |
| :--- | :--- | :--- |
| 1. Reflection Agent | 品質監査官 | 全 Agent データを交差検証し、異常とギャップを検出 |
| 2. Insight Distiller | アナリスト | 次元横断の分析的洞察を抽出 |
| 3. Outline Planner | 編集長 | 論旨と証拠マッピングで物語構成を設計 |
| 4. Section Writers | 著者（並列） | 各セクションを並列執筆 |
| 5. Section Grader | 査読者 | 各セクションを 1-5 で採点、閾値未満は再執筆 |
| 6. Report Synthesizer | 総編集 | エグゼクティブサマリー、序論、戦略提案を執筆 |

- **Strategic Report**: full scan 後に生成 — 深層競合分析、リスク評価、CMO レベルの戦略提案。
- **Weekly Report**: 直近 7 日の監視ウィンドウ — トレンド分析、リスク/成果、次週アクション計画。
- **二層出力**: **Human Readout**（深層分析）と **Agent Brief**（簡潔なアクション項目）。
- **PDF エクスポート**: ブランドロゴ入りヘッダー/フッター付きの PDF をダウンロード。
- **バージョン履歴**: latest と履歴の両方を参照できます。
- **メール配信**: 週次メールは、画面上と同じ保存済みレポートを再利用します。
- **グレースフル・フォールバック**: パイプライン障害時は自動的にシングルコール → テンプレート生成に降格。

## コア機能

- **SEO Audit**: Core Web Vitals、llms.txt、AI crawler 検出、技術健全性。
- **GEO Visibility**: ChatGPT、Claude、Gemini、Perplexity、You.com などでの見え方を追跡。
- **SERP Tracking**: キーワード順位の推移を監視。
- **Community Monitoring**: Reddit、Hacker News、Dev.to、YouTube、Bluesky、Twitter/X を監視。
- **AI Chat**: 25 以上の専門エージェントとプロジェクト文脈付きで対話。
- **Approval Queue**: 公開前に内容を確認。
- **3D Knowledge Graph**: 競合、キーワード、コミュニティを可視化。

## クイックスタート

OpenAI 互換 API を利用できます。OpenAI、DeepSeek、NVIDIA NIM、Kimi 互換ゲートウェイ、Ollama などに対応します。

```bash
git clone https://github.com/study8677/OpenCMO.git
cd OpenCMO
pip install -e ".[all]"
crawl4ai-setup

cp .env.example .env
opencmo-web
```

その後 `http://localhost:8080/app` を開きます。

> ヒント: API キーは Web ダッシュボードの **Settings** からも設定できます。

<details>
<summary>フロントエンド開発（任意）</summary>

```bash
cd frontend
npm install
npm run dev
npm run build
```

開発用アプリは `http://localhost:5173/app` で動作し、API は `:8080` にプロキシされます。

</details>

## 連携

| 機能 | プラットフォーム | 認証 |
| :--- | :--- | :--- |
| 監視 | SEO、GEO、SERP、Community | 任意の provider key |
| コミュニティソース | Reddit、HN、Dev.to、Bluesky、YouTube、Twitter/X | 任意 |
| 公開 | Reddit、Twitter/X | 必須 |
| レポート | Web + Email + PDF | メールは SMTP 必須 |
| LLM | OpenAI 互換 API | 必須 |

## ロードマップ

- [x] AI CMO 戦略スキャン
- [x] SEO / GEO / SERP / コミュニティ監視
- [x] バージョン管理された戦略レポートと週報
- [x] マルチエージェント深層レポートパイプライン（6 段階）
- [x] ブランド付き PDF エクスポート
- [x] 3D ナレッジグラフ
- [x] 承認フローと制御付き公開
- [ ] 公開先の追加
- [ ] ブランドボイス制御
- [ ] より深い企業向け SEO クロール

## Contributors

- [study8677](https://github.com/study8677) - Creator and maintainer
- [ParakhJaggi](https://github.com/ParakhJaggi) - Tavily integration ([#2](https://github.com/study8677/OpenCMO/pull/2), [#3](https://github.com/study8677/OpenCMO/pull/3))
- 詳細は [CONTRIBUTORS.md](CONTRIBUTORS.md) を参照

## Acknowledgments

- [geo-seo-claude](https://github.com/zubair-trabzada/geo-seo-claude) by [@zubair-trabzada](https://github.com/zubair-trabzada)
- [last30days-skill](https://github.com/mvanhorn/last30days-skill) by [@mvanhorn](https://github.com/mvanhorn)

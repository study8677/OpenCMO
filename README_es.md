<div align="center">
  <img src="assets/logo.png" alt="OpenCMO Logo" width="120" />
</div>

<h1 align="center">OpenCMO</h1>

<p align="center">
  <strong>Pega tu URL → obtén un brief de AI CMO, monitoreo continuo y acciones listas para tus agentes.</strong><br/>
  <sub>AI CMO open source para founders y equipos pequeños. Unifica SEO, GEO, SERP, señales de comunidad, contexto competitivo, reportes, aprobaciones y publicación.</sub>
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
    <a href="https://724claw.icu/app/">Probar Demo en Vivo</a> · <a href="https://www.bilibili.com/video/BV1T5AMzoEKV/">Ver Video Demo</a>
  </h3>
  <sub>BYOK (Trae Tu Propia Clave): sin login y con claves API guardadas solo en tu navegador.</sub>
</div>

---

<div align="center">
  <img src="assets/screenshots/knowledge-graph-demo.gif" alt="OpenCMO en acción" width="850" />
  <p><i>Un solo workspace para monitoreo, reportes, aprobaciones y contexto competitivo.</i></p>
</div>

---

## Por Qué OpenCMO

- **Empieza desde una URL**: tras un full scan recibes una lectura de nivel CMO sobre posicionamiento y mercado.
- **Mantiene el loop de señales activo**: SEO, GEO, SERP y comunidad en un solo lugar.
- **Convierte insight en ejecución**: reportes, agent briefs, cola de aprobación y borradores publicables conectados.

## Qué Obtienes

- **Estrategia inicial**: posicionamiento, fortalezas, debilidades, competencia y recomendación CMO.
- **Monitoreo continuo**: salud SEO, visibilidad en buscadores IA, rankings de keywords y menciones de comunidad.
- **Contexto competitivo**: grafo de conocimiento 3D con competidores, keywords y comunidades.
- **Superficie de ejecución**: AI chat, aprobaciones y borradores para publicar.

## Reportes AI CMO

OpenCMO ya incluye un sistema formal de reportes dentro de cada proyecto. Abre la pestaña **Reports** o visita `/app/projects/<id>/reports`.

### Pipeline Multi-Agente de Reportes Profundos

Los reportes para personas se generan a través de un **pipeline de 6 fases multi-agente** (~14 llamadas LLM) en vez de un solo prompt. Esto produce análisis de nivel McKinsey con datos validados cruzadamente y control de calidad iterativo.

| Fase | Rol | Función |
| :--- | :--- | :--- |
| 1. Reflection Agent | Auditor de calidad | Valida cruzadamente datos de todos los Agents |
| 2. Insight Distiller | Analista | Extrae insights analíticos multi-dimensionales |
| 3. Outline Planner | Editor en Jefe | Diseña arco narrativo con tesis y evidencias |
| 4. Section Writers | Autores (paralelo) | Escriben secciones en paralelo |
| 5. Section Grader | Revisor | Puntua 1-5, rechaza y reintenta bajo umbral |
| 6. Report Synthesizer | Editor General | Escribe resumen ejecutivo, intro y estrategia |

- **Strategic Report**: tras un full scan — análisis competitivo profundo, evaluación de riesgos, recomendaciones estratégicas CMO.
- **Weekly Report**: ventana de 7 días — análisis de tendencias, riesgos/logros, plan de acción.
- **Salida dual**: **Human Readout** (análisis profundo) y **Agent Brief** (acciones concisas).
- **Exportar PDF**: descarga PDFs con logo de marca en header y footer.
- **Historial de versiones**: puedes ver latest e histórico.
- **Email**: el correo semanal reutiliza el mismo reporte persistido.
- **Fallback elegante**: fallos del pipeline degradan automáticamente a llamada única → plantilla.

## Superficie Principal del Producto

- **SEO Audit**: Core Web Vitals, llms.txt, crawlers IA y salud técnica.
- **GEO Visibility**: seguimiento en ChatGPT, Claude, Gemini, Perplexity y You.com.
- **SERP Tracking**: evolución de rankings en el tiempo.
- **Community Monitoring**: Reddit, Hacker News, Dev.to, YouTube, Bluesky y Twitter/X.
- **AI Chat**: 25+ agentes especialistas con contexto del proyecto.
- **Approval Queue**: revisa antes de publicar.
- **3D Knowledge Graph**: explora competidores, keywords y comunidades.

## Inicio Rápido

Compatible con APIs tipo OpenAI, incluyendo OpenAI, DeepSeek, NVIDIA NIM, gateways compatibles con Kimi y Ollama.

```bash
git clone https://github.com/study8677/OpenCMO.git
cd OpenCMO
pip install -e ".[all]"
crawl4ai-setup

cp .env.example .env
opencmo-web
```

Luego abre `http://localhost:8080/app`.

> Consejo: también puedes configurar las claves API desde el panel **Settings** del dashboard.

<details>
<summary>Desarrollo frontend (opcional)</summary>

```bash
cd frontend
npm install
npm run dev
npm run build
```

La app de desarrollo corre en `http://localhost:5173/app` y proxya la API a `:8080`.

</details>

## Integraciones

| Capacidad | Plataformas | Auth |
| :--- | :--- | :--- |
| Monitoreo | SEO, GEO, SERP, Community | Keys opcionales |
| Fuentes de comunidad | Reddit, HN, Dev.to, Bluesky, YouTube, Twitter/X | Opcional |
| Publicación | Reddit, Twitter/X | Obligatoria |
| Reportes | Web + Email + PDF | SMTP para email |
| LLM | APIs compatibles con OpenAI | Obligatoria |

## Roadmap

- [x] Escaneo estratégico AI CMO
- [x] Monitoreo SEO / GEO / SERP / comunidad
- [x] Reportes estratégicos y semanales versionados
- [x] Pipeline multi-agente de reportes profundos (6 fases)
- [x] Exportar PDF con marca
- [x] Grafo de conocimiento 3D
- [x] Aprobaciones y publicación controlada
- [ ] Más destinos de publicación
- [ ] Control de brand voice
- [ ] Crawls SEO enterprise más profundos

## Contributors

- [study8677](https://github.com/study8677) - Creador y maintainer
- [ParakhJaggi](https://github.com/ParakhJaggi) - Integración Tavily ([#2](https://github.com/study8677/OpenCMO/pull/2), [#3](https://github.com/study8677/OpenCMO/pull/3))
- Ver [CONTRIBUTORS.md](CONTRIBUTORS.md) para la lista completa

## Acknowledgments

- [geo-seo-claude](https://github.com/zubair-trabzada/geo-seo-claude) by [@zubair-trabzada](https://github.com/zubair-trabzada)
- [last30days-skill](https://github.com/mvanhorn/last30days-skill) by [@mvanhorn](https://github.com/mvanhorn)

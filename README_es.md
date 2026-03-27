<div align="center">
  <img src="assets/logo.png" alt="OpenCMO Logo" width="120" />
</div>

<h1 align="center">OpenCMO</h1>

<p align="center">
  <strong>El CMO de IA de Codigo Abierto — Tu Equipo de Marketing Completo en Una Sola Herramienta.</strong><br/>
  <sub>Un potente sistema multiagente con mas de 25 expertos de IA, monitoreo continuo de SEO/GEO/SERP/Comunidad, una cola de aprobaciones con payload exacto y un grafo de conocimiento 3D interactivo.</sub>
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

---

## Que es OpenCMO?

OpenCMO es un **ecosistema de marketing de IA multiagente** disenado para indie hackers, startups y equipos pequenos. Solo proporciona la URL de tu producto y OpenCMO:

1. **Analiza tu sitio web en profundidad** — Comprende tu producto y audiencia objetivo.
2. **Orquesta un debate estrategico multiagente** — Identifica las mejores palabras clave, posicionamiento y comunidades objetivo.
3. **Automatiza el monitoreo continuo** — Cubre SEO, visibilidad en busqueda IA (GEO), rankings SERP y comunidades de desarrolladores (Reddit, Hacker News, Dev.to).
4. **Genera contenido para mas de 20 plataformas** — Con revision del payload exacto en una cola de aprobaciones y publicacion automatica en Reddit y Twitter cuando tu lo autorizas.

---

## Por que OpenCMO destaca

- **Une generacion y medicion en un solo bucle** — agentes de contenido, monitoreo SEO/GEO/SERP/comunidad y el grafo 3D trabajan sobre la misma superficie operativa.
- **El scheduler ya vive en el ciclo de vida del dashboard web** — si `opencmo-web` esta activo, los monitores con cron tambien siguen activos.
- **La cola de aprobaciones guarda el payload exacto** — lo que revisas es exactamente lo que se publica.
- **Sigue siendo BYOK y extensible** — almacenamiento, APIs, scheduler y frontend siguen siendo faciles de inspeccionar y ampliar.

---

## Interfaz y Experiencia de Usuario

Una moderna React SPA con diseno glassmorphism, construida para maxima claridad y control.

<div align="center">
  <img src="assets/screenshots/dashboard-full.png" alt="OpenCMO Dashboard" width="850" />
  <p><i>Dashboard de Proyectos en Tiempo Real — Monitorea SEO, GEO (Visibilidad IA), rankings SERP y engagement comunitario de un vistazo.</i></p>
</div>

<div align="center">
  <h3>
    <a href="https://www.bilibili.com/video/BV1T5AMzoEKV/">
      ▶ Ver el demo completo en Bilibili
    </a>
  </h3>
  <sub>Recorrido de 10 minutos con todas las funciones: Auditoria SEO, Deteccion GEO, Seguimiento SERP, Grafo de Conocimiento, Chat Multiagente y mas.</sub>
</div>

---

## Grafo de Conocimiento Interactivo

El **Grafo de Conocimiento** es el corazon de tu inteligencia de mercado — una red 3D interactiva dirigida por fuerzas que visualiza todo tu ecosistema de marketing.

<div align="center">
  <img src="assets/screenshots/graph-page.png" alt="3D Knowledge Graph" width="850" />
  <p><i>Mapa de red 3D dinamico que conecta tu marca, palabras clave, discusiones, competidores y rankings SERP.</i></p>
</div>

**Capacidades clave:**
- **Expansion activa del grafo** — Haz clic en "Start Exploring" y el grafo descubre competidores, palabras clave y conexiones ola por ola. Puedes pausar y reanudar cuando quieras.
- **Topologia BFS por profundidad** — Los nodos descubiertos se conectan con su nodo padre en lugar de aplanarse contra la marca. Los nodos mas profundos se ven mas pequenos y mas tenues.
- **Visualizacion de frontera** — Los nodos aun no explorados se resaltan con un anillo violeta para mostrar hacia donde puede crecer el grafo.
- **Exploracion interactiva** — Zoom, arrastre y desplazamiento por el universo digital de tu marca.
- **6 dimensiones de nodos** — Marca (purpura), Palabras clave (cian), Discusiones comunitarias (ambar), Rankings SERP (verde), Competidores (rojo), Palabras clave superpuestas (naranja).
- **Inteligencia competitiva** — Agrega URLs de competidores para visualizar campos de batalla compartidos con lineas punteadas rojas.
- **Sincronizacion en tiempo real** — El grafo se reequilibra cada 30 segundos (cada 5 segundos durante la expansion activa).
- **Descubrimiento de competidores con IA** — Identifica automaticamente competidores y rastrea palabras clave superpuestas.

---

## Funcionalidades Destacadas

### Auditoria SEO

Utiliza la API de Google PageSpeed Insights para auditar continuamente puntuacion de rendimiento, Core Web Vitals (LCP, CLS, TBT), Schema.org, robots.txt y sitemaps. Ahora incluye **Deteccion de Crawlers IA** (verifica robots.txt para 14 crawlers de IA — GPTBot, ClaudeBot, PerplexityBot, Google-Extended, etc.) y validacion y generacion de **llms.txt** (el estandar emergente para guiar crawlers de IA).

<div align="center">
  <img src="assets/screenshots/seo-page.png" alt="SEO Audit Dashboard" width="850" />
  <p><i>Grafico de tendencia de rendimiento y analisis detallado de Core Web Vitals.</i></p>
</div>

### Deteccion GEO (Visibilidad en Busqueda IA)

Monitorea la visibilidad de tu marca en motores de busqueda IA: Perplexity, You.com, ChatGPT, Claude y Gemini. Ahora mejorado con **Puntuacion de Citabilidad** (analisis de preparacion para citacion IA en 5 dimensiones), escaneo de **Huella Digital de Marca** (presencia en YouTube, Reddit, Wikipedia, Wikidata, LinkedIn con puntuacion ponderada por correlacion) y deteccion de **Acceso de Crawlers IA** (14 crawlers incluyendo GPTBot, ClaudeBot, PerplexityBot).

<div align="center">
  <img src="assets/screenshots/geo-page.png" alt="GEO Visibility Tracking" width="850" />
  <p><i>Tendencia de puntuacion de visibilidad de marca en plataformas de busqueda IA.</i></p>
</div>

### Seguimiento SERP

Rastrea continuamente las posiciones de busqueda de tus palabras clave objetivo. Compatible con web crawling o la API de DataForSEO.

<div align="center">
  <img src="assets/screenshots/serp-page.png" alt="SERP Keyword Rankings" width="850" />
  <p><i>Lista de posiciones de palabras clave y grafico de historial de rankings.</i></p>
</div>

### Monitoreo de Comunidad

Escanea automaticamente menciones de marca y discusiones relevantes en **Reddit, Hacker News, Dev.to, YouTube, Bluesky y Twitter/X**. Incluye puntuacion multi-senal (velocidad de engagement, relevancia textual, decaimiento temporal, deteccion de convergencia multiplataforma) para rankings comparables entre plataformas.

<div align="center">
  <img src="assets/screenshots/community-page.png" alt="Community Monitoring" width="850" />
  <p><i>Historial de escaneos multiplataforma y discusiones en seguimiento.</i></p>
</div>

### Investigacion de Tendencias

El **Agente de Investigacion de Tendencias** investiga temas en todas las plataformas comunitarias con expansion de consultas, modo comparativo ("X vs Y") y filtrado por ventana temporal. Los resultados se clasifican con puntuacion multi-senal y se sintetizan en informes accionables.

### Insights Proactivos

OpenCMO no espera a que revises — **te avisa cuando algo importa**. Siete detectores basados en reglas (costo LLM cero) monitorean continuamente caidas de ranking SERP, descensos de puntuacion GEO, discusiones comunitarias de alto engagement, regresiones de rendimiento SEO, brechas de keywords con competidores, **regresiones de puntuacion de citabilidad** y **bloqueos de crawlers IA**. Los insights aparecen como badge de campana de notificacion y banner prioritario en el Dashboard, cada uno con botones CTA accionables.

### Inteligencia del Grafo

El grafo de conocimiento ya no es solo una visualizacion — es una **capa de inteligencia activa**. Los datos del grafo (competidores, brechas de keywords, rankings SERP) se inyectan automaticamente en sesiones de chat e informes de investigacion, y el agente CMO puede consultar el panorama competitivo bajo demanda.

### Cola de aprobaciones y operaciones programadas

Revisa el payload exacto de publicacion dentro de la SPA, apruebalo o rechaza con traza persistente, y deja que el proceso web mantenga vivos los monitores programados. La publicacion real sigue respetando `OPENCMO_AUTO_PUBLISH=1`, asi que la aprobacion no salta la ultima barrera de seguridad.

---

## Tu Equipo de Marketing IA

OpenCMO incluye **mas de 25 agentes de IA especializados** organizados en tres categorias:

### Agentes de Inteligencia de Mercado

| Agente | Responsabilidad |
| :--- | :--- |
| **Agente CMO** | El orquestador. Enruta tareas automaticamente al experto adecuado. |
| **Auditor SEO** | Audita Core Web Vitals, Schema.org, robots.txt y sitemaps via Google PageSpeed API. |
| **Especialista GEO** | Monitorea la visibilidad de tu marca en Perplexity, You.com, ChatGPT, Claude y Gemini. |
| **Radar Comunitario** | Escanea Reddit, Hacker News y Dev.to en busca de menciones de marca y discusiones relevantes. |

### Agentes de Creacion de Contenido (Global)

| Agente | Plataforma |
| :--- | :--- |
| **Experto Twitter/X** | Tweets, hooks y hilos virales |
| **Estratega Reddit** | Posts autenticos y respuestas inteligentes en subreddits |
| **Pro LinkedIn** | Posts profesionales de liderazgo de opinion |
| **Experto Product Hunt** | Taglines, descripciones y comentarios de makers |
| **Formateador Hacker News** | Posts tecnicos "Show HN" |
| **Escritor Blog/SEO** | Articulos largos optimizados para SEO (2000+ palabras) |
| **Experto Dev.to** | Articulos para comunidad de desarrolladores |

### Agentes de Creacion de Contenido (Plataformas Chinas)

| Agente | Plataforma |
| :--- | :--- |
| **Experto Zhihu** | Zhihu - Plataforma de preguntas y respuestas |
| **Experto Xiaohongshu** | RED (Xiaohongshu) - Comercio social |
| **Experto V2EX** | V2EX - Foro de desarrolladores |
| **Experto Juejin** | Juejin - Comunidad de desarrolladores |
| **Experto Jike** | Jike - Plataforma social |
| **Experto WeChat** | Ecosistema WeChat |
| **Experto OSChina** | OSChina - Codigo abierto |
| **Experto GitCode** | GitCode - Plataforma de codigo abierto |
| **Experto SSPAI** | SSPAI - Productividad |
| **Experto InfoQ** | InfoQ China - Medios tecnologicos |
| **Experto Ruanyifeng** | Formato de envio para el semanario Ruanyifeng |

---

## Integraciones de Plataformas

Todas las integraciones se configuran directamente desde el **panel de Configuracion** del dashboard web — no es necesario editar archivos `.env`.

<div align="center">
  <img src="assets/screenshots/settings-panel.png" alt="Settings Panel" width="600" />
  <p><i>Panel de configuracion unificado — Configura todas las claves API e integraciones de plataformas desde la interfaz web.</i></p>
</div>

### Monitoreo y Analisis (automatico)

| Capacidad | Plataformas | Metodo |
| :--- | :--- | :--- |
| **Monitoreo Comunitario** | Reddit, Hacker News, Dev.to | APIs publicas (sin autenticacion) |
| **Deteccion GEO** | Perplexity, You.com | Web crawling (sin autenticacion) |
| **Deteccion GEO** | ChatGPT, Claude, Gemini | Llamadas API (configurar claves en Ajustes) |
| **Auditoria SEO** | Google PageSpeed Insights | HTTP API (clave opcional para limites mayores) |
| **Seguimiento SERP** | Google, DataForSEO | Web crawling o API DataForSEO |

### Publicacion (controlada por el usuario)

| Plataforma | Metodo | Configuracion |
| :--- | :--- | :--- |
| **Reddit** | PRAW (publicar + responder) | Configurar credenciales de app Reddit en Ajustes |
| **Twitter/X** | Tweepy (tweets) | Configurar credenciales API de Twitter en Ajustes |

### Reportes

| Funcion | Metodo | Configuracion |
| :--- | :--- | :--- |
| **Reportes por Email** | SMTP | Configurar credenciales SMTP en Ajustes |

> Los demas agentes (LinkedIn, Product Hunt, plataformas chinas, etc.) generan contenido listo para usar que puedes copiar y pegar en la plataforma destino.

---

## Como Funciona: Debate Multiagente

Al enviar una URL, OpenCMO organiza una **discusion colaborativa de 3 rondas** entre agentes especializados:

```mermaid
sequenceDiagram
    participant PA as Analista de Producto
    participant SEO as Especialista SEO
    participant CS as Estratega Comunitario
    participant SD as Director de Estrategia

    Note over PA,CS: Ronda 1 — Analisis Independiente
    PA->>PA: Identificar producto, funciones, audiencia
    SEO->>SEO: Sugerir palabras clave y terminos competitivos
    CS->>CS: Proponer temas comunitarios y plataformas

    Note over PA,CS: Ronda 2 — Refinamiento Colaborativo
    PA->>SEO: Comparte insights de producto
    SEO->>CS: Comparte estrategia de palabras clave
    CS->>PA: Comparte puntos de dolor de la comunidad

    Note over SD: Ronda 3 — Consenso Ejecutivo
    SD->>SD: Sintetiza el hilo de discusion<br/>en una Estrategia de Marca finalizada.
```

Al permitir que los agentes lean y reaccionen entre si, OpenCMO produce estrategias fundamentalmente mas ricas que las respuestas de IA de un solo paso.

<div align="center">
  <img src="assets/screenshots/multi-agent-discussion.png" alt="Multi-Agent Discussion" width="850" />
  <p><i>Discusion de analisis multiagente — Multiples agentes especializados colaborando en tiempo real.</i></p>
</div>

---

## Interfaz de Chat IA

Conversa directamente con mas de 25 agentes especializados. El agente CMO enruta automaticamente al experto optimo. Respuestas en tiempo real via streaming SSE.

<div align="center">
  <img src="assets/screenshots/chat-interface.png" alt="AI Chat Interface" width="850" />
  <p><i>Grilla de seleccion de expertos y chat con streaming — Acceso instantaneo a expertos de marketing.</i></p>
</div>

---

## Guia de Inicio Rapido

OpenCMO es compatible con cualquier API compatible con OpenAI (**OpenAI, DeepSeek, NVIDIA NIM, Ollama**, etc.).

### 1. Instalacion

```bash
git clone https://github.com/study8677/OpenCMO.git
cd OpenCMO

# Instalar todas las dependencias Python
pip install -e ".[all]"

# Inicializar playbooks del crawler
crawl4ai-setup
```

### 2. Configuracion

```bash
cp .env.example .env
```
Edita `.env` con tus credenciales de proveedor. *Ejemplo para OpenAI:*
```env
OPENAI_API_KEY=sk-yourAPIKeyHere
OPENCMO_MODEL_DEFAULT=gpt-4o
```

> **Consejo:** Tambien puedes configurar todas las claves API directamente desde el panel de **Configuracion** del dashboard web — no es necesario editar `.env` despues de la configuracion inicial.

### 3. Iniciar el Dashboard

```bash
opencmo-web
```
Abre [http://localhost:8080/app](http://localhost:8080/app) en tu navegador.

> *Prefieres la terminal? Ejecuta `opencmo` para el modo chatbot CLI interactivo.*

### 4. Desarrollo Frontend (opcional)

```bash
cd frontend
npm install
npm run dev     # Servidor dev en localhost:5173 (proxy API a :8080)
npm run build   # Build de produccion
```

---

## Hoja de Ruta

- [x] **Mas de 25 expertos IA en marketing** — Chat con enrutamiento inteligente
- [x] **Analisis de URL multiagente** — Via debate colaborativo
- [x] **React SPA** — Soporte multiidioma (EN/ZH)
- [x] **API agnostico** — OpenAI, Anthropic, DeepSeek, NVIDIA, Ollama
- [x] **Grafo de conocimiento 3D interactivo** — Con expansion BFS activa e inteligencia competitiva
- [x] **Monitoreo comunitario** — Reddit, Hacker News, Dev.to
- [x] **Deteccion GEO** — Perplexity, You.com, ChatGPT, Claude, Gemini
- [x] **Auditoria SEO** — Core Web Vitals, Schema.org, robots.txt
- [x] **Seguimiento SERP** — Monitoreo de rankings de palabras clave
- [x] **Cola de aprobaciones + runtime de monitores programados** — Revision exacta del payload y ejecucion cron en el ciclo web
- [x] **Publicacion automatica** — Reddit (publicar + responder) y Twitter
- [x] **Reportes por email** — Via SMTP
- [x] **Descubrimiento de competidores con IA** — Analisis de superposicion de palabras clave
- [x] **Puntuacion comunitaria multi-senal** — velocidad de engagement, relevancia textual, decaimiento temporal, deteccion de convergencia
- [x] **Agente de investigacion de tendencias** — exploracion de temas con expansion de consultas y modo comparativo
- [x] **Pipeline de inteligencia del grafo** — el grafo alimenta decisiones de agentes, contexto de chat y briefs de contenido
- [x] **Motor de insights proactivos** — detectores de caida SERP/GEO/comunidad/SEO/brecha competitiva + CTA accionable
- [x] **Panel de configuracion unificado** — Configura todas las claves API desde la UI web
- [x] **Kit de optimizacion GEO** — Puntuacion de citabilidad (preparacion para citacion IA en 5 dimensiones), deteccion de crawlers IA (14 crawlers), escaneo de huella digital de marca (YouTube/Reddit/Wikipedia/LinkedIn), validacion y generacion de llms.txt. Inspirado por [geo-seo-claude](https://github.com/zubair-trabzada/geo-seo-claude)
- [ ] Publicacion directa en LinkedIn, Product Hunt y mas
- [ ] Afinacion personalizada de voz de marca
- [ ] Crawls SEO de sitio completo a nivel empresarial

---

## Agradecimientos

- [geo-seo-claude](https://github.com/zubair-trabzada/geo-seo-claude) de [@zubair-trabzada](https://github.com/zubair-trabzada) — Un completo kit de auditoria GEO (Generative Engine Optimization) para Claude Code. El modulo GEO de OpenCMO se inspira en su marco de puntuacion de citabilidad, enfoque de deteccion de crawlers IA (mas de 14 crawlers incluyendo GPTBot, ClaudeBot, PerplexityBot), matriz de optimizacion especifica por plataforma (estrategias separadas para Google AIO, ChatGPT, Perplexity, Gemini, Bing Copilot) y metodologia de evaluacion E-E-A-T.
- [last30days-skill](https://github.com/mvanhorn/last30days-skill) de [@mvanhorn](https://github.com/mvanhorn) — El sistema de puntuacion multi-senal, la deteccion de convergencia multiplataforma y la herramienta de investigacion de tendencias de OpenCMO se inspiraron en el enfoque de last30days para la investigacion comunitaria multiplataforma y el ranking de calidad.

---

## Colaboradores

- [study8677](https://github.com/study8677) - Creador y mantenedor de OpenCMO
- [ParakhJaggi](https://github.com/ParakhJaggi) - Contribuciones de integracion Tavily mediante [#2](https://github.com/study8677/OpenCMO/pull/2) y [#3](https://github.com/study8677/OpenCMO/pull/3)
- Ver [CONTRIBUTORS.md](CONTRIBUTORS.md) para el registro mantenido de creditos
- Ver [CONTRIBUTING.md](CONTRIBUTING.md) para el flujo de contribucion, expectativas de PR y guia de atribucion

> El grafico predeterminado de Contributors de GitHub depende de la asociacion entre el email del autor del commit y la cuenta de GitHub. Si un PR se fusiona con commits firmados con un email no vinculado a la cuenta del colaborador, ese trabajo puede no aparecer en el grafico aunque la contribucion sea real.

---

<p align="center">
  Hecho con dedicacion por la Comunidad de Codigo Abierto.<br/>
  <b>Si OpenCMO te ahorra tiempo, por favor dale una estrella en GitHub!</b>
</p>

# Am I Exposed? — Diseño del rebuild y fases

Fecha: 2026-11-25. Dueño: Guillermo Carlin. Autor: Claude.
Base: el documento de claude.ai (`prompt-claude-code-am-i-exposed.md`) + el brand-board (`am-i-exposed-brand-board.html`) + el mapa real del repo.

Este documento es el DELTA entre ese documento y la realidad del repo: cómo se adapta a Astro, al stack que ya existe y a las decisiones tomadas. Nada se construye hasta que el dueño apruebe.

---

## 1. Intención / por qué
Reconstruir am-i-exposed.com en Astro para: (a) que lo que el sitio dice sobre dinero y elegibilidad sea verificable y defendible legalmente; (b) adoptar el sistema visual elegido (logo moneda radar + Ruta B "estado de cuenta"); (c) dejar una base limpia para el producto de monitoreo y la futura app Expo. Todo en infraestructura gratis, sin tocar el sitio vivo (que cobra $5 reales) hasta el cutover.

## 2. Decisiones ya tomadas (aprobadas por el dueño)
- **Framework:** Astro. SSG para las ~1.130 páginas + islas (React) para lo interactivo.
- **Visual:** paleta Ruta B + moneda radar (`m2` quieto / `m2a` animado), según el brand-board.
- **Dinero:** un número grande = el máximo por persona del acuerdo individual más alto, reetiquetado "top single-case payout" / "pago más alto en un caso". Nunca sumado, nunca "te deben". Cada acuerdo muestra su rango textual real de la fuente ("$45–$2,000 si calificas") + enlace a la fuente.
- **Tooling ($0 estricto):** mínimo. Turnstile (gratis) dentro de la función de chequeo que ya existe. PostHog y A/B se difieren hasta que el tráfico lo justifique.
- **Email:** se mantiene Brevo (ya tiene el dominio autenticado). Resend no hace falta.
- **Locale:** `es-US` / `en-US` (reemplaza `es_PE`).
- **Enfoque de build:** rama nueva sobre `main` + preview de Vercel. El sitio vivo intacto. Cutover solo con "aprobado" explícito.
- **Pagos/acceso:** sin cambios de producto. Stripe Checkout $5 (report) + suscripción de monitoreo unificada; Supabase `purchases`/`breach_watch`; sync a Zoho. Se portan tal cual.

## 3. No-objetivos / anti-objetivos
- Nada de infraestructura pagada. Ningún framework además de Astro. No tocar precios/productos de Stripe. Ninguna dirección visual que no sea Ruta B/radar. No tocar el sitio vivo hasta el cutover. **No inventar un "pago típico"** que no exista en los datos.

## 4. Restricciones
- Vercel Hobby: ≤12 funciones serverless (hoy 10; conservar la consolidación de `monitor.js`: 1 función, 8 operaciones por `?op=`).
- HIBP Core 1, ~10 consultas/min: cola con disciplina (9/min, caché 24h por HMAC del email).
- Bilingüe EN+ES, claro+oscuro, WCAG AA.
- Toda data de feed/CMS/DB es no confiable: validar URLs (solo http/https) y fechas antes de renderizar (regla global).

## 5. Arquitectura

### 5.1 Tech
- **Astro + TypeScript.** Islas React para: formulario de escaneo + resultado (Ruta B), dashboard del suscriptor, toggle de precios, y el componente `RadarCoin`. **Content Collections** para settlements y daily-hack, alimentadas desde los JSON que ya existen.
- **Pipeline de datos:** se mantienen los scrapers/builders de Python (`tools/`) como fuente de datos; Astro consume su salida (`settlements.json`, `open-settlements.json`, `funnel.json`, `data/radar.json`, `ftc-refunds.json`). Se portan a Content Collections de forma incremental.
- **API:** las funciones `api/*.mjs|js` se mantienen como funciones Vercel (son `fetch` puro, agnósticas al framework). Astro se despliega al lado. Se preserva la consolidación `monitor.js`. Se añade verificación Turnstile **dentro** de `check-email` (sin función nueva).
- **Hosting ($0):** Vercel (team `am-i-exposed`), Supabase `morosdhhoznicppmrqyr`, Brevo, Stripe.

### 5.2 Contenido / datos
- 1.126 páginas de settlements (SSG, solo inglés — son demandas de EE.UU.). Las 1.036 cerradas siguen sin publicarse (se usan para matching de alertas). Daily-hack EN+ES. `RadarCoin` compartido para favicon + header en todas las páginas generadas.

### 5.3 Sistema de diseño
- Tokens Ruta B (web, claro): fondo `#FBF8F2`, texto `#16120E`, muted `#5E554B`, oro `#8A5A1C`, elegible `#1F7A4D`, alerta `#B42318` (todos AA verificados en el brand-board).
- Tokens marca/app (oscuro): `#0B0907` / `#D59E5D` / `#F2CD75`.
- Tipos: Fraunces 600 (títulos y montos), Public Sans (interfaz), IBM Plex Mono (montos de línea, plazos, nº de caso).
- `RadarCoin`: `m2` estático (SVG inline con las estrías pre-renderizadas, no por JS, para favicon/emails/<32px); `m2a` animado (barrido 3s + pulso), pausa con IntersectionObserver, queda quieto con `prefers-reduced-motion`.

### 5.4 Modelo de dinero / elegibilidad (pantalla de resultado, Ruta B)
- Titular: conteo — "You may qualify for N open settlements" / "Podrías calificar para N acuerdos abiertos".
- Número grande secundario: el máximo de un solo caso, reetiquetado "top single-case payout". Nunca una suma.
- Cada línea: rango textual verbatim de la fuente + chip (Likely eligible / Check eligibility) + fuente + plazo.
- El detalle (nombres de breaches, enlaces, montos por línea) se ve **solo tras confirmar el email** con magic link de Supabase Auth (doc Fase 0 #3). El chequeo gratis devuelve solo conteos y no guarda el email (solo HMAC). Enlaces de reclamo siempre gratis.
- Disclaimer visible (EN/ES): no somos estudio de abogados, no presentamos reclamos, no afiliados al tribunal ni al administrador; el administrador decide la elegibilidad.

## 6. Hoja de ruta por fases (cada una termina en preview + aprobación)
- **M0 — Scaffold + paridad de contenido (sin rediseño visual todavía).** Proyecto Astro; portar 1:1 las páginas estáticas (home, legales, 1.126 settlements, daily-hack, pricing); cablear la API y el pipeline de datos actuales; preview de Vercel que se vea como hoy. Se hornean los arreglos de confianza en copy: el reetiquetado del número, quitar cualquier claim sumado/"owed", renombrar "Money Pool" → "Open settlements / Acuerdos abiertos", disclaimer. **Compuerta:** preview + checklist de paridad de contenido (recuento de páginas, enlaces, sitemap).
- **M1 — Rediseño Ruta B.** Pantallas nuevas (home, escaneo, resultado con magic-link, detalle de acuerdo, precios, Full Report $5) + `RadarCoin` + Turnstile + `es-US`. **Compuerta:** capturas a 390 y 1280 px EN+ES + tabla de contraste.
- **M2 — Monitoreo.** Dashboard del suscriptor + alertas (Brevo) + emails de ciclo de vida + borrado de cuenta en un clic + re-escaneo según capacidad HIBP. **Compuerta:** preview + flujos.
- **Cutover.** Apuntar producción al build de Astro tras aprobación; dejar el sitio viejo como rollback.
- **V1 / V2.** Según el documento de claude.ai (PWA, job de auditoría de matches, luego app Expo). Cada una con su compuerta.

## 7. Lo que queda al constructor (se fija en el plan de implementación por milestone)
- Esquemas exactos de las Content Collections; API de cada componente; qué pasos de Python se portan vs se mantienen; forma del cutover (swap de dominio vs cambio de production branch en Vercel), que se decide en la compuerta de cutover.

## 8. Pendiente de aprobación del dueño
1. Aprobar este diseño y arrancar por **M0** (scaffold + paridad).
2. Confirmar `es-US` como default.
3. El hotfix del "$5,050" ya va por una sesión aparte (PR a `main`), independiente de este rebuild.

## 9. Notas de seguridad / operación (se respetan en todo el rebuild)
- Preguntar qué cuenta antes de tocar GitHub/Vercel/Supabase; cuenta gh activa `gcarlin-selentic`, repo `Gcarlin-Am-I-Exposed/am-i-exposed`, team Vercel `am-i-exposed`.
- Nunca pegar secretos en el chat; todo por variables de entorno de Vercel/Supabase. Nunca imprimir valores.
- No hacer merge de PRs salvo que el dueño lo pida. Dar siempre una URL de preview para cambios visuales.
- Confirmar $0 antes de cualquier recurso facturable.

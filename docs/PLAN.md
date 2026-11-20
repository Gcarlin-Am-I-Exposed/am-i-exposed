# Radar de Ataques: investigación rica + publicación a prueba de fallos (Opción B)

Hallazgo que definió el diseño: sin la investigación de la tarea cloud, el dato
regional se cae a 1/3 (30d: Perú 19->3, LatAm 198->54, prospectos 155->51). Esa
inteligencia regional es el valor del producto, así que la tarea cloud se queda
COMO INVESTIGADORA. El problema era solo el git (403). La solución: la tarea
cloud NO toca git nunca; escribe a Supabase (conector que ya tiene). GitHub
Actions lee de Supabase + RansomLook/HIBP y publica todo con su token.

## Arquitectura final
1. Tarea cloud (claude.ai, diaria ~8:52 Lima): investiga (multi-fuente + extractores
   de la Mac) y hace UPSERT de sus day-docs curados a la tabla Supabase `radar_days`.
   SIN git, SIN gh, SIN repo. Solo el conector de Supabase. -> nunca más 403.
2. GitHub Actions (una tarea diaria, su token):
   a. refresh-radar.py -> data/radar.json (RansomLook+HIBP).
   b. Lee Supabase `radar_days` (REST + service key) -> reconstruye /tmp/radar-days/*.json.
   c. merge-radar.py -> /tmp/combinado.json (web) + /tmp/incidentes.json (dashboard).
   d. build-daily-hack.py --data combinado.json -> página pública.
   e. build-linkedin-card.py -> PNG tarjeta + texto Alerta (plantilla, $0).
   f. Sube incidentes.json a Supabase `dashboard_snapshot` (privado; el endpoint lo sirve con gate).
   g. Commit SOLO del HTML + PNG (token). Dispara el correo con la imagen+texto.
3. Dashboard web (gate): monitor.js `?op=dashboard` verifica DASHBOARD_PASSWORD -> lee
   `dashboard_snapshot` de Supabase -> lo devuelve. La página /dashboard/ hace prompt -> fetch -> render.
   Datos ricos (los mismos que hoy), no públicos.

## Qué construyo yo (todo el código)
- [x] Tablas Supabase `radar_days`, `dashboard_snapshot` (creadas en morosdhhoznicppmrqyr, RLS).
- [x] build-dashboard.py: consume incidentes.json (merged, con flag prospect), emite la vista JSON (--view-json) y el cascarón HTML. "Clientes" quitada. Marca am-i-exposed.
- [x] monitor.js `?op=dashboard` + `_dashboard.mjs`: gate por password (timingSafeEqual + rate-limit), lee dashboard_snapshot. Sin función nueva (sigue en 10/12).
- [x] build-linkedin-card.py: PNG tarjeta + texto Alerta (plantilla, $0, acentos, am-i-exposed). APROBADA por el dueño.
- [ ] email: monitor.js `?op=daily-radar` (auth CRON_SECRET) manda la tarjeta (adjunto por URL) + texto por Brevo. Helper en _email.js.
- [ ] workflow único radar-daily.yml: refresh-radar.py -> lee Supabase radar_days -> merge -> build page + dashboard view + linkedin card -> sube dashboard_snapshot a Supabase -> commit (HTML+PNG) -> llama al correo. Reemplaza refresh-radar.yml + publish-daily-hack.yml.
- [ ] página /dashboard/index.html: generada por build-dashboard.py en modo gated (no --embed). Añadir a robots noindex.

## Qué haces tú UNA vez
1. Recrear la tarea cloud una última vez con el prompt nuevo que te doy. ESTA VEZ NO necesita
   el repo (cero git), solo el conector de Supabase apuntando al proyecto morosdhhoznicppmrqyr.
   Por eso el 403 desaparece de raíz.
2. Poner `DASHBOARD_PASSWORD` en Vercel (tú eliges la clave).
3. OK para crear 2 tablas en tu Supabase morosdhhoznicppmrqyr.

## Retirar
- rama radar-data; publish-daily-hack.yml; la dependencia de git en la rutina. refresh-radar.yml se
  funde en radar-daily.yml.

Rama: `feat/radar-one-task`. Producción solo por PR aprobado.
Pendiente aclarar: pestaña "Clientes" del dashboard (watchlist de empresas a vigilar?).

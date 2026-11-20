#!/usr/bin/env python3
"""Baja los day-docs curados de la tarea cloud desde Supabase (tabla radar_days)
y los escribe como <out>/<date>.json, el formato que lee tools/merge-radar.py.

Lee SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY del entorno. Sin clave NO falla:
deja la carpeta vacia y la pagina sale solo con RansomLook/HIBP (degrada, no se
congela). Asi la publicacion nunca depende de que la tarea cloud haya escrito.

Uso: python3 tools/radar-pull-curated.py [out_dir]   (default /tmp/radar-days)
"""
import datetime as dt
import json
import os
import sys
import urllib.request

OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/radar-days'
os.makedirs(OUT, exist_ok=True)

url = os.environ.get('SUPABASE_URL', '').rstrip('/')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
if not url or not key:
    print('sin SUPABASE_URL/KEY: carpeta curada vacia (solo RansomLook/HIBP)')
    sys.exit(0)

req = urllib.request.Request(
    f'{url}/rest/v1/radar_days?select=date,doc',
    headers={'apikey': key, 'Accept': 'application/json'})
try:
    with urllib.request.urlopen(req, timeout=20) as r:
        rows = json.loads(r.read().decode('utf-8'))
except Exception as e:
    print(f'no se pudo leer radar_days ({type(e).__name__}): carpeta vacia')
    sys.exit(0)

# Ventana: solo los ultimos ~40 dias sirven a la pagina (7 dias) y al dashboard
# (30 dias); traer todo cada dia es desperdicio. radar_days es chica igual.
corte = (dt.date.today() - dt.timedelta(days=40)).isoformat()
n = 0
for row in rows if isinstance(rows, list) else []:
    date, doc = row.get('date'), row.get('doc')
    if not date or doc is None or date < corte:
        continue
    if isinstance(doc, str):
        try:
            doc = json.loads(doc)
        except Exception:
            continue
    # Nombre saneado: date viene de la DB (dato), no se mete en la ruta sin filtrar.
    safe = ''.join(c for c in date if c.isdigit() or c == '-')[:10]
    if len(safe) != 10:
        continue
    json.dump(doc, open(os.path.join(OUT, f'{safe}.json'), 'w', encoding='utf-8'),
              ensure_ascii=False)
    n += 1

print(f'{n} day-docs curados desde Supabase -> {OUT}')

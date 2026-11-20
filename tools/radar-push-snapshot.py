#!/usr/bin/env python3
"""Sube la vista del dashboard (incidentes fusionado) a Supabase, tabla
dashboard_snapshot, con upsert de la fila id='latest'. api/monitor.js?op=dashboard
la sirve detras de contrasena, asi que el dato rico queda privado (no es un
archivo publico del repo).

Lee SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY del entorno. Sin clave NO falla:
simplemente no actualiza el snapshot (el dashboard muestra el del dia anterior).

Uso: python3 tools/radar-push-snapshot.py [view.json]  (default /tmp/dashboard-view.json)
"""
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request

path = sys.argv[1] if len(sys.argv) > 1 else '/tmp/dashboard-view.json'
url = os.environ.get('SUPABASE_URL', '').rstrip('/')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
if not url or not key:
    print('sin SUPABASE_URL/KEY: no se sube el snapshot del dashboard')
    sys.exit(0)

data = json.load(open(path, encoding='utf-8'))
payload = json.dumps([{
    'id': 'latest',
    'data': data,
    'generated_at': dt.datetime.now(dt.timezone.utc).isoformat(),
}]).encode('utf-8')

req = urllib.request.Request(
    f'{url}/rest/v1/dashboard_snapshot',
    data=payload, method='POST',
    headers={
        'apikey': key,
        'Content-Type': 'application/json',
        # Upsert por PK (id) + no devolver la fila gigante.
        'Prefer': 'resolution=merge-duplicates,return=minimal',
    })
try:
    with urllib.request.urlopen(req, timeout=25) as r:
        print(f'snapshot del dashboard subido: HTTP {r.status} ({len(data.get("items", []))} filas)')
except urllib.error.HTTPError as e:
    body = e.read().decode('utf-8', 'replace')[:300]
    sys.exit(f'fallo al subir snapshot: HTTP {e.code} {body}')
except Exception as e:
    sys.exit(f'fallo al subir snapshot: {type(e).__name__}')

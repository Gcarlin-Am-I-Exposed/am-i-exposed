#!/usr/bin/env python3
"""Une el Radar de Ataques de Selentic con data/radar.json en un solo registro.

Hay dos fuentes y una sola verdad:

  data/radar.json   lo que baja tools/refresh-radar.py cada noche
                    (RansomLook y Have I Been Pwned), con pais en ISO y sector
                    en slug.
  Radar de Ataques  los documentos diarios que arma la tarea de las 8:52 de
                    Lima (ransomware.live, Brandefense ATLAS, SOCRadar,
                    Ransom-DB, RansomLook, HIBP y prensa), con etiquetas en
                    espanol, nota comercial y casos agrupados por grupo.

De aqui salen dos archivos con LAS MISMAS FILAS:

  --public     lo que lee tools/build-daily-hack.py para la pagina publica.
               Sin prospectos ni notas comerciales.
  --dashboard  incidentes.json para el Dashboard privado del Radar: las mismas
               filas, con las etiquetas en espanol y los campos de prospecto.

Ninguno de los dos se confirma en el repositorio: el repo es publico y los
terminos de ransomware.live no permiten publicar sus datos crudos. Al repo
solo va el HTML que se genera con --public.

Duplicados: el mismo grupo nombrando a la misma victima en un plazo de 14
dias es un caso. Se queda la fila del Radar, que trae pais, estado y fuente
revisados a mano, y se le suma la fuente de la otra. Una fila agrupada del
Radar ("Grupo Soul: 24 victimas") se descuenta con las filas individuales de
RansomLook que nombra; si las nombra todas, desaparece y quedan las
individuales, que tienen pais e industria por victima.

Uso:
  python3 -I tools/merge-radar.py --radar-days DIR [--site data/radar.json]
         --public OUT.json --dashboard OUT.json
DIR tiene un JSON por documento de la coleccion "days" del Radar, tal como lo
devuelve db_list/db_get (con o sin el envoltorio {"data": ...}).
"""
import argparse
import datetime as dt
import glob
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _radar import ESTADOS, LATAM, PAISES, SECTORES, TIPOS  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAZO_DUPLICADO = 14   # dias

LIMA = dt.timezone(dt.timedelta(hours=-5))


def plano(s):
    """Minusculas, sin tildes, solo letras y numeros."""
    s = unicodedata.normalize('NFKD', s or '')
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r'[^a-z0-9]', '', s)


# ---------------------------------------------------------------- vocabulario

def _invertir(tabla):
    return {plano(v[0]): k for k, v in tabla.items()}


PAIS_ES = _invertir(PAISES)
PAIS_ES.update({plano(x): 'US' for x in ('EE.UU.', 'EEUU', 'USA', 'Estados Unidos')})
PAIS_ES.update({plano('Corea'): 'KR', plano('Emiratos Árabes'): 'AE',
                plano('República Checa'): 'CZ', plano('Holanda'): 'NL',
                plano('Inglaterra'): 'GB', plano('Haití'): 'HT',
                plano('Bahamas'): 'BS', plano('Barbados'): 'BB'})
SECTOR_ES = _invertir(SECTORES)
SECTOR_ES[plano('Otros / Sin identificar')] = 'otros'

ESTADO_ES = {
    plano('Reclamado por el grupo'): 'reclamado',
    plano('Confirmado por la víctima'): 'confirmado',
    plano('Confirmado parcialmente por la víctima'): 'parcial',
    plano('Brecha verificada por HIBP'): 'verificado',
    plano('En investigación'): 'investigacion',
    plano('Datos publicados'): 'publicado',
}

CARIBE = {'CU', 'DO', 'PR', 'JM', 'TT', 'HT', 'BS', 'BB'}
NORTE = {'US', 'CA'}
EUROPA = {'ES', 'PT', 'FR', 'DE', 'IT', 'GB', 'IE', 'NL', 'BE', 'CH', 'AT', 'SE',
          'NO', 'DK', 'FI', 'PL', 'CZ', 'SK', 'HU', 'RO', 'BG', 'GR', 'UA', 'RU',
          'LU', 'IS', 'HR', 'SI', 'RS', 'LT', 'LV', 'EE'}
ASIA = {'IN', 'PK', 'BD', 'CN', 'HK', 'TW', 'JP', 'KR', 'SG', 'MY', 'TH', 'VN',
        'ID', 'PH', 'AU', 'NZ', 'LK', 'NP'}
MOA = {'TR', 'IL', 'AE', 'SA', 'QA', 'KW', 'EG', 'MA', 'NG', 'KE', 'ZA', 'GA',
       'JO', 'LB', 'OM', 'BH', 'IR', 'IQ', 'DZ', 'TN', 'GH'}


def region_dashboard(iso):
    if iso == 'PE':
        return 'Perú'
    if iso in CARIBE:
        return 'Caribe'
    if iso in LATAM:
        return 'Latinoamérica'
    if iso in NORTE:
        return 'Norteamérica'
    if iso in EUROPA:
        return 'Europa'
    if iso in ASIA:
        return 'Asia-Pacífico'
    if iso in MOA:
        return 'Medio Oriente y África'
    return 'Sin identificar'


def pais_es(iso):
    if iso == 'US':
        return 'EE.UU.'
    return PAISES[iso][0] if iso in PAISES else 'Sin identificar'


def tipo_slug(texto):
    p = plano(texto)
    if p.startswith('filtracion'):
        return 'filtracion'
    if p.startswith('ataque'):
        return 'prensa'
    return 'ransomware'


# ------------------------------------------------------------------ identidad

LEGALES = {'inc', 'llc', 'ltd', 'limited', 'sa', 'sac', 'saa', 'srl', 'sas',
           'gmbh', 'corp', 'corporation', 'co', 'company', 'plc', 'pllc', 'ag',
           'bv', 'nv', 'spa', 'lp', 'llp', 'pc', 'pa', 'de', 'cv', 'the'}
DOMINIO = re.compile(r'\b(?:www\.)?([a-z0-9][a-z0-9-]*)(?:\.[a-z0-9-]+)+\b')


def claves(nombre):
    """Las formas en que una victima puede aparecer escrita: por dominio y por
    nombre sin forma societaria."""
    n = unicodedata.normalize('NFKD', nombre or '')
    n = ''.join(c for c in n if not unicodedata.combining(c)).lower()
    out = set()
    for m in DOMINIO.finditer(n):
        if len(m.group(1)) >= 4:
            out.add(re.sub(r'[^a-z0-9]', '', m.group(1)))
    sin_par = re.sub(r'\([^)]*\)', ' ', n)
    if not DOMINIO.fullmatch(sin_par.strip()):
        sin_par = sin_par.replace('.', '')          # S.A.C. -> sac
        palabras = [w for w in re.split(r'[^a-z0-9]+', sin_par) if w and w not in LEGALES]
        k = ''.join(palabras)
        if len(k) >= 4:
            out.add(k)
    return out


def grupo_clave(g):
    k = plano(g)
    return re.sub(r'(ransomware|ransom|group|team|gang)$', '', k) or k


LOTE = re.compile(r'^Grupo\s+.+?:\s*(\d+)\s+víctimas', re.I)


def nombres_lote(claim):
    """Los nombres que una fila agrupada lista en su claim."""
    sin_par = re.sub(r'\([^)]*\)', '', claim or '')
    sin_par = re.sub(r'^[^:]{0,60}:', '', sin_par)   # "Lote del 19/11, ...:"
    return [x.strip() for x in re.split(r'[,;]|\by\b', sin_par) if x.strip()]


# --------------------------------------------------------------------- lectura

def lee_radar(carpeta):
    filas = []
    for f in sorted(glob.glob(os.path.join(carpeta, '*.json'))):
        d = json.load(open(f, encoding='utf-8'))
        d = d.get('data', d)
        dia = d.get('date') or os.path.basename(f)[:-5]
        gen = d.get('generatedAt') or f'{dia}T09:00:00-05:00'
        try:
            visto = dt.datetime.fromisoformat(gen).astimezone(dt.timezone.utc)
        except ValueError:
            visto = dt.datetime.fromisoformat(dia + 'T14:00:00+00:00')
        for k, i in enumerate(d.get('items', [])):
            m = LOTE.match(i.get('victim', ''))
            iso = PAIS_ES.get(plano(i.get('country')), '')
            filas.append({
                'id': f'{dia}-{k:03d}', 'origin': 'Radar',
                'day': dia, 'date': i.get('date') or dia,
                'seen': visto.isoformat(timespec='seconds'),
                'victim': i.get('victim', ''), 'group': i.get('group') or '—',
                'type': tipo_slug(i.get('type')),
                'status': ESTADO_ES.get(plano(i.get('status')), 'reclamado'),
                'country': iso,
                'sector': SECTOR_ES.get(plano(i.get('sector')), 'otros'),
                'victims': int(m.group(1)) if m else 1,
                'batch': bool(m), 'claim': i.get('claim', ''),
                'sources': [{'name': i.get('source', ''), 'url': i.get('sourceUrl', '')}],
                'prospect': bool(i.get('prospect')),
                'prospectNote': i.get('prospectNote', ''),
                'historical': bool(i.get('historical')),
                'republished': (i.get('claim') or '').startswith('Re-publicación'),
                # Lo que el Radar escribio a mano, para el Dashboard.
                '_country_es': i.get('country') or 'Sin identificar',
                '_region_es': i.get('region') or '',
                '_sector_es': i.get('sector') or 'Otros / Sin identificar',
                '_type_es': i.get('type', ''), '_status_es': i.get('status', ''),
            })
    return filas


def lee_sitio(ruta):
    d = json.load(open(ruta, encoding='utf-8'))
    filas = []
    for i in d['items']:
        filas.append({
            'id': 'aie-' + i['id'], 'origin': 'am-i-exposed',
            'day': i['day'], 'date': i['day'], 'seen': i.get('seen') or '',
            'victim': i['victim'], 'group': i.get('group') or '—',
            'type': i.get('type', 'ransomware'), 'status': i.get('status', 'reclamado'),
            'country': (i.get('country') or '').upper(),
            'sector': i.get('sector') or 'otros', 'victims': 1, 'batch': False,
            'claim': '',
            'sources': [{'name': i.get('source', ''), 'url': i.get('sourceUrl', '')}],
            'prospect': False, 'prospectNote': '', 'historical': False,
            'republished': False,
        })
    return filas, d.get('sources', [])


# ---------------------------------------------------------------------- fusion

def _cerca(a, b):
    return abs((dt.date.fromisoformat(a) - dt.date.fromisoformat(b)).days) <= PLAZO_DUPLICADO


def _mismo_grupo(a, b):
    ga, gb = grupo_clave(a['group']), grupo_clave(b['group'])
    if ga and gb:
        return ga == gb
    # Sin grupo (HIBP, prensa): solo si las dos son filtraciones.
    return a['type'] != 'ransomware' and b['type'] != 'ransomware'


def _suma_fuente(fila, otra):
    vistas = {s['name'].lower() for s in fila['sources']}
    for s in otra['sources']:
        if s['name'].lower() not in vistas:
            fila['sources'].append(s)
            vistas.add(s['name'].lower())


def fusiona(radar, sitio):
    # Indice del sitio por (grupo, clave de nombre).
    indice = {}
    for s in sitio:
        for k in claves(s['victim']):
            indice.setdefault((grupo_clave(s['group']), k), []).append(s)
    quitar = set()   # ids del sitio absorbidos por una fila del Radar
    salida = []
    for r in radar:
        if r['batch']:
            vistos = set()
            for nombre in nombres_lote(r['claim']):
                for k in claves(nombre):
                    for s in indice.get((grupo_clave(r['group']), k), []):
                        if s['id'] not in quitar and _cerca(r['day'], s['day']):
                            vistos.add(s['id'])
            if len(vistos) >= r['victims']:
                continue                    # las individuales lo dicen mejor
            r['victims'] -= len(vistos)
            r['victim'] = re.sub(r'\d+(\s+víctimas)', f"{r['victims']}\\1", r["victim"], count=1)
            salida.append(r)
            continue
        for k in claves(r['victim']):
            for s in indice.get((grupo_clave(r['group']), k), []):
                if s['id'] in quitar or not _cerca(r['day'], s['day']):
                    continue
                if not _mismo_grupo(r, s):
                    continue
                quitar.add(s['id'])
                _suma_fuente(r, s)
                if not r['country'] and s['country']:
                    r['country'] = s['country']
                if r['sector'] == 'otros' and s['sector'] != 'otros':
                    r['sector'] = s['sector']
                r['origin'] = 'Ambos'
        salida.append(r)
    # Los duplicados dentro del Radar (la misma victima cargada dos dias).
    unicos, vistas = [], {}
    for r in salida:
        ks = {(grupo_clave(r['group']), k) for k in claves(r['victim'])} if not r['batch'] else set()
        previa = next((vistas[k] for k in ks if k in vistas), None)
        if previa is not None and _cerca(previa['day'], r['day']) and not r['republished']:
            _suma_fuente(previa, r)
            continue
        for k in ks:
            vistas[k] = r
        unicos.append(r)
    unicos += [s for s in sitio if s['id'] not in quitar]
    # Un grupo, un nombre: RansomLook escribe "vortex" y el Radar "Vortex".
    # Sin esto la pagina contaba dos grupos activos donde hay uno.
    nombre = {}
    for r in radar + unicos:
        k = grupo_clave(r['group'])
        if k and (k not in nombre or (r['origin'] != 'am-i-exposed' and nombre[k].islower())):
            nombre[k] = r['group']
    for r in unicos:
        k = grupo_clave(r['group'])
        if k:
            r['group'] = nombre[k]
    unicos.sort(key=lambda x: (x['day'], x['seen'], x['id']), reverse=True)
    return unicos


# --------------------------------------------------------------------- salidas

def publico(fila):
    return {k: fila[k] for k in ('id', 'day', 'seen', 'victim', 'group', 'type',
                                 'status', 'country', 'sector', 'victims', 'origin')} | {
        'source': fila['sources'][0]['name'],
        'sourceUrl': fila['sources'][0]['url'],
        'sources': fila['sources'],
    }


def dashboard(fila):
    iso = fila['country']
    radar = fila['origin'] != 'am-i-exposed'
    pais = fila.get('_country_es') if radar and fila.get('_country_es') not in (None, '', 'Sin identificar') else pais_es(iso)
    return {
        'id': fila['id'], 'day': fila['day'], 'date': fila['date'],
        'victim': fila['victim'],
        'country': pais or 'Sin identificar',
        'region': (fila.get('_region_es') if radar and fila.get('_region_es') else region_dashboard(iso)),
        'sector': (fila.get('_sector_es') if radar else
                   ('Otros / Sin identificar' if fila['sector'] == 'otros'
                    else SECTORES.get(fila['sector'], ('Otros / Sin identificar',))[0])),
        'group': fila['group'],
        'type': fila.get('_type_es') or TIPOS.get(fila['type'], ('Ransomware',))[0],
        'status': fila.get('_status_es') or ESTADOS.get(fila['status'], ('Reclamado por el grupo',))[0],
        'victims': fila['victims'],
        'prospect': fila['prospect'], 'prospectNote': fila['prospectNote'],
        'historical': fila['historical'], 'republished': fila['republished'],
        'source': ' + '.join(s['name'] for s in fila['sources']),
        'sourceUrl': fila['sources'][0]['url'],
        'origin': fila['origin'],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--radar-days', required=True)
    ap.add_argument('--site', default=os.path.join(ROOT, 'data', 'radar.json'))
    ap.add_argument('--public', required=True)
    ap.add_argument('--dashboard', required=True)
    a = ap.parse_args()

    radar = lee_radar(a.radar_days)
    sitio, fuentes_sitio = lee_sitio(a.site)
    filas = fusiona(radar, sitio)

    nombres = {}
    for f in filas:
        for s in f['sources']:
            n = (s.get('name') or '').strip()
            if n and n.lower() not in nombres:
                nombres[n.lower()] = n
    pub = {
        'generated': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
        'sources': fuentes_sitio,
        'all_sources': sorted(nombres.values(), key=str.lower),
        'items': [publico(f) for f in filas],
    }
    json.dump(pub, open(a.public, 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump([dashboard(f) for f in filas],
              open(a.dashboard, 'w', encoding='utf-8'), ensure_ascii=False)
    absorbidas = len(sitio) - sum(1 for f in filas if f['origin'] == 'am-i-exposed')
    print(json.dumps({'radar': len(radar), 'sitio': len(sitio), 'filas': len(filas),
                      'sitio_absorbidas': absorbidas,
                      'victimas': sum(f['victims'] for f in filas)}, ensure_ascii=False))


if __name__ == '__main__':
    main()

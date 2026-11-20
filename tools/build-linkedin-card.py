#!/usr/bin/env python3
"""Genera la 'foto del momento' para LinkedIn y el texto de la Alerta Am I Exposed.

Lee daily-hack.json (lo escribe tools/build-daily-hack.py con las MISMAS cifras
que la pagina publica), dibuja una tarjeta oscura 1080x1080 en SVG, la convierte
a PNG con cairosvg, y escribe el texto de la Alerta (corta y larga) por PLANTILLA
(cero costo de API). El dueno descarga el PNG y lo sube; no es un link, es la
imagen.

Uso:
  python3 -I tools/build-linkedin-card.py [--data daily-hack.json]
         [--out-png linkedin/alerta.png] [--out-txt linkedin/alerta.txt]
"""

import argparse
import datetime as dt
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
E = html.escape


def fmt(n):
    try:
        return f'{int(n):,}'.replace(',', ' ')  # espacio fino de miles
    except (TypeError, ValueError):
        return str(n)


def fecha_larga(iso):
    meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
             'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
    try:
        y, m, d = iso.split('-')
        return f'{int(d)} de {meses[int(m) - 1]} de {y}'
    except Exception:
        return iso


def fecha_corta(iso):
    try:
        y, m, d = iso.split('-')
        return f'{d}/{m}/{y}'
    except Exception:
        return iso


# ----------------------------------------------------------------- la tarjeta

def tarjeta_svg(d):
    date = d.get('date', '')
    week = d.get('week', 0)
    new = d.get('new', 0)
    latam = d.get('latam', 0)
    groups = d.get('groups', 0)
    top_sectors = d.get('top_sectors') or []
    top_sec = top_sectors[0] if top_sectors else None
    gov = d.get('gov', 0)

    sec_linea = ''
    if top_sec:
        sec_linea = f'{E(str(top_sec[0]))}, el sector más golpeado: {top_sec[1]} casos'

    # Paleta del sitio: fondo casi negro, acento rojo/naranja.
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1080" viewBox="0 0 1080 1080">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#121420"/>
      <stop offset="1" stop-color="#0B0C12"/>
    </linearGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#E2454F"/>
      <stop offset="1" stop-color="#F0921E"/>
    </linearGradient>
  </defs>
  <rect width="1080" height="1080" fill="url(#bg)"/>
  <rect x="0" y="0" width="1080" height="10" fill="url(#accent)"/>

  <text x="80" y="140" font-family="Arial, sans-serif" font-size="30" font-weight="700"
        letter-spacing="6" fill="#9AA0AD">RADAR DE ATAQUES · AM I EXPOSED</text>
  <text x="80" y="188" font-family="Arial, sans-serif" font-size="26" fill="#6B7180">{E(fecha_corta(date))}</text>

  <text x="80" y="360" font-family="Arial, sans-serif" font-size="200" font-weight="800"
        fill="#F2F3F7" letter-spacing="-4">{E(fmt(week))}</text>
  <text x="80" y="430" font-family="Arial, sans-serif" font-size="38" fill="#C8CDD8">
    empresas y entidades en sitios de filtración, últimos 7 días</text>

  <line x1="80" y1="500" x2="1000" y2="500" stroke="#262A36" stroke-width="2"/>

  <text x="80" y="590" font-family="Arial, sans-serif" font-size="30" fill="#9AA0AD">Últimas 24 horas</text>
  <text x="80" y="648" font-family="Arial, sans-serif" font-size="62" font-weight="700" fill="#E2454F">{E(fmt(new))}</text>

  <text x="400" y="590" font-family="Arial, sans-serif" font-size="30" fill="#9AA0AD">Grupos activos</text>
  <text x="400" y="648" font-family="Arial, sans-serif" font-size="62" font-weight="700" fill="#F2F3F7">{E(fmt(groups))}</text>

  <text x="700" y="590" font-family="Arial, sans-serif" font-size="30" fill="#9AA0AD">En Latinoamérica</text>
  <text x="700" y="648" font-family="Arial, sans-serif" font-size="62" font-weight="700" fill="#F0921E">{E(fmt(latam))}</text>

  <text x="80" y="748" font-family="Arial, sans-serif" font-size="34" fill="#C8CDD8">{sec_linea}</text>
  <text x="80" y="800" font-family="Arial, sans-serif" font-size="34" fill="#C8CDD8">{E(fmt(gov))} entidades de gobierno</text>

  <rect x="0" y="900" width="1080" height="180" fill="#171822"/>
  <text x="80" y="975" font-family="Arial, sans-serif" font-size="34" fill="#9AA0AD">Lista completa por país, industria y grupo, cada día:</text>
  <text x="80" y="1028" font-family="Arial, sans-serif" font-size="46" font-weight="700" fill="#F2F3F7">am-i-exposed.com/es/daily-hack</text>
</svg>'''


# ----------------------------------------------------------------- la Alerta

def alerta_texto(d):
    date = fecha_corta(d.get('date', ''))
    week = d.get('week', 0)
    new = d.get('new', 0)
    latam = d.get('latam', 0)
    groups = d.get('groups', 0)
    gov = d.get('gov', 0)
    us = d.get('us', 0)
    peru = d.get('peru') or []
    lc = d.get('latam_countries') or []
    top_sectors = d.get('top_sectors') or []
    sources = d.get('sources') or []

    paises = ', '.join(f'{c[0]} {c[1]}' for c in lc) if lc else ''
    paises_simple = ', '.join(c[0] for c in lc) if lc else ''
    sec = top_sectors[0] if top_sectors else None
    top5 = '; '.join(f'{s[0]} ({s[1]})' for s in top_sectors[:5]) if top_sectors else ''
    fuentes = ', '.join(sources) if sources else 'RansomLook, Have I Been Pwned'

    corta = f"""Alerta Am I Exposed · {date}

{fmt(new)} empresas y entidades aparecieron en sitios de filtración de ransomware en las últimas 24 horas.
{fmt(week)} en los últimos 7 días.
{fmt(latam)} en Latinoamérica{(': ' + paises_simple) if paises_simple else ''}.
{fmt(groups)} grupos criminales activos.
{(sec[0] + ', el sector más golpeado de la semana: ' + str(sec[1]) + ' casos.') if sec else ''}

Lista completa por país, industria y grupo, actualizada cada día:
am-i-exposed.com/es/daily-hack

Fuentes: {fuentes}"""

    peru_linea = ''
    if peru:
        peru_linea = f'En Perú la semana tuvo {len(peru)} caso(s): {", ".join(str(p) for p in peru[:5])}.'

    larga = f"""Alerta Am I Exposed · {date}

{fmt(week)} empresas y entidades en siete días. Esa es la cuenta de los sitios de filtración de ransomware de la última semana.

Un sitio de filtración es la página donde un grupo criminal publica a quién dice haber atacado, para presionar el pago. Aparecer ahí no prueba qué se llevaron: es el reclamo del grupo hasta que la víctima confirme.

La semana en cifras:
{fmt(groups)} grupos activos.
{fmt(us)} casos en Estados Unidos.
{fmt(latam)} en Latinoamérica{(': ' + paises) if paises else ''}.
{fmt(gov)} entidades de gobierno.
{('Los sectores más golpeados: ' + top5 + '.') if top5 else ''}
{peru_linea}

¿Qué es mejor para tu empresa: enterarte por tu propio monitoreo o por una lista como esta?

Lista completa: am-i-exposed.com/es/daily-hack
Fuentes: {fuentes}"""

    return corta.strip() + '\n\n' + ('=' * 40) + '\n\n' + larga.strip() + '\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default=os.path.join(ROOT, 'daily-hack.json'))
    ap.add_argument('--out-png', default=os.path.join(ROOT, 'linkedin', 'alerta.png'))
    ap.add_argument('--out-txt', default=os.path.join(ROOT, 'linkedin', 'alerta.txt'))
    a = ap.parse_args()

    d = json.load(open(a.data, encoding='utf-8'))
    os.makedirs(os.path.dirname(a.out_png), exist_ok=True)

    svg = tarjeta_svg(d)
    import cairosvg
    cairosvg.svg2png(bytestring=svg.encode('utf-8'), write_to=a.out_png,
                     output_width=1080, output_height=1080)
    open(a.out_txt, 'w', encoding='utf-8').write(alerta_texto(d))
    print(f"LinkedIn: {a.out_png} + {a.out_txt} (week={d.get('week')}, new={d.get('new')})")


if __name__ == '__main__':
    main()

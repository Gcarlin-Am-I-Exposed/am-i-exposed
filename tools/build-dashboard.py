#!/usr/bin/env python3
"""Arma el dashboard interno del Radar de Ataques como pagina web.

Lee data/radar.json (RansomLook + HIBP, ya clasificado por refresh-radar.py) y
deriva la vista que el dueno veia en el artefacto de claude.ai: tarjetas
(victimas, Peru/LatAm/Caribe, Peru, gobierno, prospectos), ventanas 7/30/Todo y
la lista por victima con marca de prospecto. No guarda nada nuevo: todo se
calcula de los mismos datos, asi que los numeros cuadran con la pagina publica.

La region y el prospecto NO viven en el dato: se derivan aqui con tools/_radar.py.
  - prospecto = victima de Peru/LatAm/Caribe con sector identificado (lead de
    diagnostico para am-i-exposed). Es una regla, no el juicio caso por caso que
    hacia la tarea cloud, asi que el numero puede diferir un poco.

Uso:
  python3 -I tools/build-dashboard.py [--data data/radar.json] [--out dashboard/index.html]
         [--embed]   # mete los datos en la pagina (preview local, sin gate)

Sin --embed la pagina es un cascaron que pide contrasena y hace fetch a
/api/monitor?op=dashboard (la version de produccion, con gate serverless).
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


def ahora_lima():
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=-5)))


def fila_vista(c):
    """Una fila de incidentes.json (ya traducida y con el flag de prospecto que
    trae la fusion) -> el objeto que consume el dashboard. Si la tarea cloud
    aporto casos curados, el prospecto refleja su criterio; si no, lo que haya
    en RansomLook/HIBP."""
    reg = c.get('region') or 'Sin identificar'
    sector = c.get('sector') or 'Sin identificar'
    url = c.get('sourceUrl') or ''
    if not (url.startswith('http://') or url.startswith('https://')):
        url = ''
    return {
        'victim': c.get('victim') or 'Sin nombre',
        'day': c.get('day') or c.get('date') or '',
        'group': c.get('group') or '',
        'country': c.get('country') or 'Sin identificar',
        'sector': sector,
        'sectorKey': sector,
        'status': c.get('status') or '',
        'source': c.get('source') or '',
        'url': url,
        'region': reg,
        'peru': reg == 'Perú',
        'gov': sector == 'Gobierno y Defensa',
        'latam': reg in ('Perú', 'Latinoamérica', 'Caribe'),
        'prospect': bool(c.get('prospect')),
    }


def construir(data):
    rows = data if isinstance(data, list) else data.get('items', data)
    items = [fila_vista(c) for c in rows]
    # Mas nuevo primero; sin fecha al final.
    items.sort(key=lambda x: x['day'] or '0000-00-00', reverse=True)
    dias = sorted({i['day'] for i in items if i['day']})
    hoy = ahora_lima().date().isoformat()
    ultimo = dias[-1] if dias else hoy
    return {
        'items': items,
        'generatedAt': ahora_lima().isoformat(timespec='minutes'),
        'today': hoy,
        'lastDay': ultimo,
    }


# ----------------------------------------------------------------- presentacion

CSS = """
*{box-sizing:border-box}
:root{
 --bg:#0E0F14;--surface:#17181F;--surface-2:#1E202A;--line:rgba(255,255,255,.08);
 --ink:#F2F3F7;--muted:#9AA0AD;--faint:#6B7180;
 --alert:#E2454F;--money:#F0921E;--good:#5FC79A;--accent:#5B8DEF}
html,body{margin:0;background:var(--bg);color:var(--ink);
 font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Inter,Helvetica,Arial,sans-serif;
 font-size:15px;line-height:1.5;-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:none}
.wrap{max-width:1120px;margin:0 auto;padding:28px 20px 80px}
h1{font-size:26px;margin:0 0 6px;letter-spacing:-.01em}
.sub{color:var(--muted);margin:0 0 22px;max-width:760px}
.sub b{color:var(--ink);font-weight:600}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 22px}
.tab{border:1px solid var(--line);background:var(--surface);color:var(--muted);
 padding:7px 14px;border-radius:999px;font-size:13px;cursor:pointer;font-weight:600}
.tab[aria-pressed=true]{background:#fff;color:#111;border-color:#fff}
.sep{width:1px;background:var(--line);margin:2px 4px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:0 0 26px}
.tile{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px 18px}
.tile .n{font-size:30px;font-weight:700;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.tile .l{color:var(--muted);font-size:13px;margin-top:2px}
.tile.p .n{color:var(--money)}
.tile.g .n{color:var(--accent)}
.bar{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:0 0 14px}
.bar input{flex:1;min-width:200px;background:var(--surface);border:1px solid var(--line);
 color:var(--ink);border-radius:10px;padding:9px 12px;font-size:14px}
.bar select{background:var(--surface);border:1px solid var(--line);color:var(--ink);
 border-radius:10px;padding:9px 12px;font-size:13px}
.count{color:var(--faint);font-size:13px}
table{width:100%;border-collapse:collapse;font-size:14px}
th{text-align:left;color:var(--faint);font-weight:600;font-size:12px;text-transform:uppercase;
 letter-spacing:.04em;padding:8px 10px;border-bottom:1px solid var(--line)}
td{padding:11px 10px;border-bottom:1px solid var(--line);vertical-align:top}
tr:hover td{background:var(--surface)}
.vic{font-weight:600}
.pill{display:inline-block;font-size:11px;font-weight:600;padding:2px 8px;border-radius:999px;
 border:1px solid var(--line);color:var(--muted);white-space:nowrap}
.pill.prospect{color:var(--money);border-color:rgba(240,146,30,.4);background:rgba(240,146,30,.08)}
.pill.gov{color:var(--accent);border-color:rgba(91,141,239,.4);background:rgba(91,141,239,.08)}
.flag{font-size:12px;color:var(--faint)}
.muted{color:var(--muted)}
.foot{color:var(--faint);font-size:12px;margin-top:26px}
#gate{max-width:360px;margin:16vh auto;text-align:center}
#gate input{width:100%;background:var(--surface);border:1px solid var(--line);color:var(--ink);
 border-radius:10px;padding:12px 14px;font-size:15px;margin:14px 0}
#gate button{width:100%;background:#fff;color:#111;border:0;border-radius:10px;
 padding:12px;font-size:15px;font-weight:700;cursor:pointer}
#gate .err{color:var(--alert);font-size:13px;min-height:18px}
@media(max-width:620px){th:nth-child(4),td:nth-child(4){display:none}}
"""

JS_RENDER = """
const fmt=n=>n.toLocaleString('es-PE');
const WIN={'7':7,'30':30,'all':99999};
let state={win:'30',q:'',sector:'',region:'',year:'',quarter:''};
let DATA=null;

function inWindow(it,days){
  if(days>=99999) return true;
  if(!it.day) return false;
  const last=DATA.lastDay, d=it.day;
  const dl=new Date(last+'T00:00:00'), dd=new Date(d+'T00:00:00');
  return (dl-dd)/86400000 < days;
}
function inCal(it){
  if(state.year && (!it.day||it.day.slice(0,4)!==state.year)) return false;
  if(state.quarter){ if(!it.day) return false; var m=parseInt(it.day.slice(5,7),10); if(Math.ceil(m/3)!==parseInt(state.quarter,10)) return false; }
  return true;
}
function pool(){
  // Si hay año o trimestre elegido, manda el filtro de calendario (ignora la ventana).
  if(state.year||state.quarter) return DATA.items.filter(inCal);
  return DATA.items.filter(it=>inWindow(it,WIN[state.win]));
}
function render(){
  const xs=pool();
  const tiles=[
    ['Víctimas publicadas', xs.length, ''],
    ['En Perú, LatAm y Caribe', xs.filter(x=>x.latam).length, 'g'],
    ['En Perú', xs.filter(x=>x.peru).length, 'g'],
    ['Entidades de gobierno', xs.filter(x=>x.gov).length, ''],
    ['Prospectos para diagnóstico', xs.filter(x=>x.prospect).length, 'p'],
  ];
  document.getElementById('tiles').innerHTML=tiles.map(([l,n,c])=>
    `<div class="tile ${c}"><div class="n">${fmt(n)}</div><div class="l">${l}</div></div>`).join('');
  // subtitle
  const grp={};xs.forEach(x=>{if(x.group&&x.group!=='—')grp[x.group]=(grp[x.group]||0)+1});
  const top=Object.entries(grp).sort((a,b)=>b[1]-a[1])[0];
  const win=(state.year||state.quarter)
    ? ((state.quarter?'Q'+state.quarter+' ':'')+(state.year||'todos los años'))
    : (state.win==='all'?'todo el periodo':`los últimos ${state.win} días`);
  document.getElementById('sub').innerHTML=
    `<b>${fmt(xs.length)}</b> víctimas publicadas en ${win} (al ${fmtDay(DATA.lastDay)}); `+
    `<b>${fmt(xs.filter(x=>x.latam).length)}</b> en Perú, LatAm o el Caribe.`+
    (top?` El grupo más activo fue <b>${esc(top[0])}</b> con ${top[1]}.`:'');
  // filters
  let rows=xs;
  if(state.q){const q=state.q.toLowerCase();rows=rows.filter(x=>
    (x.victim+' '+x.group+' '+x.country+' '+x.sector).toLowerCase().includes(q));}
  if(state.sector) rows=rows.filter(x=>x.sectorKey===state.sector);
  if(state.region==='latam') rows=rows.filter(x=>x.latam);
  else if(state.region==='peru') rows=rows.filter(x=>x.peru);
  else if(state.region==='resto') rows=rows.filter(x=>!x.latam);
  document.getElementById('count').textContent=fmt(rows.length)+' de '+fmt(xs.length);
  const body=rows.slice(0,600).map(x=>{
    const name=x.url?`<a href="${esc(x.url)}" target="_blank" rel="noopener noreferrer nofollow">${esc(x.victim)}</a>`:esc(x.victim);
    const tags=[x.prospect?'<span class="pill prospect">Prospecto</span>':'',
               x.gov?'<span class="pill gov">Gobierno</span>':''].join(' ');
    return `<tr><td><div class="vic">${name}</div><div class="flag">${esc(x.source)}</div></td>`+
      `<td>${esc(x.country)}</td><td>${esc(x.sector)} ${tags}</td>`+
      `<td class="muted">${esc(x.group&&x.group!=='—'?x.group:'')}</td>`+
      `<td class="muted">${esc(x.status)}</td><td class="muted">${fmtDay(x.day)}</td></tr>`;
  }).join('');
  document.getElementById('rows').innerHTML=body||'<tr><td colspan="6" class="muted">Sin resultados.</td></tr>';
  document.querySelectorAll('[data-win]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.win===state.win));
}
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function fmtDay(d){if(!/^\\d{4}-\\d{2}-\\d{2}$/.test(String(d==null?'':d)))return '';const[y,m,da]=d.split('-');return `${da}/${m}/${y}`;}
function wire(){
  document.querySelectorAll('[data-win]').forEach(b=>b.onclick=()=>{state.win=b.dataset.win;render();});
  document.getElementById('q').oninput=e=>{state.q=e.target.value;render();};
  document.getElementById('fs').onchange=e=>{state.sector=e.target.value;render();};
  document.getElementById('fr').onchange=e=>{state.region=e.target.value;render();};
  document.getElementById('fy').onchange=e=>{state.year=e.target.value;render();};
  document.getElementById('fq').onchange=e=>{state.quarter=e.target.value;render();};
}
function start(d){DATA=d;document.getElementById('app').style.display='';document.getElementById('gate').style.display='none';
  // sector options
  const secs={};DATA.items.forEach(x=>{if(x.sectorKey)secs[x.sectorKey]=x.sector});
  document.getElementById('fs').innerHTML='<option value="">Todos los sectores</option>'+
    Object.entries(secs).sort((a,b)=>a[1].localeCompare(b[1])).map(([k,v])=>`<option value="${esc(k)}">${esc(v)}</option>`).join('');
  // años disponibles (para el filtro por año/trimestre)
  var years={};DATA.items.forEach(x=>{if(x.day)years[x.day.slice(0,4)]=1});
  document.getElementById('fy').innerHTML='<option value="">Todos los años</option>'+
    Object.keys(years).sort().reverse().map(y=>`<option value="${esc(y)}">${esc(y)}</option>`).join('');
  wire();render();}
"""

SHELL = """
<div id="gate">
  <h1 style="font-size:22px">Radar de Ataques</h1>
  <p class="muted">Panel interno · Am I Exposed</p>
  <input id="pw" type="password" placeholder="Contraseña" autocomplete="current-password">
  <label style="display:flex;align-items:center;gap:8px;justify-content:center;margin:0 0 12px;color:var(--muted);font-size:13px;cursor:pointer"><input type="checkbox" id="showpw"> Mostrar contraseña</label>
  <button id="go">Entrar</button>
  <p class="err" id="gerr"></p>
</div>
<div id="app" style="display:none">
  <h1>Radar de Ataques</h1>
  <p class="sub" id="sub"></p>
  <div class="tabs">
    <button class="tab" data-win="7">7 días</button>
    <button class="tab" data-win="30" aria-pressed="true">30 días</button>
    <button class="tab" data-win="all">Todo</button>
  </div>
  <div class="tiles" id="tiles"></div>
  <div class="bar">
    <input id="q" placeholder="Buscar víctima, grupo, país...">
    <select id="fr"><option value="">Toda región</option><option value="peru">Perú</option><option value="latam">Perú/LatAm/Caribe</option><option value="resto">Resto del mundo</option></select>
    <select id="fs"></select>
    <select id="fy"></select>
    <select id="fq"><option value="">Todo el año</option><option value="1">Q1</option><option value="2">Q2</option><option value="3">Q3</option><option value="4">Q4</option></select>
    <span class="count" id="count"></span>
  </div>
  <table><thead><tr><th>Víctima</th><th>País</th><th>Sector</th><th>Grupo</th><th>Estado</th><th>Fecha</th></tr></thead>
  <tbody id="rows"></tbody></table>
  <p class="foot" id="foot"></p>
</div>
"""


def pagina(vista, embed):
    datos_js = (f"const EMBED={json.dumps(vista, ensure_ascii=False).replace(chr(60), chr(92)+'u003c')};"
                if embed else "const EMBED=null;")
    arranque = ("start(EMBED);" if embed else """
document.getElementById('go').onclick=async()=>{
  const pw=document.getElementById('pw').value;const err=document.getElementById('gerr');
  err.textContent='';try{
    const r=await fetch('/api/monitor?op=dashboard',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password:pw})});
    if(r.status===401){err.textContent='Contraseña incorrecta.';return;}
    if(!r.ok){err.textContent='Error al cargar.';return;}
    start(await r.json());
  }catch(e){err.textContent='Error de red.';}
};
document.getElementById('pw').addEventListener('keydown',e=>{if(e.key==='Enter')document.getElementById('go').click();});
document.getElementById('showpw').addEventListener('change',e=>{document.getElementById('pw').type=e.target.checked?'text':'password';});
""")
    gen = E(vista.get('generatedAt', ''))
    return f"""<!doctype html><html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Radar de Ataques · Panel interno</title>
<style>{CSS}</style></head>
<body><div class="wrap">{SHELL}</div>
<script>
{datos_js}
{JS_RENDER}
document.getElementById('foot').textContent='Generado {gen} (hora de Lima). Fuente: RansomLook y Have I Been Pwned.';
{arranque}
</script></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    # --data es incidentes.json (la vista fusionada, con prospecto). En Actions
    # se pasa /tmp/incidentes.json.
    ap.add_argument('--data', default=os.path.join(ROOT, 'incidentes.json'))
    ap.add_argument('--out', default=os.path.join(ROOT, 'dashboard', 'index.html'),
                    help='cascaron HTML con gate (o con datos embebidos si --embed)')
    ap.add_argument('--view-json', default=None,
                    help='escribe la vista calculada como JSON (lo que Actions sube a dashboard_snapshot)')
    ap.add_argument('--embed', action='store_true', help='mete los datos en la pagina (preview local)')
    a = ap.parse_args()
    data = json.load(open(a.data, encoding='utf-8'))
    vista = construir(data)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, 'w', encoding='utf-8').write(pagina(vista, a.embed))
    if a.view_json:
        json.dump(vista, open(a.view_json, 'w', encoding='utf-8'), ensure_ascii=False)
    n = len(vista['items'])
    pros = sum(1 for i in vista['items'] if i['prospect'])
    print(f"dashboard: {n} víctimas, {pros} prospectos -> {a.out}"
          + (f" + vista {a.view_json}" if a.view_json else "") + f" (embed={a.embed})")


if __name__ == '__main__':
    main()

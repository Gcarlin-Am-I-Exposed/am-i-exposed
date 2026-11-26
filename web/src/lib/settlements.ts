// Settlement page composition, ported faithfully from tools/build-settlement-pages.py
// render(). Data comes from the Python pipeline (data/settlements-content.json),
// which is untrusted scraper output: every dynamic value is HTML-escaped and every
// URL is validated (http/https only) before it reaches the page.

import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const DOM = 'https://www.am-i-exposed.com';

export interface SettlementRecord {
  tipo: string;
  slug: string;
  empresa: string;
  fondo: number | null;
  pago: number | null;
  premio: string | null;
  elegible: string | null;
  plazo: string | null;
  audiencia: string | null;
  sitio: string | null;
  caso: string | null;
  fuente: string;
  fuente_nombre: string;
  fuente_cao?: string | null;
  datos: string | string[] | null;
  estado_sede: string | null;
  desc?: string | null;
  fecha?: string | null;
  publicado?: string | null;
  afectados?: number | null;
  nacional?: boolean | null;
  estados_notificados?: string[] | null;
  comprobante?: string | null;
  filtracion?: boolean | null;
  hibp?: { cuentas: number } | null;
  claim_href: string | null;
  claim_display: string | null;
}

export interface FaqItem { q: string; a: string; }
export interface FactRow { k: string; v: string; }
export interface SettlementPage {
  slug: string;
  url: string;
  empresa: string;
  tipo: string;
  title: string;
  desc: string;
  h1: string;
  ledeHtml: string;
  facts: FactRow[];
  coveredHtml: string | null;
  exposed: string[];
  onRecordHtml: string | null;
  publishedHtml: string | null;
  claimHtml: string;
  sourceHtml: string;
  faq: FaqItem[];
  caveatHtml: string;
  ctaHtml: string;
  hibp: boolean;
  jsonld: unknown;
  // listing helpers
  pago: number | null;
  fondo: number | null;
  plazo: string | null;
  abierto: boolean;
}

// ---- helpers ported from the builder ----
export function esc(s: unknown): string {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
}

export function money(n: number | null | undefined): string | null {
  if (!n) return null;
  n = Math.trunc(n);
  if (n >= 1_000_000 && n % 100_000 === 0) {
    const v = n / 1_000_000;
    let s = `$${v.toFixed(1)}`.replace(/0+$/, '').replace(/\.$/, '');
    return s + ' million';
  }
  return '$' + n.toLocaleString('en-US');
}

export function fechaLarga(d: string | null | undefined): string {
  if (!d) return '';
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(d);
  if (!m) return d;
  const dt = new Date(Date.UTC(+m[1], +m[2] - 1, +m[3]));
  if (isNaN(dt.getTime())) return d;
  return dt.toLocaleDateString('en-US', {
    month: 'long', day: 'numeric', year: 'numeric', timeZone: 'UTC',
  });
}

function plazoPasado(plazo: string | null | undefined, today: Date): boolean | null {
  if (!plazo) return null;
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(plazo);
  if (!m) return null;
  const d = Date.UTC(+m[1], +m[2] - 1, +m[3]);
  const t = Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate());
  return d < t;
}

function safeUrl(u: string | null | undefined): string | null {
  if (!u) return null;
  return /^https?:\/\//i.test(u) ? u : null;
}

function collapse(s: string): string {
  return s.replace(/\s+/g, ' ').trim();
}

function stripTags(s: string): string {
  return collapse(s.replace(/<[^>]+>/g, ''));
}

// ---- data loading (build time) ----
let _cache: SettlementRecord[] | null = null;
export function loadRecords(): SettlementRecord[] {
  if (_cache) return _cache;
  const path = join(process.cwd(), '..', 'data', 'settlements-content.json');
  _cache = JSON.parse(readFileSync(path, 'utf-8')) as SettlementRecord[];
  return _cache;
}

// ---- the port of render() ----
export function composePage(p: SettlementRecord, today = new Date()): SettlementPage {
  const emp = p.empresa;
  const esAbierto = p.tipo === 'abierto';
  const esAcuerdo = p.tipo === 'acuerdo' || esAbierto;
  const url = `${DOM}/settlements/${p.slug}/`;
  const fondo = money(p.fondo);
  const pago = money(p.pago);
  const pasado = plazoPasado(p.plazo, today);

  // title + h1
  let h1: string, title: string;
  if (esAbierto) {
    const asunto = p.filtracion ? 'data breach' : 'class action';
    h1 = `${emp} ${asunto} settlement: how to claim`;
    title = `${emp} ${asunto} settlement claim | Am I Exposed?`;
  } else if (esAcuerdo) {
    h1 = `${emp} data breach settlement`;
    title = `${emp} data breach settlement | Am I Exposed?`;
  } else {
    h1 = `${emp} data breach lawsuit`;
    title = `${emp} data breach lawsuit | Am I Exposed?`;
  }

  // description (facts, not adjectives)
  const d: string[] = [];
  if (pago) d.push(`Paid up to ${pago} per person`);
  else if (fondo) d.push(`A ${fondo} fund`);
  if (p.plazo) d.push((pasado ? 'claims closed ' : 'claims close ') + fechaLarga(p.plazo));
  if (d.length === 0) d.push('A data breach lawsuit against ' + emp);
  let desc = d.join('. ') + '. Who was covered, what was exposed, and where the official claim site is.';
  desc = desc.slice(0, 300);

  // pasado_txt
  let pasadoTxt = '';
  if (pasado === true) {
    pasadoTxt = ` The claim window <strong>closed on ${esc(fechaLarga(p.plazo))}</strong>, so this one can no longer be claimed &mdash; but new settlements open all the time, and some are paying out right now. The free check tells you in seconds whether your email is in a breach that still pays.`;
  } else if (pasado === false) {
    pasadoTxt = ` Claims are accepted until <strong>${esc(fechaLarga(p.plazo))}</strong>.`;
  }

  // lede
  let lede: string;
  if (esAbierto) {
    const cuanto = pago
      ? `up to <strong>${esc(pago)} per person</strong>`
      : (fondo ? `a <strong>${esc(fondo)}</strong> fund` : 'compensation');
    const cierra = p.plazo
      ? `Claims close <strong>${esc(fechaLarga(p.plazo))}</strong>.`
      : 'No closing date has been published yet.';
    const sinPrueba = (p.comprobante || '').startsWith('n') ? ' No proof of purchase is required.' : '';
    lede = `${esc(emp)} is paying ${cuanto}, and the claim window is <strong>still open</strong>. ${cierra}${sinPrueba}`;
  } else if (esAcuerdo) {
    if (pago && fondo) lede = `${esc(emp)} settled a data breach claim for ${esc(fondo)}, with up to <strong>${esc(pago)} per person</strong>.${pasadoTxt}`;
    else if (pago) lede = `${esc(emp)} settled a data breach claim that paid up to <strong>${esc(pago)} per person</strong>.${pasadoTxt}`;
    else if (fondo) lede = `${esc(emp)} settled a data breach claim for <strong>${esc(fondo)}</strong>.${pasadoTxt}`;
    else lede = `${esc(emp)} settled a data breach claim.${pasadoTxt}`;
  } else {
    const vivo = p.tipo === 'investigacion abierta';
    const cuando = p.fecha ? ` after the breach reported in ${esc(p.fecha)}` : '';
    lede = `Lawyers are ${vivo ? 'currently investigating' : 'pursuing'} claims against ${esc(emp)}${cuando}. No settlement has been announced, so there is nothing to claim yet.`;
  }

  // facts table
  const facts: FactRow[] = [];
  if (fondo) facts.push({ k: 'Settlement fund', v: esc(fondo) });
  if (pago) facts.push({ k: 'Maximum per person', v: esc(pago) });
  if (p.premio) facts.push({ k: 'What it covered', v: esc(collapse(p.premio)) });
  if (p.plazo) facts.push({ k: pasado ? 'Claim deadline (passed)' : 'Claim deadline', v: esc(fechaLarga(p.plazo)) });
  if (p.audiencia) facts.push({ k: 'Final approval hearing', v: esc(fechaLarga(p.audiencia)) });
  if (p.caso) facts.push({ k: 'Case', v: esc(collapse(p.caso).slice(0, 160)) });
  if (p.estado_sede) facts.push({ k: 'Filed in', v: esc(p.estado_sede) });

  // who was covered
  const coveredHtml = p.elegible ? esc(collapse(p.elegible)) : null;

  // what was exposed
  let exposed: string[] = [];
  if (p.datos) {
    const raw = p.datos;
    const list = Array.isArray(raw)
      ? raw.map((x) => String(x).trim()).filter(Boolean)
      : String(raw).split(/[,;]/).map((x) => x.trim()).filter(Boolean);
    exposed = list.slice(0, 12).map((x) => esc(x));
  }

  // what is on the record
  const hechos: string[] = [];
  if (p.fecha) hechos.push(`The incident is recorded as ${esc(p.fecha)}`);
  if (p.afectados != null) {
    const n = Number(p.afectados);
    if (Number.isFinite(n) && n > 0) hechos.push(`about ${n.toLocaleString('en-US')} people were affected`);
  }
  if (p.estado_sede) hechos.push(`the company is based in ${esc(p.estado_sede)}`);
  const nEst = (p.estados_notificados || []).length;
  if (p.nacional) hechos.push('the breach was reported nationally');
  else if (nEst) hechos.push(`notice went to attorneys general in ${nEst} ${nEst === 1 ? 'state' : 'states'}`);
  let onRecordHtml: string | null = null;
  if (hechos.length) {
    let frase: string;
    if (hechos.length > 2) frase = hechos.slice(0, -1).join(', ') + ', and ' + hechos[hechos.length - 1];
    else frase = hechos[0] + (hechos.length > 1 ? ', and ' + hechos[hechos.length - 1] : '');
    onRecordHtml = `${frase}.`;
  }

  // published line
  let publishedHtml: string | null = null;
  if (p.publicado) {
    const estadoTxt = ({
      'investigacion abierta': 'Lawyers were still taking claims at that point.',
      'acuerdo': 'A settlement followed.',
      'demanda presentada': 'A complaint had been filed.',
    } as Record<string, string>)[p.tipo] || '';
    publishedHtml = `The case was first listed on ${esc(p.publicado)}. ${estadoTxt}`;
  }

  // where to claim
  const href = safeUrl(p.claim_href);
  const sitio = p.claim_display || '';
  let claimHtml: string;
  if (href) {
    if (esAbierto) {
      claimHtml = `File at <a href="${esc(href)}" rel="nofollow noopener">${esc(sitio)}</a>, the site run by the administrator the court appointed. That is the only place a claim counts, it is free, and nobody should ever charge you to file one.`;
    } else if (pasado === true) {
      claimHtml = `The administrator&rsquo;s site is <a href="${esc(href)}" rel="nofollow noopener">${esc(sitio)}</a>. The window is closed, so it is there for the record, not to file.`;
    } else {
      claimHtml = `Claims go through the court-appointed administrator, at <a href="${esc(href)}" rel="nofollow noopener">${esc(sitio)}</a>. That is the only place a claim counts. Nobody should ever charge you to file one.`;
    }
  } else {
    claimHtml = 'We do not have an administrator&rsquo;s site on record for this one. The case page below is the primary source we used, and any claim site would be named there.';
  }
  const fuenteHref = safeUrl(p.fuente);
  const sourceHtml = `Source: ${fuenteHref ? `<a href="${esc(fuenteHref)}" rel="nofollow noopener">${esc(p.fuente_nombre)}</a>` : esc(p.fuente_nombre)}` +
    (p.fuente_cao && safeUrl(p.fuente_cao) ? ` &middot; <a href="${esc(p.fuente_cao)}" rel="nofollow noopener">ClassAction.org</a>` : '');

  // FAQ
  const faq: FaqItem[] = [];
  if (esAbierto) {
    if (p.plazo && pasado === false) faq.push({ q: `Is the ${emp} settlement still open?`, a: `Yes. Claims are open until <strong>${esc(fechaLarga(p.plazo))}</strong>.` });
    else if (pasado === true) faq.push({ q: `Can you still claim the ${emp} settlement?`, a: `No. The claim window closed on <strong>${esc(fechaLarga(p.plazo))}</strong>.` });
    else faq.push({ q: `Is the ${emp} settlement still open?`, a: 'Yes, the claim window is open.' });
  } else if (esAcuerdo) {
    if (pasado === true) faq.push({ q: `Can you still claim the ${emp} settlement?`, a: `No. The claim window closed on <strong>${esc(fechaLarga(p.plazo))}</strong>.` });
    else if (p.plazo && pasado === false) faq.push({ q: `Is the ${emp} settlement still open?`, a: `Yes. Claims are accepted until <strong>${esc(fechaLarga(p.plazo))}</strong>.` });
    else faq.push({ q: `What was the ${emp} data breach settlement?`, a: `${esc(emp)} settled a data breach claim. The amount and the official claim site are listed above.` });
  } else {
    faq.push({ q: `Can you claim money from the ${emp} case yet?`, a: 'Not yet. No settlement has been announced, so there is nothing to claim. This is the stage at which it is worth knowing your data is involved, so you are not surprised by a notice letter later.' });
  }
  if (pago) {
    let aMonto = `Up to <strong>${esc(pago)} per person</strong>.`;
    if (fondo) aMonto += ` The total settlement fund was ${esc(fondo)}.`;
    faq.push({ q: `How much can you get from the ${emp} settlement?`, a: aMonto });
  } else if (fondo) {
    faq.push({ q: `How much was the ${emp} settlement?`, a: `A <strong>${esc(fondo)}</strong> fund.` });
  }
  if (exposed.length) {
    faq.push({ q: `What information did the ${emp} breach expose?`, a: exposed.slice(0, 8).join(', ') + '.' });
  }
  if (href && pasado !== true) {
    faq.push({ q: `Where do you file a ${emp} claim?`, a: `On the court-appointed administrator&rsquo;s official site, <a href="${esc(href)}" rel="nofollow noopener">${esc(sitio)}</a>. It is the only place a claim counts, and filing is always free.` });
  }

  const caveatHtml = 'Being in the breach is not the same as being in the class. Class membership usually turns on having received the company&rsquo;s own notice letter, and only the settlement administrator can confirm it. We are not lawyers, we take no fee from any claim, and we never file on anyone&rsquo;s behalf.';

  // CTA bridge to the free check
  let ctaHtml: string;
  if (p.hibp) {
    const n = Number(p.hibp.cuentas);
    ctaHtml = `This one is in the breach data we check against: ${Number.isFinite(n) ? n.toLocaleString('en-US') : '?'} accounts. The check is free, takes seconds, needs no account, and we do not store your address.`;
  } else {
    ctaHtml = 'Free, no account, and we do not store your address. If a company that leaked your data ends up paying, that is how you find out in time.';
  }

  // JSON-LD
  const graph: unknown[] = [
    {
      '@type': 'Article', headline: h1, description: desc, inLanguage: 'en',
      url, mainEntityOfPage: url, about: { '@type': 'Organization', name: emp },
      isPartOf: { '@type': 'CollectionPage', name: 'Data breach settlements', url: `${DOM}/settlements/` },
    },
    {
      '@type': 'BreadcrumbList', itemListElement: [
        { '@type': 'ListItem', position: 1, name: 'Home', item: DOM + '/' },
        { '@type': 'ListItem', position: 2, name: 'Settlements', item: `${DOM}/settlements/` },
        { '@type': 'ListItem', position: 3, name: emp, item: url },
      ],
    },
  ];
  if (faq.length) {
    graph.push({
      '@type': 'FAQPage',
      mainEntity: faq.map((f) => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: stripTags(f.a) } })),
    });
  }
  const jsonld = { '@context': 'https://schema.org', '@graph': graph };

  return {
    slug: p.slug, url, empresa: emp, tipo: p.tipo, title, desc, h1,
    ledeHtml: lede, facts, coveredHtml, exposed, onRecordHtml, publishedHtml,
    claimHtml, sourceHtml, faq, caveatHtml, ctaHtml, hibp: !!p.hibp, jsonld,
    pago: p.pago, fondo: p.fondo, plazo: p.plazo, abierto: esAbierto,
  };
}

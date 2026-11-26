// Slim index of the real US class-action settlements that are keyed to a HIBP
// breach name. Used to match a scan's breaches to settlements the visitor may
// qualify for, client-side, without touching the paid API. Source: repo-root
// settlements.json (.filas) — the same file api/report.js matches against. These
// are public settlement facts (company, published per-person max, deadline,
// official claim site, eligibility), safe to ship to the browser. Loaded at
// build; the match itself runs in the page so no email reaches a settlement call.

import { readFileSync } from 'node:fs';
import { join } from 'node:path';

export interface SettlementIndexRow {
  hibp: string;              // HIBP breach Name this settlement is keyed to
  slug: string;
  empresa: string;
  porPersona: number | null; // administrator's published per-person max, verbatim
  plazo: string | null;      // claim deadline ISO (yyyy-mm-dd) or null
  sitio: string | null;      // official claim-site host
  elegible: string | null;   // eligibility text, verbatim
}

let _cache: SettlementIndexRow[] | null = null;

export function settlementIndex(): SettlementIndexRow[] {
  if (_cache) return _cache;
  const path = join(process.cwd(), '..', 'settlements.json');
  const raw = JSON.parse(readFileSync(path, 'utf-8'));
  const filas: unknown = raw?.filas;
  _cache = (Array.isArray(filas) ? filas : [])
    .filter((r: any) => r && typeof r.hibp === 'string' && r.hibp)
    .map((r: any): SettlementIndexRow => ({
      hibp: r.hibp,
      slug: typeof r.slug === 'string' ? r.slug : '',
      empresa: r.empresa || r.titulo || r.hibp,
      porPersona: typeof r.porPersona === 'number' ? r.porPersona : null,
      plazo: typeof r.plazo === 'string' ? r.plazo : null,
      sitio: typeof r.sitio === 'string' && r.sitio ? r.sitio : null,
      elegible: typeof r.elegible === 'string' && r.elegible ? r.elegible : null,
    }));
  return _cache;
}

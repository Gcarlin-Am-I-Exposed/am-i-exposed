// Daily Hack ("who got hacked today") data, from the Python radar pipeline.
// daily-hack.json = the aggregate summary; data/radar.json = the raw items.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

export interface DHSummary {
  date: string; new: number; week: number; from: string; to: string;
  latam: number; latam_countries: [string, number][]; peru: string[];
  us: number; groups: number; top_groups: [string, number][];
  top_sectors: [string, number][]; gov: number; sources: string[];
}

export interface DHItem {
  victim: string; group: string; sector: string; country: string;
  status: string; type: string; source: string; sourceUrl: string;
}

function root(file: string): string {
  return join(process.cwd(), '..', file);
}

let _sum: DHSummary | null = null;
export function loadSummary(): DHSummary {
  if (!_sum) _sum = JSON.parse(readFileSync(root('daily-hack.json'), 'utf-8'));
  return _sum!;
}

export function loadTodayItems(date: string): DHItem[] {
  const all = JSON.parse(readFileSync(root('data/radar.json'), 'utf-8')).items as any[];
  return all
    .filter((it) => it.day === date)
    .map((it) => ({
      victim: String(it.victim || '').trim(),
      group: String(it.group || '').trim(),
      sector: String(it.sector || '').trim(),
      country: String(it.country || '').trim(),
      status: String(it.status || '').trim(),
      type: String(it.type || '').trim(),
      source: String(it.source || '').trim(),
      sourceUrl: /^https?:\/\//i.test(it.sourceUrl || '') ? it.sourceUrl : '',
    }))
    .filter((it) => it.victim);
}

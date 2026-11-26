import { loadRecords } from '../lib/settlements';

const SITE = 'https://www.am-i-exposed.com';

// Bilingual page pairs (EN + its translated ES slug). Each emits two <url>
// entries carrying en/es/x-default alternates, mirroring the live sitemap.
const PAIRS: { en: string; es: string }[] = [
  { en: '/', es: '/es/' },
  { en: '/pricing/', es: '/es/precios/' },
  { en: '/faq/', es: '/es/preguntas-frecuentes/' },
  { en: '/privacy/', es: '/es/privacidad/' },
  { en: '/terms/', es: '/es/terminos/' },
  { en: '/us-privacy-notice/', es: '/es/aviso-privacidad-eeuu/' },
  { en: '/daily-hack/', es: '/es/daily-hack/' },
  { en: '/what-to-do-if-your-email-was-leaked/', es: '/es/que-hacer-si-se-filtro-mi-correo/' },
  { en: '/how-to-know-if-your-password-was-leaked/', es: '/es/como-saber-si-mi-contrasena-fue-filtrada/' },
];

export async function GET() {
  const recs = loadRecords();
  const parts: string[] = [];

  for (const p of PAIRS) {
    const alts =
      `<xhtml:link rel="alternate" hreflang="en" href="${SITE}${p.en}"/>` +
      `<xhtml:link rel="alternate" hreflang="es" href="${SITE}${p.es}"/>` +
      `<xhtml:link rel="alternate" hreflang="x-default" href="${SITE}${p.en}"/>`;
    for (const loc of [p.en, p.es]) {
      parts.push(`<url><loc>${SITE}${loc}</loc>${alts}</url>`);
    }
  }

  // Settlements hub + the EN-only detail pages (US lawsuits).
  parts.push(`<url><loc>${SITE}/settlements/</loc></url>`);
  for (const r of recs) {
    parts.push(`<url><loc>${SITE}/settlements/${r.slug}/</loc></url>`);
  }

  const xml =
    `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n` +
    parts.join('\n') +
    `\n</urlset>\n`;

  return new Response(xml, {
    headers: { 'Content-Type': 'application/xml; charset=utf-8' },
  });
}

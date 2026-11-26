// Bilingual copy for the rebuilt home (Ruta B). EN at /, ES at /es/.
// Keep facts verifiable: no summed amounts, no "owed", relabeled single-case payout.

export type Lang = 'en' | 'es';

export interface HomeStrings {
  htmlLang: string;
  ogLocale: string;
  title: string;
  metaDesc: string;
  navHow: string;
  navSettle: string;
  navPrice: string;
  heroTitle: string;
  heroSub: string;
  heroCta: string;
  heroTrust: string;
  emailPh: string;
  resEyebrow: string;
  resH: string;
  resLede: string;
  exLabel: string;
  resCount: string;
  amtLab: string;
  resMax: string;
  chipOk: string;
  chipChk: string;
  ctaReport: string;
  exCtaFree: string;
  ctaAlerts: string;
  ctaNote: string;
  openTag: string;
  openH: string;
  openLede: string;
  statOpen: string;
  statTracked: string;
  statMax: string;
  browse: string;
  priceTag: string;
  priceH: string;
  p1t: string;
  p1p: string;
  p1a: string;
  p1b: string;
  p1c: string;
  p1cta: string;
  p2t: string;
  p2p: string;
  p2a: string;
  p2b: string;
  p2c: string;
  p2cta: string;
  disc: string;
  altHome: string;
}

export const strings: Record<Lang, HomeStrings> = {
  en: {
    htmlLang: 'en',
    ogLocale: 'en_US',
    title: 'Am I Exposed? — Check your email for breaches and settlements',
    metaDesc:
      "Check your email against known data breaches and the settlements they led to. Free, we don't store your email.",
    navHow: 'How it works',
    navSettle: 'Open settlements',
    navPrice: 'Pricing',
    heroTitle: 'You may be owed money — and nobody told you!',
    heroSub:
      'Check your email against known data breaches and the real class-action settlements they led to.',
    heroCta: 'Check my email',
    heroTrust: "Free · We don't store your email · Results in seconds",
    emailPh: 'you@email.com',
    resEyebrow: 'What a result looks like',
    resH: 'Your money, itemized — not a vague promise.',
    resLede:
      "After you confirm it's your email, every line shows the real payout range and its source. We never add maximums together.",
    exLabel: 'Example',
    resCount: 'You may qualify for 3 open settlements',
    amtLab: 'top single-case payout',
    resMax: 'Up to $5,000 more with documented losses',
    chipOk: 'Likely eligible',
    chipChk: 'Check eligibility',
    ctaReport: 'Get relief now — step by step · $5',
    exCtaFree: 'See my free full report',
    ctaAlerts: 'Get breach alerts',
    ctaNote: 'Your full report is free. Claim links are always free.',
    openTag: 'Open settlements',
    openH: 'The settlements companies are paying right now.',
    openLede:
      "Companies that leak data settle class actions and pay the people affected. We track every open one. Search a company you've dealt with and see what they're paying.",
    statOpen: 'open to claim now',
    statTracked: 'settlements tracked',
    statMax: 'top single-case payout',
    browse: 'Browse all settlements →',
    priceTag: 'Pricing',
    priceH: 'Your full report is free. $5 for the step-by-step.',
    p1t: 'Step-by-step guide',
    p1p: 'one-time',
    p1a: 'Lock down every exposed account, step by step',
    p1b: 'File each settlement claim the right way',
    p1c: "Your free report shows what's exposed — this shows what to do",
    p1cta: 'Get relief now — step by step · $5',
    p2t: 'Monitoring',
    p2p: '/mo · or $39.99/yr',
    p2a: 'We re-scan and alert you on new breaches',
    p2b: 'New settlements you may qualify for',
    p2c: '14-day free trial · cancel in one click',
    p2cta: 'Start my 14-day free trial',
    disc:
      "We're not a law firm and we don't file claims for you. We're not affiliated with the court or the claims administrator. The administrator decides eligibility. Companies, amounts and dates shown above are example data.",
    altHome: 'Am I Exposed? home',
  },
  es: {
    htmlLang: 'es',
    ogLocale: 'es_US',
    title: 'Am I Exposed? — Revisa tu email en filtraciones y acuerdos',
    metaDesc:
      'Revisa tu email en filtraciones conocidas y en los acuerdos que pagaron por ellas. Gratis, no guardamos tu email.',
    navHow: 'Cómo funciona',
    navSettle: 'Acuerdos abiertos',
    navPrice: 'Precios',
    heroTitle: 'Puede que te deban dinero. ¡Y nadie te avisó!',
    heroSub:
      'Revisa tu email en filtraciones conocidas y en las demandas colectivas reales que pagaron por ellas.',
    heroCta: 'Revisar mi email',
    heroTrust: 'Gratis · No guardamos tu email · Resultado en segundos',
    emailPh: 'tu@email.com',
    resEyebrow: 'Así se ve un resultado',
    resH: 'Tu dinero, detallado — no una promesa vaga.',
    resLede:
      'Después de confirmar que es tu email, cada línea muestra el rango real de pago y su fuente. Nunca sumamos los máximos.',
    exLabel: 'Ejemplo',
    resCount: 'Podrías calificar para 3 acuerdos abiertos',
    amtLab: 'pago más alto en un caso',
    resMax: 'Hasta $5,000 más con pérdidas documentadas',
    chipOk: 'Probablemente elegible',
    chipChk: 'Revisar elegibilidad',
    ctaReport: 'Recupera la tranquilidad, paso a paso · $5',
    exCtaFree: 'Ver mi reporte gratis',
    ctaAlerts: 'Recibir alertas',
    ctaNote: 'Tu reporte completo es gratis. Los enlaces de reclamo siempre son gratis.',
    openTag: 'Acuerdos abiertos',
    openH: 'Los acuerdos que las empresas están pagando ahora.',
    openLede:
      'Las empresas que filtran datos cierran demandas colectivas y pagan a los afectados. Seguimos cada acuerdo abierto. Busca una empresa con la que trataste y mira lo que están pagando.',
    statOpen: 'abiertos para reclamar ahora',
    statTracked: 'acuerdos en seguimiento',
    statMax: 'pago más alto en un caso',
    browse: 'Ver todos los acuerdos →',
    priceTag: 'Precios',
    priceH: 'Tu reporte completo es gratis. $5 por el paso a paso.',
    p1t: 'Guía paso a paso',
    p1p: 'pago único',
    p1a: 'Asegura cada cuenta expuesta, paso a paso',
    p1b: 'Presenta cada reclamo de la forma correcta',
    p1c: 'Tu reporte gratis muestra qué pasó — esto muestra qué hacer',
    p1cta: 'Recupera la tranquilidad, paso a paso · $5',
    p2t: 'Monitoreo',
    p2p: '/mes · o $39.99/año',
    p2a: 'Re-escaneamos y te avisamos de nuevas filtraciones',
    p2b: 'Nuevos acuerdos para los que podrías calificar',
    p2c: 'Prueba gratis de 14 días · cancela en un clic',
    p2cta: 'Empezar mi prueba gratis de 14 días',
    disc:
      'No somos un estudio de abogados y no presentamos reclamos por ti. No estamos afiliados al tribunal ni al administrador. El administrador decide la elegibilidad. Las empresas, montos y fechas de arriba son datos de ejemplo.',
    altHome: 'Inicio de Am I Exposed?',
  },
};

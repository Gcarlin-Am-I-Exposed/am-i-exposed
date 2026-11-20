// El correo diario del Radar de Ataques para el dueño: el texto de la Alerta
// (corta y larga) y la tarjeta de LinkedIn como adjunto PNG, listo para subir.
// Lo dispara el workflow radar-daily.yml con un POST autenticado por CRON_SECRET,
// pasando el texto y la imagen en base64 en el cuerpo (así no depende de que el
// despliegue de la página ya esté arriba).
//
// Cuelga de api/monitor.js (?op=daily-radar). Fail-closed como los otros jobs:
// sin CRON_SECRET es 503, un bearer malo o ausente es 401.

import { authorizeCron } from './_breach-watch.mjs';
import { readBody } from './_shared.js';
import { sendDailyRadar } from './_email.js';

// maxBody de monitor.js cubre el adjunto (~100 KB en base64).

function alertRecipient() {
    return process.env.ALERT_EMAIL || process.env.ALERT_MAIL || null;
}

function esc(s) {
    return String(s ?? '')
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

export async function handleDailyRadar(req, res) {
    if (req.method !== 'POST') {
        res.setHeader('Allow', 'POST');
        return res.status(405).json({ error: 'Method not allowed' });
    }
    const secret = process.env.CRON_SECRET;
    if (!secret) return res.status(503).json({ error: 'Not configured' });
    if (!authorizeCron(req.headers.authorization || '', secret)) {
        return res.status(401).json({ error: 'Unauthorized' });
    }

    const to = alertRecipient();
    if (!to) {
        console.error('Daily radar: no recipient (ALERT_EMAIL/ALERT_MAIL)');
        return res.status(503).json({ error: 'No recipient' });
    }

    const body = readBody(req) || {};
    const date = typeof body.date === 'string' ? body.date.slice(0, 20) : '';
    const text = typeof body.text === 'string' ? body.text : '';
    const png = typeof body.pngBase64 === 'string' ? body.pngBase64 : '';
    if (!text) return res.status(400).json({ error: 'Missing text' });

    const subject = `Radar de Ataques · ${date || 'hoy'}`;
    const html = `<!doctype html><html><head><meta charset="utf-8"></head>
<body style="margin:0;background:#FAFAFA;">
<div style="max-width:620px;margin:0 auto;padding:28px 22px;
            font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;
            font-size:15px;line-height:1.6;color:#111;">
  <p style="margin:0 0 6px;font-weight:700;font-size:17px;">Radar de Ataques · Am I Exposed?</p>
  <p style="margin:0 0 18px;color:#666;font-size:13px;">La tarjeta para LinkedIn va adjunta (PNG, lista para subir). Debajo, el texto de la Alerta: versión corta y versión larga.</p>
  <pre style="white-space:pre-wrap;font-family:inherit;font-size:14px;line-height:1.55;color:#1a1a1a;margin:0;padding:16px;background:#fff;border:1px solid #eee;border-radius:10px;">${esc(text)}</pre>
  <p style="margin:22px 0 0;font-size:12px;color:#999;">Correo automático del Radar de Ataques. Página pública: am-i-exposed.com/es/daily-hack</p>
</div></body></html>`;

    const attachments = png ? [{ content: png, name: `alerta-${(date || 'hoy').replace(/[^0-9A-Za-z-]/g, '')}.png` }] : [];
    const okMail = await sendDailyRadar({ to, subject, html, attachments });
    return res.status(okMail ? 200 : 502).json({ ok: okMail, attached: attachments.length > 0 });
}

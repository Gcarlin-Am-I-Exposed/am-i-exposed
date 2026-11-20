// Panel interno del Radar de Ataques. Sirve el snapshot que GitHub Actions sube
// a la tabla dashboard_snapshot cada día, SOLO tras una contraseña. Es una
// herramienta interna, no una función pública: sin la clave no devuelve nada.
//
// Cuelga de api/monitor.js (?op=dashboard) para no sumar una función serverless
// más (el plan Hobby topa en 12). Vercel no convierte un archivo _*.mjs en ruta.

import { timingSafeEqual } from 'node:crypto';
import { readBody, sbSelect, clientIp, rateLimitOk, makeLocalLimiter } from './_shared.js';

// Respaldo en memoria si el limitador de Postgres no responde: no deja que un
// fallo de base de datos abra la puerta a fuerza bruta en esta instancia.
const localLimiter = makeLocalLimiter(20, 10 * 60 * 1000);

function safeEqual(given, expected) {
    const a = Buffer.from(String(given));
    const b = Buffer.from(String(expected));
    // timingSafeEqual exige misma longitud; distinta longitud = no coincide.
    if (a.length !== b.length) return false;
    return timingSafeEqual(a, b);
}

export async function handleDashboard(req, res) {
    if (req.method !== 'POST') {
        res.setHeader('Allow', 'POST');
        return res.status(405).json({ error: 'Method not allowed' });
    }

    const expected = process.env.DASHBOARD_PASSWORD;
    if (!expected) {
        console.error('DASHBOARD_PASSWORD not configured');
        return res.status(503).json({ error: 'Not configured' });
    }

    // Freno a la fuerza bruta: 20 intentos por IP cada 10 minutos. El contador
    // vive en Postgres (vale entre instancias); si no responde, cae al local.
    const ip = clientIp(req) || 'unknown';
    const shared = await rateLimitOk(`dashpw:${ip}`, 20, 600);
    const overLimit = shared === null ? localLimiter(ip) : !shared;
    if (overLimit) {
        res.setHeader('Retry-After', '600');
        return res.status(429).json({ error: 'Too many attempts' });
    }

    const body = readBody(req) || {};
    const given = typeof body.password === 'string' ? body.password : '';
    if (!safeEqual(given, expected)) {
        return res.status(401).json({ error: 'Unauthorized' });
    }

    const { ok, rows } = await sbSelect('dashboard_snapshot?id=eq.latest&select=data');
    if (!ok || !rows.length || !rows[0]?.data) {
        return res.status(404).json({ error: 'No snapshot yet' });
    }

    res.setHeader('Cache-Control', 'no-store');
    return res.status(200).json(rows[0].data);
}

// Public endpoint — the desktop app calls this to begin a pairing flow. No
// auth required here; the code alone grants nothing until a signed-in
// browser session approves it against a real user_id (see approve.js).
import { ensureSchema, requireDb, DbNotConfigured } from '../_lib/db.js';
import { generatePairingCode } from '../_lib/auth.js';

const EXPIRES_MINUTES = 10;

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');

  if (req.method === 'OPTIONS') {
    res.status(204).end();
    return;
  }
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed. Use POST.' });
    return;
  }

  try {
    await ensureSchema();
    const db = requireDb();

    let code;
    for (let attempt = 0; attempt < 5; attempt++) {
      code = generatePairingCode();
      const existing = await db`SELECT 1 FROM device_logins WHERE code = ${code}`;
      if (existing.length === 0) break;
    }

    const expiresAt = new Date(Date.now() + EXPIRES_MINUTES * 60 * 1000).toISOString();
    await db`
      INSERT INTO device_logins (code, status, expires_at) VALUES (${code}, 'pending', ${expiresAt})
    `;

    res.status(200).json({ code, expires_in_seconds: EXPIRES_MINUTES * 60 });
  } catch (err) {
    if (err instanceof DbNotConfigured) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.status(500).json({ error: err.message });
  }
}

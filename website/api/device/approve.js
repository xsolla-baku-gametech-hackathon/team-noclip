// Called by the logged-in browser tab after the user types/confirms the
// pairing code shown by the desktop app. Requires a valid web session —
// the device token is minted for whoever is authenticated in THIS request,
// never for an id supplied in the request body.
import { ensureSchema, requireDb, DbNotConfigured } from '../_lib/db.js';
import { getAuthedUserId, generateDeviceToken, hashDeviceToken } from '../_lib/auth.js';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', req.headers.origin || '*');
  res.setHeader('Access-Control-Allow-Credentials', 'true');
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
    const userId = await getAuthedUserId(req);
    if (!userId) {
      res.status(401).json({ error: 'Not signed in.' });
      return;
    }

    const { code } = req.body || {};
    if (!code) {
      res.status(400).json({ error: 'Missing code.' });
      return;
    }

    await ensureSchema();
    const db = requireDb();

    const rows = await db`
      SELECT code, status, expires_at FROM device_logins WHERE code = ${code.toUpperCase()}
    `;
    if (rows.length === 0) {
      res.status(404).json({ error: 'Invalid pairing code.' });
      return;
    }
    const login = rows[0];
    if (login.status !== 'pending') {
      res.status(409).json({ error: 'This code was already used.' });
      return;
    }
    if (new Date(login.expires_at).getTime() < Date.now()) {
      res.status(410).json({ error: 'This code has expired. Restart login from the app.' });
      return;
    }

    const deviceToken = generateDeviceToken();
    await db`
      UPDATE device_logins SET status = 'approved', device_token = ${deviceToken}, user_id = ${userId}
      WHERE code = ${login.code}
    `;
    await db`
      INSERT INTO device_tokens (token_hash, user_id) VALUES (${hashDeviceToken(deviceToken)}, ${userId})
    `;

    res.status(200).json({ ok: true });
  } catch (err) {
    if (err instanceof DbNotConfigured) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.status(500).json({ error: err.message });
  }
}

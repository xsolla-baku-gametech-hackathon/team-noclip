// Public — the desktop app polls this with the code it displayed while
// waiting for approve.js to run in the user's browser. The device_token is
// revealed exactly once (this response), then wiped from device_logins;
// device_tokens already holds the hashed copy that future requests check.
import { ensureSchema, requireDb, DbNotConfigured } from '../_lib/db.js';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');

  if (req.method === 'OPTIONS') {
    res.status(204).end();
    return;
  }
  if (req.method !== 'GET') {
    res.status(405).json({ error: 'Method not allowed. Use GET.' });
    return;
  }

  const code = String(req.query.code || '').toUpperCase();
  if (!code) {
    res.status(400).json({ error: 'Missing code.' });
    return;
  }

  try {
    await ensureSchema();
    const db = requireDb();

    const rows = await db`SELECT status, device_token, expires_at FROM device_logins WHERE code = ${code}`;
    if (rows.length === 0) {
      res.status(404).json({ error: 'Invalid pairing code.' });
      return;
    }
    const login = rows[0];

    if (login.status === 'approved' && login.device_token) {
      const token = login.device_token;
      await db`UPDATE device_logins SET status = 'consumed', device_token = NULL WHERE code = ${code}`;
      res.status(200).json({ status: 'approved', device_token: token });
      return;
    }

    if (new Date(login.expires_at).getTime() < Date.now()) {
      res.status(200).json({ status: 'expired' });
      return;
    }

    res.status(200).json({ status: login.status });
  } catch (err) {
    if (err instanceof DbNotConfigured) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.status(500).json({ error: err.message });
  }
}

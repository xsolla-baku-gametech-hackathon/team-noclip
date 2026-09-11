// Mints a real device token for the currently authenticated (cookie) user —
// used by the desktop app's loopback login (auth_server.py/login_window.py)
// instead of a client-fabricated token. Same device_tokens table and
// credential shape as the /api/device/approve pairing-code flow; this is
// just a second, simpler way to reach the same real credential.
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

    await ensureSchema();
    const db = requireDb();

    const token = generateDeviceToken();
    await db`INSERT INTO device_tokens (token_hash, user_id) VALUES (${hashDeviceToken(token)}, ${userId})`;

    res.status(200).json({ token });
  } catch (err) {
    if (err instanceof DbNotConfigured) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.status(500).json({ error: err.message });
  }
}

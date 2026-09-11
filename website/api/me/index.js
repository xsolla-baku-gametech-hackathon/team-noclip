import { ensureSchema, requireDb, DbNotConfigured } from '../_lib/db.js';
import { getAuthedUserId } from '../_lib/auth.js';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', req.headers.origin || '*');
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');

  if (req.method === 'OPTIONS') {
    res.status(204).end();
    return;
  }
  if (req.method !== 'GET') {
    res.status(405).json({ error: 'Method not allowed. Use GET.' });
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
    const rows = await db`SELECT id, email, name, picture, created_at FROM users WHERE id = ${userId}`;
    if (rows.length === 0) {
      res.status(401).json({ error: 'Not signed in.' });
      return;
    }
    res.status(200).json({ user: rows[0] });
  } catch (err) {
    if (err instanceof DbNotConfigured) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.status(500).json({ error: err.message });
  }
}

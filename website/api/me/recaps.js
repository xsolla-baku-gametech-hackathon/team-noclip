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

    const recaps = await db`
      SELECT r.id, r.session_id, r.previously_on, r.priorities, r.inventory, r.generated_at,
             g.title AS game_title, g.slug AS game_slug
      FROM recaps r
      JOIN games g ON g.id = r.game_id
      WHERE r.user_id = ${userId}
      ORDER BY r.generated_at DESC
    `;

    res.status(200).json({ recaps });
  } catch (err) {
    if (err instanceof DbNotConfigured) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.status(500).json({ error: err.message });
  }
}

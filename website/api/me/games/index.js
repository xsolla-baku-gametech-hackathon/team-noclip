import { ensureSchema, requireDb, DbNotConfigured } from '../../_lib/db.js';
import { getAuthedUserId } from '../../_lib/auth.js';

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

    const games = await db`
      SELECT
        g.id, g.slug, g.title, g.cover_image_url,
        ug.first_played_at, ug.last_played_at, ug.total_sessions,
        (SELECT COUNT(*) FROM recaps r WHERE r.game_id = g.id AND r.user_id = ${userId}) AS recap_count
      FROM user_games ug
      JOIN games g ON g.id = ug.game_id
      WHERE ug.user_id = ${userId}
      ORDER BY ug.last_played_at DESC
    `;

    res.status(200).json({ games });
  } catch (err) {
    if (err instanceof DbNotConfigured) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.status(500).json({ error: err.message });
  }
}

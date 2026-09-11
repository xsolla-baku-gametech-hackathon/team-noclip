import { ensureSchema, requireDb, DbNotConfigured } from '../../../_lib/db.js';
import { getAuthedUserId } from '../../../_lib/auth.js';

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

    const { gameId: slug } = req.query;

    await ensureSchema();
    const db = requireDb();

    const sessions = await db`
      SELECT
        s.id, s.window_title, s.started_at, s.ended_at, s.duration_seconds, s.created_at,
        (r.id IS NOT NULL) AS has_recap
      FROM game_sessions s
      JOIN games g ON g.id = s.game_id
      LEFT JOIN recaps r ON r.session_id = s.id
      WHERE s.user_id = ${userId} AND g.slug = ${slug}
      ORDER BY s.created_at DESC
    `;

    res.status(200).json({ sessions });
  } catch (err) {
    if (err instanceof DbNotConfigured) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.status(500).json({ error: err.message });
  }
}

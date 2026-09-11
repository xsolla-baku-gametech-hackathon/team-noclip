// Public, unauthenticated — this is the whole point of a share link. Only
// returns what was explicitly selected into the package: game title, the
// recap (if one was attached), and the chosen media. Never the owner's
// email, raw user_id, or anything outside what was shared.
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

  try {
    await ensureSchema();
    const db = requireDb();

    const { shareId } = req.query;
    const rows = await db`
      SELECT sp.id, sp.title, sp.media_ids, sp.created_at,
             g.title AS game_title,
             r.previously_on, r.priorities, r.inventory
      FROM share_packages sp
      JOIN games g ON g.id = sp.game_id
      LEFT JOIN recaps r ON r.id = sp.recap_id
      WHERE sp.id = ${shareId}
    `;
    if (rows.length === 0) {
      res.status(404).json({ error: 'This share link is invalid or has been removed.' });
      return;
    }
    const row = rows[0];

    let media = [];
    if (Array.isArray(row.media_ids) && row.media_ids.length > 0) {
      media = await db`
        SELECT id, type, url, duration_seconds, captured_at FROM media_assets WHERE id = ANY(${row.media_ids})
      `;
    }

    res.status(200).json({
      share: {
        title: row.title,
        game_title: row.game_title,
        recap: row.previously_on
          ? { previously_on: row.previously_on, priorities: row.priorities, inventory: row.inventory }
          : null,
        media,
        created_at: row.created_at,
      },
    });
  } catch (err) {
    if (err instanceof DbNotConfigured) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.status(500).json({ error: err.message });
  }
}

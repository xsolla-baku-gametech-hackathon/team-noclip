// POST creates a share package from resources the caller already owns —
// every id in the request is re-validated against the authenticated user's
// own rows before being included; nothing is trusted from the client beyond
// "here are ids I'd like to share," and ownership is re-checked here, not
// assumed from what the UI happened to show.
import { ensureSchema, requireDb, DbNotConfigured } from '../../_lib/db.js';
import { getAuthedUserId } from '../../_lib/auth.js';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', req.headers.origin || '*');
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');

  if (req.method === 'OPTIONS') {
    res.status(204).end();
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

    if (req.method === 'GET') {
      const shares = await db`
        SELECT sp.id, sp.title, sp.media_ids, sp.created_at, g.title AS game_title, g.slug AS game_slug,
               (sp.recap_id IS NOT NULL) AS has_recap
        FROM share_packages sp
        JOIN games g ON g.id = sp.game_id
        WHERE sp.user_id = ${userId}
        ORDER BY sp.created_at DESC
      `;
      res.status(200).json({ shares });
      return;
    }

    if (req.method !== 'POST') {
      res.status(405).json({ error: 'Method not allowed. Use GET or POST.' });
      return;
    }

    const { game_slug: gameSlug, recap_id: recapId, media_ids: mediaIds, title } = req.body || {};
    if (!gameSlug) {
      res.status(400).json({ error: 'Missing game_slug.' });
      return;
    }

    const gameRows = await db`
      SELECT g.id FROM user_games ug JOIN games g ON g.id = ug.game_id
      WHERE ug.user_id = ${userId} AND g.slug = ${gameSlug}
    `;
    if (gameRows.length === 0) {
      res.status(404).json({ error: "That game isn't in your collection." });
      return;
    }
    const gameId = gameRows[0].id;

    let ownedRecapId = null;
    if (recapId) {
      const recapRows = await db`SELECT id FROM recaps WHERE id = ${recapId} AND user_id = ${userId}`;
      if (recapRows.length === 0) {
        res.status(403).json({ error: "That recap doesn't belong to you." });
        return;
      }
      ownedRecapId = recapRows[0].id;
    }

    let ownedMediaIds = [];
    if (Array.isArray(mediaIds) && mediaIds.length > 0) {
      const mediaRows = await db`
        SELECT id FROM media_assets WHERE user_id = ${userId} AND id = ANY(${mediaIds})
      `;
      ownedMediaIds = mediaRows.map((r) => r.id);
    }

    const rows = await db`
      INSERT INTO share_packages (user_id, game_id, recap_id, media_ids, title)
      VALUES (${userId}, ${gameId}, ${ownedRecapId}, ${JSON.stringify(ownedMediaIds)}, ${title || null})
      RETURNING id, created_at
    `;

    res.status(200).json({ share: rows[0] });
  } catch (err) {
    if (err instanceof DbNotConfigured) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.status(500).json({ error: err.message });
  }
}

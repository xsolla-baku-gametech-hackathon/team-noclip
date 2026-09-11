import { ensureSchema, requireDb, DbNotConfigured } from '../../_lib/db.js';
import { getAuthedUserId } from '../../_lib/auth.js';

const PAGE_SIZE = 60;

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

    const type = typeof req.query.type === 'string' ? req.query.type : null;
    const gameSlug = typeof req.query.game === 'string' ? req.query.game : null;
    const offset = Math.max(0, Number(req.query.offset) || 0);

    await ensureSchema();
    const db = requireDb();

    // Only two filter combinations exist in the UI today — keep the query
    // explicit per case rather than building dynamic SQL by hand.
    let media;
    if (type && gameSlug) {
      media = await db`
        SELECT m.id, m.type, m.url, m.mime_type, m.size_bytes, m.duration_seconds, m.captured_at, m.created_at,
               g.title AS game_title, g.slug AS game_slug
        FROM media_assets m
        LEFT JOIN games g ON g.id = m.game_id
        WHERE m.user_id = ${userId} AND m.type = ${type} AND g.slug = ${gameSlug}
        ORDER BY COALESCE(m.captured_at, m.created_at) DESC
        LIMIT ${PAGE_SIZE} OFFSET ${offset}
      `;
    } else if (type) {
      media = await db`
        SELECT m.id, m.type, m.url, m.mime_type, m.size_bytes, m.duration_seconds, m.captured_at, m.created_at,
               g.title AS game_title, g.slug AS game_slug
        FROM media_assets m
        LEFT JOIN games g ON g.id = m.game_id
        WHERE m.user_id = ${userId} AND m.type = ${type}
        ORDER BY COALESCE(m.captured_at, m.created_at) DESC
        LIMIT ${PAGE_SIZE} OFFSET ${offset}
      `;
    } else if (gameSlug) {
      media = await db`
        SELECT m.id, m.type, m.url, m.mime_type, m.size_bytes, m.duration_seconds, m.captured_at, m.created_at,
               g.title AS game_title, g.slug AS game_slug
        FROM media_assets m
        LEFT JOIN games g ON g.id = m.game_id
        WHERE m.user_id = ${userId} AND g.slug = ${gameSlug}
        ORDER BY COALESCE(m.captured_at, m.created_at) DESC
        LIMIT ${PAGE_SIZE} OFFSET ${offset}
      `;
    } else {
      media = await db`
        SELECT m.id, m.type, m.url, m.mime_type, m.size_bytes, m.duration_seconds, m.captured_at, m.created_at,
               g.title AS game_title, g.slug AS game_slug
        FROM media_assets m
        LEFT JOIN games g ON g.id = m.game_id
        WHERE m.user_id = ${userId}
        ORDER BY COALESCE(m.captured_at, m.created_at) DESC
        LIMIT ${PAGE_SIZE} OFFSET ${offset}
      `;
    }

    res.status(200).json({ media, next_offset: media.length === PAGE_SIZE ? offset + PAGE_SIZE : null });
  } catch (err) {
    if (err instanceof DbNotConfigured) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.status(500).json({ error: err.message });
  }
}

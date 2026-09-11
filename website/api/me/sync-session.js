// Desktop app pushes a completed session here (device Bearer token auth).
// Upserts the game, the user's collection entry, and the session row — this
// is the real bridge between software/recap_manager.py's local session JSON
// and the authenticated web app.
import { ensureSchema, requireDb, slugify, DbNotConfigured } from '../_lib/db.js';
import { getAuthedUserId } from '../_lib/auth.js';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

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
      res.status(401).json({ error: 'Not signed in. Pair the desktop app first.' });
      return;
    }

    const { session_id: externalSessionId, game_name: gameName, window_title: windowTitle,
      started_at: startedAt, ended_at: endedAt, duration_seconds: durationSeconds, events } = req.body || {};

    if (!externalSessionId || !gameName) {
      res.status(400).json({ error: 'Missing session_id or game_name.' });
      return;
    }

    await ensureSchema();
    const db = requireDb();
    const slug = slugify(gameName);

    const gameRows = await db`
      INSERT INTO games (slug, title) VALUES (${slug}, ${gameName})
      ON CONFLICT (slug) DO UPDATE SET title = EXCLUDED.title
      RETURNING id
    `;
    const gameId = gameRows[0].id;

    const sessionRows = await db`
      INSERT INTO game_sessions (user_id, game_id, external_session_id, window_title, started_at, ended_at, duration_seconds, events)
      VALUES (${userId}, ${gameId}, ${externalSessionId}, ${windowTitle || null}, ${startedAt || null}, ${endedAt || null}, ${durationSeconds || null}, ${JSON.stringify(events || [])})
      ON CONFLICT (user_id, external_session_id) DO UPDATE SET
        window_title = EXCLUDED.window_title,
        ended_at = EXCLUDED.ended_at,
        duration_seconds = EXCLUDED.duration_seconds,
        events = EXCLUDED.events
      RETURNING id, (xmax = 0) AS inserted
    `;
    const sessionId = sessionRows[0].id;
    const sessionIncrement = sessionRows[0].inserted ? 1 : 0;

    await db`
      INSERT INTO user_games (user_id, game_id, first_played_at, last_played_at, total_sessions)
      VALUES (${userId}, ${gameId}, now(), now(), 1)
      ON CONFLICT (user_id, game_id) DO UPDATE SET
        last_played_at = now(),
        total_sessions = user_games.total_sessions + ${sessionIncrement}
    `;

    res.status(200).json({ ok: true, session_id: sessionId, game_id: gameId });
  } catch (err) {
    if (err instanceof DbNotConfigured) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.status(500).json({ error: err.message });
  }
}

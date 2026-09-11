// Consolidated /api/me/* routes (see api/auth/[...action].js for why — the
// Hobby plan's 12-function cap). Every authenticated "my stuff" endpoint
// lives here now, dispatched by path segments + method. URLs unchanged:
//   GET  /api/me
//   GET  /api/me/games
//   GET  /api/me/games/:slug
//   GET  /api/me/games/:slug/sessions
//   GET  /api/me/recaps
//   GET  /api/me/sessions/:id/recap
//   POST /api/me/sessions/:id/recap
//   POST /api/me/sync-session
//   GET  /api/me/media
//   POST /api/me/media/upload
//   GET  /api/me/share-packages
//   POST /api/me/share-packages
import { ensureSchema, requireDb, slugify, DbNotConfigured } from '../_lib/db.js';
import { getAuthedUserId } from '../_lib/auth.js';
import { storeFile, MAX_UPLOAD_BYTES } from '../_lib/storage.js';

const OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions';
const DEFAULT_MODEL = 'openai/gpt-4o-mini';
const MEDIA_PAGE_SIZE = 60;

// ---- GET /api/me ----------------------------------------------------------
async function getMe(req, res, userId) {
  const db = requireDb();
  const rows = await db`SELECT id, email, name, picture, created_at FROM users WHERE id = ${userId}`;
  if (rows.length === 0) {
    res.status(401).json({ error: 'Not signed in.' });
    return;
  }
  res.status(200).json({ user: rows[0] });
}

// ---- GET /api/me/games -----------------------------------------------------
async function listGames(req, res, userId) {
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
}

// ---- GET /api/me/games/:slug -----------------------------------------------
async function getGame(req, res, userId, slug) {
  const db = requireDb();
  const rows = await db`
    SELECT
      g.id, g.slug, g.title, g.cover_image_url,
      ug.first_played_at, ug.last_played_at, ug.total_sessions
    FROM user_games ug
    JOIN games g ON g.id = ug.game_id
    WHERE ug.user_id = ${userId} AND g.slug = ${slug}
  `;
  if (rows.length === 0) {
    res.status(404).json({ error: 'Game not found in your collection.' });
    return;
  }
  res.status(200).json({ game: rows[0] });
}

// ---- GET /api/me/games/:slug/sessions --------------------------------------
async function listGameSessions(req, res, userId, slug) {
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
}

// ---- GET /api/me/recaps -----------------------------------------------------
async function listRecaps(req, res, userId) {
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
}

// ---- GET/POST /api/me/sessions/:id/recap -----------------------------------
function buildRecapPrompt(gameName, events) {
  const eventLines = (events || [])
    .map((e) => {
      const time = e.timestamp || e.time || '';
      const text = e.text || e.description || JSON.stringify(e);
      return time ? `[${time}] ${text}` : `- ${text}`;
    })
    .join('\n');

  return [
    `You are generating a structured session recap for the game "${gameName || 'this game'}".`,
    'Base it only on the event log below — never invent details it does not imply.',
    'Respond with ONLY a JSON object (no markdown, no code fences) matching exactly:',
    '{"previously_on": string, "priorities": string[], "inventory": string[]}',
    '- previously_on: 2-4 sentences, written like a TV recap narrator.',
    '- priorities: up to 4 short, concrete things the player should focus on next.',
    '- inventory: up to 6 short notes on important items, resources, or unfinished objectives.',
    'If the event log is too sparse for a field, return an empty array or a short honest sentence — never fabricate specifics.',
    '',
    'Event log:',
    eventLines || '(no events recorded)',
  ].join('\n');
}

function parseSessionRecap(raw) {
  const cleaned = raw.trim().replace(/^```(?:json)?/i, '').replace(/```$/, '').trim();
  const parsed = JSON.parse(cleaned);
  return {
    previouslyOn: String(parsed.previously_on || '').trim(),
    priorities: Array.isArray(parsed.priorities) ? parsed.priorities.map(String) : [],
    inventory: Array.isArray(parsed.inventory) ? parsed.inventory.map(String) : [],
  };
}

async function getOrGenerateRecap(req, res, userId, sessionId) {
  const db = requireDb();

  if (req.method === 'GET') {
    const rows = await db`
      SELECT previously_on, priorities, inventory, generated_at
      FROM recaps WHERE session_id = ${sessionId} AND user_id = ${userId}
    `;
    if (rows.length === 0) {
      res.status(404).json({ error: 'No recap yet for this session.' });
      return;
    }
    res.status(200).json({ recap: rows[0] });
    return;
  }

  const sessionRows = await db`
    SELECT s.id, s.game_id, s.events, g.title AS game_title
    FROM game_sessions s
    JOIN games g ON g.id = s.game_id
    WHERE s.id = ${sessionId} AND s.user_id = ${userId}
  `;
  const session = sessionRows[0];
  if (!session) {
    res.status(404).json({ error: 'Session not found.' });
    return;
  }

  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) {
    res.status(500).json({ error: 'Server is not configured: OPENROUTER_API_KEY is missing.' });
    return;
  }

  const upstream = await fetch(OPENROUTER_URL, {
    method: 'POST',
    headers: { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: process.env.OPENROUTER_MODEL || DEFAULT_MODEL,
      messages: [{ role: 'user', content: buildRecapPrompt(session.game_title, session.events) }],
    }),
  });

  if (!upstream.ok) {
    const errText = await upstream.text();
    res.status(502).json({ error: `OpenRouter request failed (${upstream.status}): ${errText}` });
    return;
  }

  const data = await upstream.json();
  const raw = data?.choices?.[0]?.message?.content?.trim();
  if (!raw) {
    res.status(502).json({ error: 'OpenRouter returned no recap content.' });
    return;
  }

  let structured;
  try {
    structured = parseSessionRecap(raw);
  } catch {
    structured = { previouslyOn: raw, priorities: [], inventory: [] };
  }

  const rows = await db`
    INSERT INTO recaps (session_id, user_id, game_id, previously_on, priorities, inventory)
    VALUES (${session.id}, ${userId}, ${session.game_id}, ${structured.previouslyOn}, ${JSON.stringify(structured.priorities)}, ${JSON.stringify(structured.inventory)})
    ON CONFLICT (session_id) DO UPDATE SET
      previously_on = EXCLUDED.previously_on,
      priorities = EXCLUDED.priorities,
      inventory = EXCLUDED.inventory,
      generated_at = now()
    RETURNING previously_on, priorities, inventory, generated_at
  `;

  res.status(200).json({ recap: rows[0] });
}

// ---- POST /api/me/sync-session ---------------------------------------------
async function syncSession(req, res, userId) {
  const db = requireDb();
  const {
    session_id: externalSessionId,
    game_name: gameName,
    window_title: windowTitle,
    started_at: startedAt,
    ended_at: endedAt,
    duration_seconds: durationSeconds,
    events,
  } = req.body || {};

  if (!externalSessionId || !gameName) {
    res.status(400).json({ error: 'Missing session_id or game_name.' });
    return;
  }

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
}

// ---- GET /api/me/media ------------------------------------------------------
async function listMedia(req, res, userId) {
  const db = requireDb();
  const type = typeof req.query.type === 'string' ? req.query.type : null;
  const gameSlug = typeof req.query.game === 'string' ? req.query.game : null;
  const offset = Math.max(0, Number(req.query.offset) || 0);

  let media;
  if (type && gameSlug) {
    media = await db`
      SELECT m.id, m.type, m.url, m.mime_type, m.size_bytes, m.duration_seconds, m.captured_at, m.created_at,
             g.title AS game_title, g.slug AS game_slug
      FROM media_assets m
      LEFT JOIN games g ON g.id = m.game_id
      WHERE m.user_id = ${userId} AND m.type = ${type} AND g.slug = ${gameSlug}
      ORDER BY COALESCE(m.captured_at, m.created_at) DESC
      LIMIT ${MEDIA_PAGE_SIZE} OFFSET ${offset}
    `;
  } else if (type) {
    media = await db`
      SELECT m.id, m.type, m.url, m.mime_type, m.size_bytes, m.duration_seconds, m.captured_at, m.created_at,
             g.title AS game_title, g.slug AS game_slug
      FROM media_assets m
      LEFT JOIN games g ON g.id = m.game_id
      WHERE m.user_id = ${userId} AND m.type = ${type}
      ORDER BY COALESCE(m.captured_at, m.created_at) DESC
      LIMIT ${MEDIA_PAGE_SIZE} OFFSET ${offset}
    `;
  } else if (gameSlug) {
    media = await db`
      SELECT m.id, m.type, m.url, m.mime_type, m.size_bytes, m.duration_seconds, m.captured_at, m.created_at,
             g.title AS game_title, g.slug AS game_slug
      FROM media_assets m
      LEFT JOIN games g ON g.id = m.game_id
      WHERE m.user_id = ${userId} AND g.slug = ${gameSlug}
      ORDER BY COALESCE(m.captured_at, m.created_at) DESC
      LIMIT ${MEDIA_PAGE_SIZE} OFFSET ${offset}
    `;
  } else {
    media = await db`
      SELECT m.id, m.type, m.url, m.mime_type, m.size_bytes, m.duration_seconds, m.captured_at, m.created_at,
             g.title AS game_title, g.slug AS game_slug
      FROM media_assets m
      LEFT JOIN games g ON g.id = m.game_id
      WHERE m.user_id = ${userId}
      ORDER BY COALESCE(m.captured_at, m.created_at) DESC
      LIMIT ${MEDIA_PAGE_SIZE} OFFSET ${offset}
    `;
  }

  res.status(200).json({ media, next_offset: media.length === MEDIA_PAGE_SIZE ? offset + MEDIA_PAGE_SIZE : null });
}

// ---- POST /api/me/media/upload ----------------------------------------------
async function uploadMedia(req, res, userId) {
  const db = requireDb();
  const {
    game_name: gameName,
    session_id: sessionId,
    type,
    filename,
    content_type: contentType,
    captured_at: capturedAt,
    duration_seconds: durationSeconds,
    data_base64: dataBase64,
  } = req.body || {};

  if (!type || !['screenshot', 'video'].includes(type)) {
    res.status(400).json({ error: "type must be 'screenshot' or 'video'." });
    return;
  }
  if (!filename || !dataBase64) {
    res.status(400).json({ error: 'Missing filename or data_base64.' });
    return;
  }

  const buffer = Buffer.from(dataBase64, 'base64');
  if (buffer.length > MAX_UPLOAD_BYTES) {
    res.status(413).json({
      error: `File is ${buffer.length} bytes, over the ${MAX_UPLOAD_BYTES}-byte proxy-upload limit. Large video clips need direct-to-storage upload, not implemented yet.`,
    });
    return;
  }

  let gameId = null;
  if (gameName) {
    const slug = slugify(gameName);
    const rows = await db`
      INSERT INTO games (slug, title) VALUES (${slug}, ${gameName})
      ON CONFLICT (slug) DO UPDATE SET title = EXCLUDED.title
      RETURNING id
    `;
    gameId = rows[0].id;
  }

  const { storageKey, url } = await storeFile(buffer, { userId, filename, contentType });

  const rows = await db`
    INSERT INTO media_assets (user_id, game_id, session_id, type, storage_key, url, mime_type, size_bytes, duration_seconds, captured_at)
    VALUES (${userId}, ${gameId}, ${sessionId || null}, ${type}, ${storageKey}, ${url}, ${contentType || null}, ${buffer.length}, ${durationSeconds || null}, ${capturedAt || null})
    RETURNING id, type, url, mime_type, size_bytes, duration_seconds, captured_at, created_at
  `;

  res.status(200).json({ media: rows[0] });
}

// ---- GET/POST /api/me/share-packages -----------------------------------------
async function shareGetOrCreate(req, res, userId) {
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
    const mediaRows = await db`SELECT id FROM media_assets WHERE user_id = ${userId} AND id = ANY(${mediaIds})`;
    ownedMediaIds = mediaRows.map((r) => r.id);
  }

  const rows = await db`
    INSERT INTO share_packages (user_id, game_id, recap_id, media_ids, title)
    VALUES (${userId}, ${gameId}, ${ownedRecapId}, ${JSON.stringify(ownedMediaIds)}, ${title || null})
    RETURNING id, created_at
  `;

  res.status(200).json({ share: rows[0] });
}

// ---- dispatch -----------------------------------------------------------------
export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', req.headers.origin || '*');
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    res.status(204).end();
    return;
  }

  const raw = req.query.path;
  const path = Array.isArray(raw) ? raw : raw ? [raw] : [];

  try {
    const userId = await getAuthedUserId(req);
    if (!userId) {
      res.status(401).json({ error: 'Not signed in.' });
      return;
    }

    await ensureSchema();

    if (path.length === 0 && req.method === 'GET') return await getMe(req, res, userId);
    if (path[0] === 'games' && path.length === 1 && req.method === 'GET') return await listGames(req, res, userId);
    if (path[0] === 'games' && path.length === 2 && req.method === 'GET') return await getGame(req, res, userId, path[1]);
    if (path[0] === 'games' && path.length === 3 && path[2] === 'sessions' && req.method === 'GET')
      return await listGameSessions(req, res, userId, path[1]);
    if (path[0] === 'recaps' && path.length === 1 && req.method === 'GET') return await listRecaps(req, res, userId);
    if (path[0] === 'sessions' && path.length === 3 && path[2] === 'recap' && (req.method === 'GET' || req.method === 'POST'))
      return await getOrGenerateRecap(req, res, userId, path[1]);
    if (path[0] === 'sync-session' && path.length === 1 && req.method === 'POST') return await syncSession(req, res, userId);
    if (path[0] === 'media' && path.length === 1 && req.method === 'GET') return await listMedia(req, res, userId);
    if (path[0] === 'media' && path.length === 2 && path[1] === 'upload' && req.method === 'POST')
      return await uploadMedia(req, res, userId);
    if (path[0] === 'share-packages' && path.length === 1 && (req.method === 'GET' || req.method === 'POST'))
      return await shareGetOrCreate(req, res, userId);

    res.status(404).json({ error: 'Not found.' });
  } catch (err) {
    if (err instanceof DbNotConfigured) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.status(500).json({ error: err.message });
  }
}

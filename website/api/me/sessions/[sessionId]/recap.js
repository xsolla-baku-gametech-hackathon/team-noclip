// GET  -> returns the stored recap for this session, if one exists.
// POST -> generates one via OpenRouter (structured Previously On / Critical
//         Priorities / Inventory & Goals), stores it, and returns it.
// Every query is scoped to the authenticated user_id — a session that
// belongs to someone else 404s, it never leaks existence.
import { ensureSchema, requireDb, DbNotConfigured } from '../../../_lib/db.js';
import { getAuthedUserId } from '../../../_lib/auth.js';

const OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions';
const DEFAULT_MODEL = 'openai/gpt-4o-mini';

function buildPrompt(gameName, events) {
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

function parseStructuredRecap(raw) {
  const cleaned = raw.trim().replace(/^```(?:json)?/i, '').replace(/```$/, '').trim();
  const parsed = JSON.parse(cleaned);
  return {
    previouslyOn: String(parsed.previously_on || '').trim(),
    priorities: Array.isArray(parsed.priorities) ? parsed.priorities.map(String) : [],
    inventory: Array.isArray(parsed.inventory) ? parsed.inventory.map(String) : [],
  };
}

async function loadOwnedSession(db, userId, sessionId) {
  const rows = await db`
    SELECT s.id, s.game_id, s.events, g.title AS game_title
    FROM game_sessions s
    JOIN games g ON g.id = s.game_id
    WHERE s.id = ${sessionId} AND s.user_id = ${userId}
  `;
  return rows[0] || null;
}

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', req.headers.origin || '*');
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');

  if (req.method === 'OPTIONS') {
    res.status(204).end();
    return;
  }
  if (req.method !== 'GET' && req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed. Use GET or POST.' });
    return;
  }

  try {
    const userId = await getAuthedUserId(req);
    if (!userId) {
      res.status(401).json({ error: 'Not signed in.' });
      return;
    }

    const { sessionId } = req.query;
    await ensureSchema();
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

    // POST — generate.
    const session = await loadOwnedSession(db, userId, sessionId);
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
        messages: [{ role: 'user', content: buildPrompt(session.game_title, session.events) }],
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
      structured = parseStructuredRecap(raw);
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
  } catch (err) {
    if (err instanceof DbNotConfigured) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.status(500).json({ error: err.message });
  }
}

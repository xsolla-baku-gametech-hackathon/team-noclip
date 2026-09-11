// Vercel Serverless Function — Xsolla Game Recap Engine
// Holds API configuration server-side only, never shipping in the client binary.
// Real generation only — no fallback text pretending to know what the player
// did when the AI service isn't configured or fails. See ai_recap.py for how
// the desktop app is expected to handle an error response from this route.

const RECAP_SERVICE_URL = process.env.RECAP_SERVICE_URL || 'https://openrouter.ai/api/v1/chat/completions';
const DEFAULT_MODEL = 'openai/gpt-4o-mini';

function buildPrompt(gameName, playerName, saveData, events) {
  const saveSummary = saveData ? JSON.stringify(saveData, null, 2) : 'No save data available';
  const eventLines = (events || [])
    .map((e) => {
      const time = e.timestamp || e.time || '';
      const text = e.text || e.description || JSON.stringify(e);
      return time ? `[${time}] ${text}` : `- ${text}`;
    })
    .join('\n') || '(no recent session events)';

  return [
    `You are the official Xsolla Game Recap engine. You act as a personalized, context-aware memory bridge for a player returning to "${gameName || 'their game'}" after time away.`,
    `Player name: ${playerName || 'Player'}`,
    '',
    'GAME & SESSION STATE:',
    saveSummary,
    '',
    'RECENT HIGHLIGHT EVENTS:',
    eventLines,
    '',
    'INSTRUCTIONS:',
    'Base everything only on the state and events above — never invent progress, items, or story beats they do not imply.',
    'Respond with ONLY a JSON object (no markdown, no code fences) matching exactly:',
    '{"previously_on": string, "what_you_were_up_to": string[], "next_objectives": string[]}',
    '- previously_on: 2-3 engaging narrative sentences, written like a recap narrator.',
    '- what_you_were_up_to: up to 3 short bullet points on current progress/status.',
    '- next_objectives: up to 3 short, prioritized, actionable next steps.',
    'If the data is too sparse for a field, say so honestly in 1 short sentence rather than fabricating specifics.',
  ].join('\n');
}

function parseStructuredRecap(raw) {
  const cleaned = raw.trim().replace(/^```(?:json)?/i, '').replace(/```$/, '').trim();
  const parsed = JSON.parse(cleaned);
  return {
    previously_on: String(parsed.previously_on || '').trim(),
    what_you_were_up_to: Array.isArray(parsed.what_you_were_up_to) ? parsed.what_you_were_up_to.map(String) : [],
    next_objectives: Array.isArray(parsed.next_objectives) ? parsed.next_objectives.map(String) : [],
  };
}

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.status(204).end();
    return;
  }

  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed. Use POST.' });
    return;
  }

  const { game_name, player_name, save_data, events } = req.body || {};

  const apiKey = process.env.RECAP_API_KEY || process.env.OPENROUTER_API_KEY;
  if (!apiKey) {
    res.status(500).json({ error: 'Server is not configured: RECAP_API_KEY / OPENROUTER_API_KEY is missing.' });
    return;
  }

  try {
    const model = process.env.RECAP_MODEL || process.env.OPENROUTER_MODEL || DEFAULT_MODEL;
    const upstream = await fetch(RECAP_SERVICE_URL, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model,
        messages: [{ role: 'user', content: buildPrompt(game_name, player_name, save_data, events) }],
      }),
    });

    if (!upstream.ok) {
      const errText = await upstream.text();
      res.status(502).json({ error: `Recap service request failed (${upstream.status}): ${errText}` });
      return;
    }

    const data = await upstream.json();
    const raw = data?.choices?.[0]?.message?.content?.trim();
    if (!raw) {
      res.status(502).json({ error: 'Recap service returned no content.' });
      return;
    }

    let structured;
    try {
      structured = parseStructuredRecap(raw);
    } catch {
      // Model didn't return valid JSON — surface the raw text rather than
      // silently discarding it or fabricating structured fields for it.
      structured = { previously_on: raw, what_you_were_up_to: [], next_objectives: [] };
    }

    res.status(200).json({ recap: structured.previously_on, structured });
  } catch (err) {
    res.status(500).json({ error: `Recap generation failed: ${err.message}` });
  }
}

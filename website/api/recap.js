// Vercel Serverless Function — holds the OpenRouter key server-side only.
// Set OPENROUTER_API_KEY (and optionally OPENROUTER_MODEL) as Environment
// Variables in the Vercel project dashboard — never commit them here. This
// is what keeps the key out of the desktop app / .exe entirely.

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
    `You are writing a short, punchy "Previously On..." recap of a gameplay session for the game "${gameName || 'this game'}".`,
    'Base it only on the event log below — do not invent details that aren\'t implied by it.',
    'Keep it to 2-4 sentences, written like a TV show recap narrator. No markdown, no headers.',
    '',
    'Event log:',
    eventLines || '(no events recorded)',
  ].join('\n');
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

  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) {
    res.status(500).json({ error: 'Server is not configured: OPENROUTER_API_KEY is missing.' });
    return;
  }

  const { game_name, events } = req.body || {};

  try {
    const upstream = await fetch(OPENROUTER_URL, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: process.env.OPENROUTER_MODEL || DEFAULT_MODEL,
        messages: [{ role: 'user', content: buildPrompt(game_name, events) }],
      }),
    });

    if (!upstream.ok) {
      const errText = await upstream.text();
      res.status(502).json({ error: `OpenRouter request failed (${upstream.status}): ${errText}` });
      return;
    }

    const data = await upstream.json();
    const recap = data?.choices?.[0]?.message?.content?.trim();

    if (!recap) {
      res.status(502).json({ error: 'OpenRouter returned no recap content.' });
      return;
    }

    res.status(200).json({ recap });
  } catch (err) {
    res.status(500).json({ error: `Recap generation failed: ${err.message}` });
  }
}

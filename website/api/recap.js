// Vercel Serverless Function — Xsolla Game Recap Engine
// Holds API configuration server-side only, never shipping in the client binary.

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
    'Write a concise, high-energy gaming recap with 3 sections:',
    '1. PREVIOUSLY ON: Exactly 2-3 engaging narrative sentences summarizing progress, storyline state, and checkpoint where the player left off.',
    '2. WHAT YOU WERE UP TO: Exactly 3 bullet points detailing current progress, in-game achievements, and status.',
    '3. NEXT OBJECTIVES: Exactly 3 prioritized, actionable tasks the player should tackle right now upon resuming gameplay.',
    '',
    'Keep it punchy, accurate to the provided data, and formatted cleanly with clear headers.'
  ].join('\n');
}

function generateUniversalFallback(gameName, playerName, saveData, events) {
  const game = gameName || 'Your Game';
  const evCount = events?.length || saveData?.stats?.events_count || 0;
  const screenshots = saveData?.stats?.screenshots_count || 0;

  const previouslyOn = `You returned to ${game} with your latest in-game progress and session milestones securely preserved. Your run is ready to resume right where you saved.`;

  const whatYouWereUpTo = [
    `Actively playing ${game} with ${evCount} session milestones logged.`,
    `Archived ${screenshots} visual memories in your personal capture vault.`,
    `Character checkpoint and gameplay state ready to continue.`
  ];

  const nextObjectives = [
    `Resume Primary Quest: Continue your main storyline objectives in ${game}.`,
    `Inventory & Supply Check: Verify your equipment, items, and resources.`,
    `Capture Highlights: Press F11 for instant screenshots or F9 to capture video clips.`
  ];

  const recapText = [
    `PREVIOUSLY ON ${game.toUpperCase()}:`,
    previouslyOn,
    '',
    'WHAT YOU WERE UP TO:',
    ...whatYouWereUpTo.map(item => `• ${item}`),
    '',
    'NEXT OBJECTIVES:',
    ...nextObjectives.map(item => `• ${item}`)
  ].join('\n');

  return {
    recap: recapText,
    structured: {
      previously_on: previouslyOn,
      what_you_were_up_to: whatYouWereUpTo,
      next_objectives: nextObjectives
    }
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
    const fallback = generateUniversalFallback(game_name, player_name, save_data, events);
    res.status(200).json(fallback);
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
      const fallback = generateUniversalFallback(game_name, player_name, save_data, events);
      res.status(200).json(fallback);
      return;
    }

    const data = await upstream.json();
    const recap = data?.choices?.[0]?.message?.content?.trim();

    if (!recap) {
      const fallback = generateUniversalFallback(game_name, player_name, save_data, events);
      res.status(200).json(fallback);
      return;
    }

    res.status(200).json({ recap });
  } catch (err) {
    const fallback = generateUniversalFallback(game_name, player_name, save_data, events);
    res.status(200).json(fallback);
  }
}

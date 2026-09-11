// Vercel Serverless Function — Xsolla Game Recap Engine
// Powered by OpenRouter AI (gpt-4o-mini) for high-energy, context-aware gaming recaps.

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
    `Player: ${playerName || 'Player'}`,
    `Game: ${gameName || 'Current Game'}`,
    '',
    'GAME & SESSION TELEMETRY:',
    saveSummary,
    '',
    'RECENT HIGHLIGHT EVENTS:',
    eventLines,
    '',
    'TASK:',
    `Write an immersive, high-energy gaming recap for a player returning to ${gameName || 'their game'}.`,
    'Return a valid JSON object with:',
    '- "previously_on": 2-3 engaging cinematic sentences summarizing what happened and where the player is currently standing in the story/world.',
    '- "what_you_were_up_to": An array of exactly 3 distinct accomplishment strings summarizing progress, resources, or world status.',
    '- "next_objectives": An array of exactly 3 objects with "title" (concise string), "description" (actionable instructions), and "priority" ("HIGH", "MEDIUM", or "OPTIONAL").'
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
    {
      title: 'Resume Primary Quest',
      description: `Continue your main storyline objectives in ${game}.`,
      priority: 'HIGH'
    },
    {
      title: 'Inventory & Supply Check',
      description: 'Verify your equipment, items, and resources before moving ahead.',
      priority: 'MEDIUM'
    },
    {
      title: 'Capture Highlights',
      description: `Press F11 for instant screenshots or F9 to capture video clips (${screenshots} saved).`,
      priority: 'OPTIONAL'
    }
  ];

  const recapText = [
    `PREVIOUSLY ON ${game.toUpperCase()}:`,
    previouslyOn,
    '',
    'WHAT YOU WERE UP TO:',
    ...whatYouWereUpTo.map(item => `• ${item}`),
    '',
    'NEXT OBJECTIVES:',
    ...nextObjectives.map(o => `• ${o.title}: ${o.description}`)
  ].join('\n');

  return {
    recap: recapText,
    structured: {
      previously_on: previouslyOn,
      what_you_were_up_to: whatYouWereUpTo,
      next_objectives: nextObjectives.map(o => `${o.title}: ${o.description}`),
      raw_objectives: nextObjectives
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
        response_format: { type: 'json_object' },
        messages: [
          {
            role: 'system',
            content: 'You are the official Xsolla Game Recap engine. Generate a cinematic, high-energy gaming recap as a valid JSON object with keys: "previously_on" (string), "what_you_were_up_to" (array of 3 strings), and "next_objectives" (array of 3 objects with "title", "description", and "priority" where priority is HIGH, MEDIUM, or OPTIONAL).'
          },
          {
            role: 'user',
            content: buildPrompt(game_name, player_name, save_data, events)
          }
        ],
      }),
    });

    if (!upstream.ok) {
      const fallback = generateUniversalFallback(game_name, player_name, save_data, events);
      res.status(200).json(fallback);
      return;
    }

    const data = await upstream.json();
    const rawContent = data?.choices?.[0]?.message?.content?.trim();

    let structured = null;
    try {
      structured = JSON.parse(rawContent);
    } catch {
      // Ignore JSON parse error and fallback
    }

    if (structured && structured.previously_on) {
      const objs = structured.next_objectives || [];
      const formattedObjectives = objs.map(o => {
        if (typeof o === 'string') return o;
        return `${o.title || 'Objective'}: ${o.description || ''}`;
      });

      const recapText = [
        `PREVIOUSLY ON ${(game_name || 'YOUR GAME').toUpperCase()}:`,
        structured.previously_on,
        '',
        'WHAT YOU WERE UP TO:',
        ...(structured.what_you_were_up_to || []).map(item => `• ${item}`),
        '',
        'NEXT OBJECTIVES:',
        ...formattedObjectives.map(item => `• ${item}`)
      ].join('\n');

      res.status(200).json({
        recap: recapText,
        structured: {
          previously_on: structured.previously_on,
          what_you_were_up_to: structured.what_you_were_up_to || [],
          next_objectives: formattedObjectives,
          raw_objectives: objs
        }
      });
      return;
    }

    const fallback = generateUniversalFallback(game_name, player_name, save_data, events);
    res.status(200).json(fallback);
  } catch (err) {
    const fallback = generateUniversalFallback(game_name, player_name, save_data, events);
    res.status(200).json(fallback);
  }
}

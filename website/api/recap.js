// Vercel Serverless Function — holds the OpenRouter key server-side only.
// Set OPENROUTER_API_KEY (and optionally OPENROUTER_MODEL) as Environment
// Variables in the Vercel project dashboard — never commit them here. This
// keeps the key out of the desktop app / .exe entirely.

const OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions';
const DEFAULT_MODEL = 'openai/gpt-4o-mini';

function buildPrompt(gameName, playerName, saveData, events) {
  const saveSummary = saveData ? JSON.stringify(saveData, null, 2) : 'No save file data available';
  const eventLines = (events || [])
    .map((e) => {
      const time = e.timestamp || e.time || '';
      const text = e.text || e.description || JSON.stringify(e);
      return time ? `[${time}] ${text}` : `- ${text}`;
    })
    .join('\n') || '(no recent session events)';

  return [
    `You are the official Xsolla Game Recap AI engine. You act as a personalized, context-aware memory bridge for a player returning to "${gameName || 'their game'}" after time away.`,
    `Player name: ${playerName || 'Player'}`,
    '',
    'SAVE FILE & GAME STATE:',
    saveSummary,
    '',
    'RECENT HIGHLIGHT EVENTS:',
    eventLines,
    '',
    'INSTRUCTIONS:',
    'Write a concise, high-energy gaming recap with 3 sections:',
    '1. PREVIOUSLY ON: Exactly 2-3 engaging narrative sentences summarizing temporal, economic, and storyline state where the player left off.',
    '2. WHAT YOU WERE UP TO: Exactly 3 bullet points detailing current progress, farm/world conditions, and key stats.',
    '3. NEXT OBJECTIVES: Exactly 3 prioritized, actionable tasks the player should tackle right now upon resuming gameplay.',
    '',
    'Keep it punchy, accurate to the provided data, and formatted cleanly with clear headers.'
  ].join('\n');
}

function generateHeuristicFallback(gameName, playerName, saveData, events) {
  const name = playerName || saveData?.player_name || 'Player';
  const stats = saveData?.stats || {};
  const priorities = saveData?.priorities || [];

  let previouslyOn = '';
  let whatYouWereUpTo = [];
  let nextObjectives = [];

  const lowerGame = (gameName || '').toLowerCase();

  if (lowerGame.includes('stardew')) {
    const season = stats.season || 'Summer';
    const day = stats.day || 18;
    const year = stats.year || 2;
    const gold = (stats.gold || 12450).toLocaleString();
    const farmName = saveData?.farm_name || 'Misty Farm';

    previouslyOn = `You returned to ${farmName} on ${season} ${day}, Year ${year} with ${gold}g in savings. Your farm is thriving with active crops, while Pelican Town and the Community Center await your next move.`;
    whatYouWereUpTo = [
      `Tending crops across ${farmName} (${stats.ready_to_harvest || 2} ready to harvest, ${stats.needs_water || 0} dry).`,
      `Community Center restoration underway (${stats.completed_bundles || 18}/30 bundles restored).`,
      `Maintaining connections with townspeople and active community requests.`
    ];
    nextObjectives = (priorities.length ? priorities : [
      { title: 'Harvest Ripe Crops', description: 'Collect ripe crops before the day ends.' },
      { title: 'Check Community Center', description: 'Donate required seasonal items to unlock bundles.' },
      { title: 'Visit Town Bulletin Board', description: 'Take on active villager requests at Pierre\'s store.' }
    ]).map(p => `${p.title}: ${p.description}`);
  } else if (lowerGame.includes('undertale') || lowerGame.includes('deltarune')) {
    const lv = stats.lv || 1;
    const location = stats.location || 'Waterfall';
    const gold = stats.gold || 142;
    const route = stats.route || 'Pacifist Route';

    previouslyOn = `You left ${name} resting at a SAVE star in ${location} at LV ${lv} with ${gold}G. Your journey through the Underground remains firmly on the ${route}.`;
    whatYouWereUpTo = [
      `Exploring ${location} while conserving items and staying determined.`,
      `Holding 0 EXP and LV ${lv} in adherence to the ${route}.`,
      `Keeping in touch with Papyrus and friends via Cell Phone.`
    ];
    nextObjectives = [
      'Maintain Pacifist Stance: Spare or ACT with monsters without dealing lethal damage.',
      'Explore Local Passages: Check hidden rooms for dimensional boxes and healing treats.',
      'Reach the Next Checkpoint: Advance through the caverns to the next SAVE star.'
    ];
  } else {
    previouslyOn = `You resumed your session in ${gameName || 'your game'}. Your journey is active with recent milestones logged and ready to resume.`;
    whatYouWereUpTo = [
      `Active session with ${events?.length || 0} recorded gameplay events.`,
      `Progress intact with latest checkpoints preserved.`,
      `Ready to jump back into action right where you saved.`
    ];
    nextObjectives = [
      'Review Active Objectives: Check the quest journal or map markers.',
      'Inventory Check: Replenish supplies, ammo, and healing items.',
      'Continue Main Storyline: Head to the primary waypoint.'
    ];
  }

  const recapText = [
    `PREVIOUSLY ON ${gameName ? gameName.toUpperCase() : 'YOUR GAME'}:`,
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

  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) {
    // Intelligent fallback when OPENROUTER_API_KEY is not configured
    const fallback = generateHeuristicFallback(game_name, player_name, save_data, events);
    res.status(200).json(fallback);
    return;
  }

  try {
    const upstream = await fetch(OPENROUTER_URL, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: process.env.OPENROUTER_MODEL || DEFAULT_MODEL,
        messages: [{ role: 'user', content: buildPrompt(game_name, player_name, save_data, events) }],
      }),
    });

    if (!upstream.ok) {
      console.warn(`[recap.js] OpenRouter returned ${upstream.status}. Using fallback.`);
      const fallback = generateHeuristicFallback(game_name, player_name, save_data, events);
      res.status(200).json(fallback);
      return;
    }

    const data = await upstream.json();
    const recap = data?.choices?.[0]?.message?.content?.trim();

    if (!recap) {
      const fallback = generateHeuristicFallback(game_name, player_name, save_data, events);
      res.status(200).json(fallback);
      return;
    }

    res.status(200).json({ recap });
  } catch (err) {
    console.error(`[recap.js] Error: ${err.message}. Using fallback.`);
    const fallback = generateHeuristicFallback(game_name, player_name, save_data, events);
    res.status(200).json(fallback);
  }
}

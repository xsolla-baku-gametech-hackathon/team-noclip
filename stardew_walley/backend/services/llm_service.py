import json
import logging
from typing import Optional
import httpx

from backend.config import settings
from backend.models import GameStateDto, RecapResponseDto
from backend.services.heuristic_service import generate_heuristic_recap

logger = logging.getLogger("xsolla_recap.llm")

SYSTEM_PROMPT = """You are the Xsolla Game Recap engine for Stardew Valley. Your role is to act as a personalized, context-aware memory bridge for a player returning to their farm after weeks or months away. You eliminate resumption friction in under 10 seconds.

STRICT FACTUAL GROUNDING RULES:
1. ZERO HALLUCINATION: Only use facts explicitly provided in the input JSON.
2. NEVER invent quests, items, villagers, seasons, dates, or crop states.
3. NEVER assume the player owns an item or completed a task unless verified in the input.
4. If a field is missing, null, or empty, ignore it gracefully.
5. All IDs have been pre-resolved to human-readable names. Use only those names.

CONTENT CONSTRAINTS:
1. "previouslyOn": EXACTLY TWO SENTENCES.
   - Sentence 1: Remind the player of their current temporal and financial place (e.g., "You returned to Misty Farm on Summer 18, Year 2, with 12,450g in savings.").
   - Sentence 2: Summarize current ongoing efforts or macro-level situation (e.g., "Your farm is in the middle of harvest season while the Community Center awaits several key contributions.").
2. "criticalPriorities": EXACTLY THREE ITEMS (or fewer if fewer exist in the data).
   - Priority hierarchy:
     * HIGH: Dead crops that need clearing; crops ready for harvest today; unwatered crops.
     * HIGH: Quests expiring today (daysLeft == 0) or tomorrow (daysLeft == 1).
     * HIGH: A villager's birthday occurring today or tomorrow.
     * MEDIUM: Active community center missing items that are in season.
     * MEDIUM: Villagers with low friendship hearts (<= 2) worth talking to.
     * LOW: Long-term farm goals and general milestones.
   - Each priority must have:
     * "title": Short action imperative (3-5 words max, e.g., "Harvest Ready Crops").
     * "description": One concise informative sentence with quantities.
     * "importance": "high" | "medium" | "low".
3. "goalTracker":
   - "activeQuests": Max 5 active quests formatted as "Title - X days left" (or "No time limit").
   - "missingBundleItems": Key missing items for the Community Center.
   - "milestones": Current overarching objectives (e.g., "Community Center: 18/30 bundles completed").
4. FORMAT:
   - Output MUST be valid, parseable JSON matching the schema exactly.
   - DO NOT include markdown fences (```json ... ```) or conversational commentary.
"""

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "success": {"type": "BOOLEAN"},
        "previouslyOn": {"type": "STRING"},
        "criticalPriorities": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "title": {"type": "STRING"},
                    "description": {"type": "STRING"},
                    "importance": {"type": "STRING", "enum": ["high", "medium", "low"]},
                },
                "required": ["title", "description", "importance"],
            },
        },
        "goalTracker": {
            "type": "OBJECT",
            "properties": {
                "activeQuests": {"type": "ARRAY", "items": {"type": "STRING"}},
                "missingBundleItems": {"type": "ARRAY", "items": {"type": "STRING"}},
                "milestones": {"type": "ARRAY", "items": {"type": "STRING"}},
            },
            "required": ["activeQuests", "missingBundleItems", "milestones"],
        },
    },
    "required": ["success", "previouslyOn", "criticalPriorities", "goalTracker"],
}


async def generate_llm_recap(state: GameStateDto) -> RecapResponseDto:
    """
    Calls Google Gemini API with structured output schema.
    Falls back gracefully to the heuristic generator on any error or timeout.
    """
    if not settings.ENABLE_LLM or not settings.GEMINI_API_KEY:
        logger.info("LLM disabled or GEMINI_API_KEY not set. Using heuristic generator.")
        return generate_heuristic_recap(state)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent"
    headers = {"x-goog-api-key": settings.GEMINI_API_KEY}

    state_json = state.model_dump_json(by_alias=True)

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            f"{SYSTEM_PROMPT}\n\n"
                            f"CURRENT GAME STATE:\n{state_json}\n\n"
                            "Generate the structured recap JSON now."
                        )
                    }
                ],
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
            "temperature": 0.2,
            "maxOutputTokens": 800,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS) as client:
            response = await client.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            logger.warning(
                f"Gemini API returned status {response.status_code}: {response.text}. Falling back to heuristic."
            )
            return generate_heuristic_recap(state)

        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            logger.warning("No candidates returned from Gemini. Falling back to heuristic.")
            return generate_heuristic_recap(state)

        text_content = candidates[0]["content"]["parts"][0]["text"]
        parsed_json = json.loads(text_content)
        return RecapResponseDto.model_validate(parsed_json)

    except httpx.TimeoutException:
        logger.warning(f"LLM request timed out (> {settings.HTTP_TIMEOUT_SECONDS}s). Using heuristic fallback.")
        return generate_heuristic_recap(state)
    except Exception as e:
        logger.error(f"Error during LLM generation: {e}. Using heuristic fallback.")
        return generate_heuristic_recap(state)

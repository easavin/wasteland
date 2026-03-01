"""Async wrapper for Google Gemini 2.5 Flash — narration, intent parsing, and voice."""

from __future__ import annotations

import json
import logging
from typing import Any

from google import genai
from google.genai.types import GenerateContentConfig, Part

from bot.config import settings
from bot.narrator.lore import LORE_SUMMARY, FACTION_LORE
from bot.narrator.profiler import PlayerProfiler

logger = logging.getLogger(__name__)


class GeminiNarrator:
    """Generates narrative text, parses intents, and transcribes voice using
    Gemini 2.5 Flash.
    """

    def __init__(self, profiler: PlayerProfiler | None = None):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model
        self.profiler = profiler or PlayerProfiler()

    # ------------------------------------------------------------------
    # Turn narration
    # ------------------------------------------------------------------

    async def generate(
        self,
        state: Any,
        deltas: dict,
        event: dict | None,
        action: str,
        target: str | None,
        language: str,
        is_premium: bool,
        build_error: str | None = None,
        comm_profile: dict | None = None,
    ) -> str:
        """Generate narrative text for a completed turn."""
        word_limit = 200 if is_premium else 100
        lang_name = "Russian" if language == "ru" else "English"

        # Build style description from comm profile
        style_desc = self.profiler.get_style_description(comm_profile or {})

        system_prompt = f"""You are the Narrator of Wasteland Chronicles, a post-apocalyptic
settlement survival game. You speak as a weathered survivor chronicling events
through a crackling radio broadcast.

{LORE_SUMMARY}

NARRATOR VOICE:
- Gritty, sardonic, occasionally darkly humorous
- References the old world with bitter nostalgia
- Adapts to player behavior and communication style

PLAYER STYLE PROFILE:
- Aggression: {state.style_aggression:.1f}/1.0
- Commerce: {state.style_commerce:.1f}/1.0
- Exploration: {state.style_exploration:.1f}/1.0
- Diplomacy: {state.style_diplomacy:.1f}/1.0

PLAYER COMMUNICATION STYLE:
{style_desc}

LANGUAGE: Respond ONLY in {lang_name}.
Keep response to approximately {word_limit} words.

CRITICAL RULES:
- Never break character
- Never reference game mechanics directly (no "+10 food")
- Weave resource changes into narrative naturally
- End with a brief hint about what might come next
- Match the player's communication style and vocabulary level"""

        # Build context from narrator memory
        memory_text = ""
        if state.narrator_memory:
            memory_text = "\n\nPrevious broadcasts:\n" + "\n".join(state.narrator_memory[-5:])

        # Build turn description
        turn_desc = f"""TURN {state.turn_number}/50:

Settlement: {state.settlement_name}
Action taken: {action}{f' ({target})' if target else ''}
{f'Build error: {build_error}' if build_error else ''}

Resource changes this turn:
{json.dumps({k: v for k, v in deltas.items() if v != 0}, indent=2)}

Current state after changes:
- Population: {state.population}
- Food: {state.food}
- Scrap: {state.scrap}
- Morale: {state.morale}/100
- Defense: {state.defense}/100
- Buildings: {json.dumps(state.buildings)}
- Starvation counter: {state.food_zero_turns}/2

Faction relations:
- Raiders: {state.raiders_rep} ({self._rep_label(state.raiders_rep)})
- Traders: {state.traders_rep} ({self._rep_label(state.traders_rep)})
- Remnants: {state.remnants_rep} ({self._rep_label(state.remnants_rep)})"""

        if event:
            turn_desc += f"""

Random event occurred: {event['name']}
Event hint: {event.get('narration_hint', '')}"""

        if state.status in ("won", "lost"):
            turn_desc += f"\n\nGAME OUTCOME: {state.status.upper()}"

        prompt = turn_desc + memory_text

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.85,
                max_output_tokens=500 if is_premium else 250,
            ),
        )
        return response.text.strip()

    # ------------------------------------------------------------------
    # Onboarding narration
    # ------------------------------------------------------------------

    async def generate_onboarding(
        self,
        settlement_name: str,
        language: str,
        player_name: str,
    ) -> str:
        """Generate a welcome narrative for a new game."""
        lang_name = "Russian" if language == "ru" else "English"

        system_instruction = f"""You are the Narrator of Wasteland Chronicles, a post-apocalyptic
settlement survival game. You speak as a weathered survivor broadcasting on a crackling shortwave radio.

{LORE_SUMMARY}

CRITICAL RULES — NEVER BREAK THESE:
- Write PURE atmospheric narrative storytelling ONLY
- NEVER mention game mechanics, stats, numbers, turns, resources, or game systems
- NEVER include lines like "population: X" or "food: Y" or "turn 1/50"
- NEVER list actions or buttons — the game UI handles that
- Write ONLY in {lang_name}"""

        prompt = f"""Write a 200-250 word origin story for a new survivor who just arrived at the ruins
that will become their settlement "{settlement_name}".

The survivor's name is {player_name}. They have led a desperate group of 50 people here after weeks
of wandering the Wasteland. This place — crumbling structures, overgrown lots, the smell of old fire
and rust — is their last chance.

Structure your narration in this order:
1. Set the scene: describe the desolate location as {player_name} first lays eyes on it at dusk
2. Show the human weight: the exhausted faces of the 50 survivors looking to them for hope
3. Reference the fractured world outside: Raiders circling like wolves, Trader caravans that demand too much, the Remnants and their strange knowledge
4. End with the narrator passing the burden directly to the player: something like "Now it falls to you, {player_name}. What do you do first?"

Tone: gritty shortwave radio broadcast, weathered and sardonic, but with a thread of desperate hope.
Length: 200-250 words. Language: {lang_name} ONLY."""

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.88,
                max_output_tokens=700,
            ),
        )
        return response.text.strip()

    # ------------------------------------------------------------------
    # Free-text intent parsing
    # ------------------------------------------------------------------

    async def parse_intent(self, text: str, language: str) -> dict | None:
        """Parse a free-text player message into a game action.

        Returns {"action": str, "target": str|None} or None if unparseable.
        """
        prompt = f"""The player sent this message in a post-apocalyptic settlement game:
"{text}"

Valid actions: build (target: farm/watchtower/workshop/barracks/shelter/clinic),
explore, trade, defend, diplomacy (target: raiders/traders/remnants), rest

Respond with ONLY valid JSON, no markdown:
{{"action": "action_name", "target": "target_or_null"}}

If you cannot determine a valid action, respond: {{"action": null, "target": null}}"""

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=100,
                ),
            )
            text_resp = response.text.strip()
            # Clean potential markdown wrapping
            if text_resp.startswith("```"):
                text_resp = text_resp.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            result = json.loads(text_resp)
            if result.get("action"):
                return result
        except Exception:
            logger.exception("Intent parsing failed for: %s", text[:100])
        return None

    # ------------------------------------------------------------------
    # Voice transcription
    # ------------------------------------------------------------------

    async def transcribe_voice(self, audio_bytes: bytes, language: str) -> dict | None:
        """Transcribe voice message and extract game command.

        Returns {"transcription": str, "action": str|None, "target": str|None}
        """
        prompt = """Transcribe this voice message from a post-apocalyptic strategy game player.
Extract their intended game command.

Valid commands: build [building], explore, trade, defend, diplomacy [faction], rest, status

Respond with ONLY valid JSON, no markdown:
{"transcription": "full text heard", "action": "command_name_or_null", "target": "target_or_null"}"""

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=[
                    prompt,
                    Part.from_bytes(data=audio_bytes, mime_type="audio/ogg"),
                ],
                config=GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=200,
                ),
            )
            text_resp = response.text.strip()
            if text_resp.startswith("```"):
                text_resp = text_resp.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            return json.loads(text_resp)
        except Exception:
            logger.exception("Voice transcription failed")
        return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _rep_label(rep: int) -> str:
        if rep <= -50:
            return "hostile"
        elif rep <= -20:
            return "unfriendly"
        elif rep <= 20:
            return "neutral"
        elif rep <= 50:
            return "friendly"
        return "allied"

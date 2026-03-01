"""Async wrapper for Google Gemini 2.5 Flash — narration, intent parsing, and voice."""

from __future__ import annotations

import json
import logging
from typing import Any

from google import genai
from google.genai.types import GenerateContentConfig, Part, ThinkingConfig

from bot.config import settings
from bot.engine.classes import PLAYER_CLASSES
from bot.engine.skills import SKILLS
from bot.narrator.lore import LORE_SUMMARY, FACTION_LORE, CLASS_LORE, ZONE_LORE
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
        xp_earned: int = 0,
        new_levels: list | None = None,
    ) -> str:
        """Generate narrative text for a completed turn."""
        word_limit = 200 if is_premium else 100
        lang_name = "Russian" if language == "ru" else "English"

        # Build style description from comm profile
        style_desc = self.profiler.get_style_description(comm_profile or {})

        # Class info for narrator context
        cls_info = PLAYER_CLASSES.get(state.player_class, {})
        cls_name_en = cls_info.get("name", {}).get("en", "Survivor")
        cls_lore = CLASS_LORE.get(state.player_class, "")
        zone_lore = ZONE_LORE.get(state.zone, "")

        # Summarize learned skills for narrator flavor
        skills_desc = ""
        if state.skills:
            learned = []
            for sid, rank in state.skills.items():
                spec = SKILLS.get(sid)
                if spec and rank > 0:
                    learned.append(f"{spec['name']['en']} (rank {rank})")
            if learned:
                skills_desc = "Learned skills: " + ", ".join(learned)

        system_prompt = f"""You are the Narrator of Wasteland Chronicles, a post-apocalyptic
settlement RPG. You speak as a weathered survivor chronicling events
through a crackling radio broadcast.

{LORE_SUMMARY}

PLAYER CLASS: {cls_name_en} (Level {state.level}, Zone {state.zone})
{cls_lore}
{f"ZONE: " + zone_lore if zone_lore else ""}
{skills_desc}

NARRATOR VOICE:
- Gritty, sardonic, occasionally darkly humorous
- References the old world with bitter nostalgia
- Adapts to player behavior and communication style
- Acknowledge the player's class identity and growing reputation when relevant

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
- Never reference game mechanics directly (no "+10 food" or "XP")
- Never mention "Week X", "Week Two", or count weeks in the narrative — the journey has no fixed end
- Weave resource changes into narrative naturally
- End with a brief hint about what might come next
- Match the player's communication style and vocabulary level
- If the player leveled up, weave a sense of growing reputation/power into the narrative
- Reference the zone's dangers naturally (higher zones = more hostile territory)"""

        # Build context from narrator memory
        memory_text = ""
        if state.narrator_memory:
            memory_text = "\n\nPrevious broadcasts:\n" + "\n".join(state.narrator_memory[-5:])

        # Build turn description
        level_up_text = ""
        if new_levels:
            level_up_text = f"\nLEVEL UP! Player reached level {new_levels[-1]}. Weave a sense of growing power/reputation into the narrative."

        turn_desc = f"""SETTLEMENT STATE:

Settlement: {state.settlement_name}
Class: {cls_name_en} | Level {state.level} | Zone {state.zone}
Action taken: {action}{f' ({target})' if target else ''}
{f'Build error: {build_error}' if build_error else ''}
{level_up_text}

Resource changes this turn:
{json.dumps({k: v for k, v in deltas.items() if v != 0}, indent=2)}

Current state after changes:
- Population: {state.population}
- Food: {state.food}
- Scrap: {state.scrap}
- Gold: {state.gold}
- Morale: {state.morale}/100
- Defense: {state.defense}/100
- Buildings: {json.dumps(state.buildings)}
- Skills: {json.dumps(state.skills) if state.skills else "none"}
- Starvation counter: {state.food_zero_turns}

Faction relations:
- Raiders: {state.raiders_rep} ({self._rep_label(state.raiders_rep)})
- Traders: {state.traders_rep} ({self._rep_label(state.traders_rep)})
- Remnants: {state.remnants_rep} ({self._rep_label(state.remnants_rep)})"""

        if event:
            turn_desc += f"""

Random event occurred: {event['name']}
Event hint: {event.get('narration_hint', '')}"""

        if state.status == "lost":
            turn_desc += "\n\nGAME OUTCOME: DEFEAT. The settlement has fallen."

        prompt = turn_desc + memory_text

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.85,
                max_output_tokens=500 if is_premium else 250,
                thinking_config=ThinkingConfig(thinking_budget=0),
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
        player_class: str = "",
    ) -> str:
        """Generate a welcome narrative for a new game."""
        lang_name = "Russian" if language == "ru" else "English"
        cls_info = PLAYER_CLASSES.get(player_class, {})
        cls_name = cls_info.get("name", {}).get("en", "survivor")
        cls_desc = cls_info.get("description", {}).get("en", "")
        cls_lore = CLASS_LORE.get(player_class, "")

        system_instruction = f"""You are the Narrator of Wasteland Chronicles, a post-apocalyptic
settlement RPG. You speak as a weathered survivor broadcasting on a crackling shortwave radio.

{LORE_SUMMARY}

CRITICAL RULES — NEVER BREAK THESE:
- Write atmospheric narrative storytelling — no raw stats, no UI instructions
- NEVER include lines like "population: X" or "food: Y" or "level 1"
- NEVER list buttons or mention game UI
- Practical guidance must come from the Navigator's voice, as advice from a survivor
- Write ONLY in {lang_name}"""

        prompt = f"""Write a 250-320 word opening scene for a new survivor arriving at their future settlement.

The survivor's name is {player_name}. They are a {cls_name} — {cls_desc}
{cls_lore}

They have led 50 desperate people here after weeks of wandering.
The settlement will be called "{settlement_name}" — a ruin of crumbling concrete, overgrown lots, rusted steel.

You are "the Navigator" — a weathered voice on a shortwave radio who has been watching this frequency,
waiting for someone to make contact. You just picked up {player_name}'s signal.

Structure in this order:
1. OPENING (3-4 sentences): The shortwave crackles to life — you (the Navigator) make first contact with {player_name}. Describe what you see from your vantage point: the ruin they've arrived at, the dusk light, the exhausted 50. Acknowledge their background as a {cls_name} — the Navigator has heard of them.

2. THE WORLD (3-4 sentences): Paint the dangers — Raiders who smell weakness, the Trader Guild who'll bleed them dry, the Remnants with their strange knowledge. Make it vivid and specific, not a list.

3. PRACTICAL GUIDANCE (4-5 sentences): The Navigator shares hard-won survival wisdom naturally, as advice between survivors. Tailor advice to their class strengths. Work these into the narrative:
   - Food runs out fast — they need farms, and soon
   - The ruins nearby are full of useful scrap — worth sending scouts
   - Walls won't build themselves, and Raiders test the weak
   - The factions can be allies or enemies — depends on how {player_name} plays it
   - Sometimes the best move is to let people rest and recover
   - Just talk — say what you want to do in plain words, the Navigator will understand

4. CLOSING (1-2 sentences): End with a direct question to {player_name} — draw them into their first decision. Make it feel urgent but not overwhelming. Reference their {cls_name} skills.

Tone: sardonic, world-weary, but genuinely invested in this survivor making it.
The Navigator has seen settlements rise and fall. This time feels different — maybe.
Language: {lang_name} ONLY."""

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.88,
                max_output_tokens=1200,
                thinking_config=ThinkingConfig(thinking_budget=0),
            ),
        )
        return response.text.strip()

    # ------------------------------------------------------------------
    # Free-text intent parsing
    # ------------------------------------------------------------------

    async def parse_intent(self, text: str, language: str) -> dict | None:
        """Parse a free-text player message into a game action.

        Returns {"action": str, "target": str|None} or None if not a game action.
        """
        prompt = f"""The player sent this message in a post-apocalyptic settlement game:
"{text}"

Valid actions and their targets:
- build — MUST have a target: farm, watchtower, workshop, barracks, shelter, clinic, market, radio_tower, armory, vault
  Examples: "build a farm" → action=build, target=farm; "I want to construct a watchtower" → action=build, target=watchtower; "build a market" → action=build, target=market
- explore — no target needed
- trade — no target needed
- defend — no target needed
- diplomacy — optional target: raiders, traders, remnants
- rest — no target needed

Output a single JSON object. If the message maps to a valid action:
{{"action": "action_name", "target": "target_or_null"}}
If it does NOT map to any valid action:
{{"action": null, "target": null}}

IMPORTANT: For "build", always extract the building type from the message as the target."""

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=60,
                    response_mime_type="application/json",
                    thinking_config=ThinkingConfig(thinking_budget=0),
                ),
            )
            text_resp = response.text.strip()
            # Regex fallback: extract the first {...} block in case of extra text
            if not text_resp.startswith("{"):
                import re as _re
                m = _re.search(r'\{[^}]*\}', text_resp)
                text_resp = m.group() if m else text_resp
            result = json.loads(text_resp)
            if result.get("action"):
                return result
        except Exception:
            logger.debug("Intent parsing failed for: %s", text[:100])
        return None

    async def generate_aside(self, player_message: str, state, language: str) -> str:
        """Generate a short in-character narrator reply to a non-action player message."""
        lang_name = "Russian" if language == "ru" else "English"

        # Build rich context about the settlement
        buildings_desc = "no buildings yet"
        if state.buildings:
            buildings_desc = ", ".join(
                f"{name} x{count}" for name, count in state.buildings.items() if count > 0
            )

        memory_text = ""
        if state.narrator_memory:
            memory_text = "\n\nRecent events (use these to maintain narrative continuity):\n" + "\n".join(state.narrator_memory[-5:])

        cls_info = PLAYER_CLASSES.get(state.player_class, {})
        cls_name = cls_info.get("name", {}).get("en", "Survivor")
        zone_lore = ZONE_LORE.get(state.zone, "")

        # Summarize learned skills
        skills_desc = "none"
        if state.skills:
            learned = []
            for sid, rank in state.skills.items():
                spec = SKILLS.get(sid)
                if spec and rank > 0:
                    learned.append(f"{spec['name']['en']} (rank {rank})")
            if learned:
                skills_desc = ", ".join(learned)

        prompt = f"""The player said: "{player_message}"

CURRENT SETTLEMENT STATE — use this to give informed, specific answers:
- Settlement: {state.settlement_name}
- Class: {cls_name} | Level {state.level} | Zone {state.zone}
- Population: {state.population} survivors
- Food: {state.food} (consumed each week — runs out = starvation)
- Scrap: {state.scrap} (building material and trade currency)
- Gold: {state.gold} (rare currency for special purchases via /shop)
- Morale: {state.morale}/100
- Defense: {state.defense}/100
- Buildings: {buildings_desc}
- Learned skills: {skills_desc}
- Skill points available: {state.skill_points}
- Faction relations: Raiders {state.raiders_rep:+d} ({self._rep_label(state.raiders_rep)}), Traders {state.traders_rep:+d} ({self._rep_label(state.traders_rep)}), Remnants {state.remnants_rep:+d} ({self._rep_label(state.remnants_rep)})
{f"ZONE CONTEXT: " + zone_lore if zone_lore else ""}
{memory_text}

WHAT THE PLAYER CAN DO (reference naturally when relevant):
- Build structures: farm (food), watchtower (defense), workshop (scrap), barracks (defense), shelter (morale), clinic (morale + population), market (gold, L3+), radio tower (defense, L7+), armory (defense, L12+), vault (gold, L20+)
- Send scouts to explore the ruins for scrap and gold
- Trade scrap for food and gold with passing caravans
- Fortify defenses against raids
- Negotiate with factions: Raiders, Trader Guild, Remnants
- Let the settlement rest to recover morale
- Spend gold at the shop (/shop): emergency rations, mercenaries, faction gifts, recruit settlers, scrap shipment, skill respec
- Invest skill points in specializations (/skills): survival, economy, military, social categories

This message is NOT a game command — it's a question, observation, or comment.
Respond in character as the Navigator. Be SPECIFIC and USEFUL:
- If they ask "where am I?" — describe the settlement's location, the ruins, what surrounds them
- If they ask about factions — share what you know from lore, their current relations
- If they ask "what can I do?" — describe their options as practical survival advice
- If they ask about the world — draw from the lore, be vivid and detailed
- If they ask about their class or level — reference their growing reputation
- If they ask about skills — describe their learned abilities and available skill points
- If they ask about gold/shop — mention what they can buy and how much they have
Always ground your answer in the actual settlement state and lore.
End with a natural nudge toward action — suggest something relevant to their situation.
Never mention "Week X" or count weeks — the journey has no fixed end.

100-150 words. Language: {lang_name} ONLY."""

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=GenerateContentConfig(
                system_instruction=(
                    f"You are the Navigator of Wasteland Chronicles — a shortwave radio contact "
                    f"who guides survivors from an unknown location. You have been watching this "
                    f"settlement and know its situation intimately.\n\n{LORE_SUMMARY}\n\n"
                    f"{FACTION_LORE.get('raiders', '')}\n{FACTION_LORE.get('traders', '')}\n"
                    f"{FACTION_LORE.get('remnants', '')}\n\n"
                    f"Never break character. Give specific, grounded answers — not vague deflections. "
                    f"Respond ONLY in {lang_name}."
                ),
                temperature=0.85,
                max_output_tokens=600,
                thinking_config=ThinkingConfig(thinking_budget=0),
            ),
        )
        return response.text.strip()

    # ------------------------------------------------------------------
    # Display name moderation
    # ------------------------------------------------------------------

    async def validate_display_name(self, text: str, language: str) -> tuple[bool, str | None]:
        """Check if a display name is appropriate.

        Returns (ok, rejection_reason). Reject if: profanity, slurs,
        offensive content, impersonation attempts. Never return the
        actual offensive content in the reason.
        """
        lang_name = "Russian" if language == "ru" else "English"
        prompt = f"""You are a content moderator for a post-apocalyptic multiplayer game.

A player wants to use this as their display name (how other survivors will see them): "{text}"

Check if the name is appropriate. REJECT if it contains:
- Profanity, swears, or vulgarity (in any language: English, Russian, etc.)
- Slurs or hate speech
- Offensive or derogatory content
- Impersonation of real people
- Spam-like content (repeated characters, etc.)

ALLOW:
- Creative/fantasy names (e.g. "Commander Rex", "DustWalker", "Rust")
- Numbers if not offensive (e.g. "Scout47")
- Spaces and hyphens
- Non-Latin scripts if appropriate

Respond with ONLY valid JSON, no markdown:
{{"ok": true}} if acceptable
{{"ok": false, "reason": "generic"}} if not acceptable — "reason" must be a generic phrase like "inappropriate" or "contains prohibited content", NEVER repeat the offensive text."""

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=GenerateContentConfig(
                    temperature=0.0,
                    max_output_tokens=80,
                    response_mime_type="application/json",
                    thinking_config=ThinkingConfig(thinking_budget=0),
                ),
            )
            text_resp = response.text.strip()
            if not text_resp.startswith("{"):
                import re as _re
                m = _re.search(r'\{[^}]*\}', text_resp)
                text_resp = m.group() if m else text_resp
            result = json.loads(text_resp)
            ok = result.get("ok", False)
            reason = result.get("reason") if not ok else None
            return (ok, reason)
        except Exception:
            logger.exception("Display name validation failed — defaulting to reject")
            return (False, "validation_error")

    # ------------------------------------------------------------------
    # Voice transcription
    # ------------------------------------------------------------------

    async def transcribe_voice(self, audio_bytes: bytes, language: str) -> dict | None:
        """Transcribe voice message and extract game command.

        Returns {"transcription": str, "action": str|None, "target": str|None}
        """
        prompt = """Transcribe this voice message from a post-apocalyptic strategy game player.
Extract their intended game command.

Valid commands: build [building: farm/watchtower/workshop/barracks/shelter/clinic/market/radio_tower/armory/vault], explore, trade, defend, diplomacy [faction: raiders/traders/remnants], rest, status

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
                    thinking_config=ThinkingConfig(thinking_budget=0),
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

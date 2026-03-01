"""Player communication profiler — learns and adapts to player voice.

Tracks vocabulary level, tone, message length, humor, and preferred themes.
Updates are applied via exponential moving average so the profile builds up
gradually over 3-5 turns and reaches good adaptation by turn 10.
"""

from __future__ import annotations

import json
import logging
import re
from collections import Counter

import asyncpg

logger = logging.getLogger(__name__)

_EMA_ALPHA = 0.25  # Blend factor for profile updates

# Word complexity heuristics
_SIMPLE_MAX_LEN = 5
_LITERARY_MIN_LEN = 8

# Tone markers
_CASUAL_MARKERS = {
    "lol", "lmao", "yo", "nah", "yeah", "haha", "heh", "bruh", "dude",
    "gonna", "wanna", "gotta", "kinda", "sorta", "cuz", "tho",
    "лол", "хах", "ахах", "ну", "чё", "чо", "ваще", "норм", "збс",
    "ок", "окей", "блин", "фиг",
}
_FORMAL_MARKERS = {
    "therefore", "consequently", "furthermore", "regarding", "pursuant",
    "nevertheless", "accordingly", "henceforth",
    "следовательно", "таким образом", "относительно", "впоследствии",
    "соответственно",
}

# Theme keywords
_THEME_KEYWORDS = {
    "combat": {"attack", "fight", "raid", "war", "kill", "defend", "army", "warrior",
               "атака", "бой", "рейд", "война", "армия", "воин"},
    "trade": {"trade", "buy", "sell", "merchant", "deal", "profit", "market",
              "торговля", "купить", "продать", "сделка"},
    "exploration": {"explore", "scout", "discover", "search", "find", "ruins",
                    "разведка", "искать", "найти", "руины"},
    "lore": {"network", "hegemony", "wasting", "collapse", "machines", "history",
             "сеть", "гегемония", "мор", "коллапс", "машины", "история"},
    "building": {"build", "construct", "farm", "wall", "shelter",
                 "строить", "ферма", "стена", "убежище"},
}


def _analyze_vocabulary(text: str) -> float:
    """Return 0.0 (simple) to 1.0 (literary) based on word length distribution."""
    words = re.findall(r'[a-zA-Zа-яА-ЯёЁ]+', text)
    if not words:
        return 0.5
    avg_len = sum(len(w) for w in words) / len(words)
    if avg_len <= _SIMPLE_MAX_LEN:
        return 0.2
    elif avg_len >= _LITERARY_MIN_LEN:
        return 0.9
    else:
        return 0.3 + (avg_len - _SIMPLE_MAX_LEN) / (_LITERARY_MIN_LEN - _SIMPLE_MAX_LEN) * 0.5


def _analyze_tone(text: str) -> float:
    """Return 0.0 (casual) to 1.0 (formal)."""
    words = set(re.findall(r'[a-zA-Zа-яА-ЯёЁ]+', text.lower()))
    casual_count = len(words & _CASUAL_MARKERS)
    formal_count = len(words & _FORMAL_MARKERS)

    # Emoji/emoticon presence = casual
    emoji_count = len(re.findall(r'[😀-🙏🌀-🗿🚀-🛿🤀-🧿]+', text))
    casual_count += min(emoji_count, 3)

    if casual_count > formal_count:
        return max(0.0, 0.3 - casual_count * 0.1)
    elif formal_count > casual_count:
        return min(1.0, 0.7 + formal_count * 0.1)
    return 0.5


def _analyze_humor(text: str) -> float:
    """Return 0.0 (serious) to 1.0 (humorous)."""
    lower = text.lower()
    humor_signals = 0
    if any(m in lower for m in ("lol", "lmao", "haha", "хах", "ахах", "😂", "🤣")):
        humor_signals += 2
    if "!" in text and "?" in text:
        humor_signals += 1
    if any(m in lower for m in ("joke", "funny", "шутк", "смешн")):
        humor_signals += 1
    return min(1.0, humor_signals * 0.25)


def _analyze_length(text: str) -> float:
    """Return 0.0 (terse) to 1.0 (verbose)."""
    word_count = len(text.split())
    if word_count <= 3:
        return 0.1
    elif word_count <= 8:
        return 0.4
    elif word_count <= 15:
        return 0.6
    else:
        return 0.9


def _detect_themes(text: str) -> list[str]:
    """Return list of theme tags found in text."""
    words = set(re.findall(r'[a-zA-Zа-яА-ЯёЁ]+', text.lower()))
    found = []
    for theme, keywords in _THEME_KEYWORDS.items():
        if words & keywords:
            found.append(theme)
    return found


def _ema(old: float, new: float, alpha: float = _EMA_ALPHA) -> float:
    return (1.0 - alpha) * old + alpha * new


class PlayerProfiler:
    """Analyzes player messages and updates their communication profile."""

    async def analyze_and_update(
        self,
        pool: asyncpg.Pool,
        player_id: str,
        text: str,
        current_profile: dict | None,
    ) -> dict:
        """Analyze text and return updated comm_profile dict.

        Also persists the update to the database.
        """
        if isinstance(current_profile, str):
            try:
                profile = json.loads(current_profile)
            except (json.JSONDecodeError, TypeError):
                profile = {}
        elif isinstance(current_profile, dict):
            profile = dict(current_profile)
        else:
            profile = {}

        # Analyze current message
        vocab_score = _analyze_vocabulary(text)
        tone_score = _analyze_tone(text)
        humor_score = _analyze_humor(text)
        length_score = _analyze_length(text)
        themes = _detect_themes(text)

        # Update via EMA
        profile["vocabulary_level"] = _ema(
            profile.get("vocabulary_level", 0.5), vocab_score,
        )
        profile["tone"] = _ema(profile.get("tone", 0.5), tone_score)
        profile["humor_affinity"] = _ema(
            profile.get("humor_affinity", 0.3), humor_score,
        )
        profile["message_length"] = _ema(
            profile.get("message_length", 0.5), length_score,
        )

        # Track theme preferences (keep top 5)
        theme_counts: dict = profile.get("theme_counts", {})
        for t in themes:
            theme_counts[t] = theme_counts.get(t, 0) + 1
        profile["theme_counts"] = theme_counts
        profile["preferred_themes"] = sorted(
            theme_counts, key=theme_counts.get, reverse=True,
        )[:5]

        # Keep last 5 sample phrases (non-trivial messages)
        samples: list = profile.get("sample_phrases", [])
        if len(text.split()) >= 3:
            samples.append(text[:200])  # Truncate very long messages
            samples = samples[-5:]
        profile["sample_phrases"] = samples

        # Message count for profile maturity tracking
        profile["message_count"] = profile.get("message_count", 0) + 1

        # Persist
        try:
            await pool.execute(
                "UPDATE players SET comm_profile = $1::jsonb WHERE id = $2",
                json.dumps(profile),
                player_id,
            )
        except Exception:
            logger.exception("Failed to persist comm_profile for player %s", player_id)

        return profile

    def get_style_description(self, profile: dict) -> str:
        """Generate a natural language description of the player's comm style
        for injection into the narrator prompt."""
        if not profile or profile.get("message_count", 0) < 2:
            return "New player — use a balanced, welcoming tone."

        parts = []

        # Vocabulary
        vocab = profile.get("vocabulary_level", 0.5)
        if vocab < 0.3:
            parts.append("uses simple, direct language")
        elif vocab > 0.7:
            parts.append("uses sophisticated, literary vocabulary")
        else:
            parts.append("uses moderate vocabulary")

        # Tone
        tone = profile.get("tone", 0.5)
        if tone < 0.3:
            parts.append("speaks casually with slang")
        elif tone > 0.7:
            parts.append("speaks formally and precisely")

        # Humor
        humor = profile.get("humor_affinity", 0.3)
        if humor > 0.5:
            parts.append("enjoys humor and sarcasm")
        elif humor < 0.2:
            parts.append("prefers serious tone")

        # Length
        length = profile.get("message_length", 0.5)
        if length < 0.3:
            parts.append("prefers short, punchy responses")
        elif length > 0.7:
            parts.append("appreciates detailed, lengthy responses")

        # Themes
        themes = profile.get("preferred_themes", [])
        if themes:
            parts.append(f"most interested in: {', '.join(themes[:3])}")

        desc = "The player " + ", ".join(parts) + "."

        # Add sample phrases for style mimicry
        samples = profile.get("sample_phrases", [])
        if samples:
            desc += "\n\nRecent player messages (match this style):\n"
            for s in samples[-3:]:
                desc += f'- "{s}"\n'

        return desc

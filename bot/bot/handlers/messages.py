"""Free text message handler — interprets natural language input."""

from __future__ import annotations

import logging
import re

from telegram import Update
from telegram.ext import ContextTypes

from bot.db.queries.players import get_player_by_telegram_id
from bot.db.queries.game_states import get_active_game
from bot.engine.game_state import GameState
from bot.handlers.game import _execute_turn
from bot.i18n import get_text

logger = logging.getLogger(__name__)

# Simple keyword mapping for when narrator is unavailable
_KEYWORD_MAP = {
    # English
    "build": ("build", None),
    "farm": ("build", "farm"),
    "watchtower": ("build", "watchtower"),
    "workshop": ("build", "workshop"),
    "barracks": ("build", "barracks"),
    "shelter": ("build", "shelter"),
    "clinic": ("build", "clinic"),
    "explore": ("explore", None),
    "scout": ("explore", None),
    "search": ("explore", None),
    "trade": ("trade", None),
    "barter": ("trade", None),
    "sell": ("trade", None),
    "buy": ("trade", None),
    "defend": ("defend", None),
    "fortify": ("defend", None),
    "wall": ("defend", None),
    "guard": ("defend", None),
    "diplomacy": ("diplomacy", None),
    "negotiate": ("diplomacy", None),
    "ally": ("diplomacy", None),
    "raiders": ("diplomacy", "raiders"),
    "traders": ("diplomacy", "traders"),
    "remnants": ("diplomacy", "remnants"),
    "rest": ("rest", None),
    "sleep": ("rest", None),
    "wait": ("rest", None),
    # Russian
    "строить": ("build", None),
    "ферма": ("build", "farm"),
    "вышка": ("build", "watchtower"),
    "мастерская": ("build", "workshop"),
    "казарма": ("build", "barracks"),
    "убежище": ("build", "shelter"),
    "клиника": ("build", "clinic"),
    "разведка": ("explore", None),
    "искать": ("explore", None),
    "торговля": ("trade", None),
    "торговать": ("trade", None),
    "оборона": ("defend", None),
    "защита": ("defend", None),
    "дипломатия": ("diplomacy", None),
    "рейдеры": ("diplomacy", "raiders"),
    "торговцы": ("diplomacy", "traders"),
    "осколки": ("diplomacy", "remnants"),
    "отдых": ("rest", None),
    "отдыхать": ("rest", None),
}


def _parse_keywords(text: str) -> tuple[str, str | None] | None:
    """Try to extract a game action from plain text via keywords."""
    words = re.findall(r'\w+', text.lower())
    for word in words:
        if word in _KEYWORD_MAP:
            return _KEYWORD_MAP[word]
    return None


async def handle_free_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle non-command text messages as game actions."""
    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, update.effective_user.id)
    if not player:
        await update.message.reply_text(get_text("free_text_no_game", "en"))
        return

    lang = player.get("language", "en")
    game_row = await get_active_game(pool, str(player["id"]))
    if not game_row:
        await update.message.reply_text(get_text("free_text_no_game", lang))
        return

    text = update.message.text or ""
    narrator = context.bot_data.get("narrator")

    # Try AI intent parsing first
    if narrator:
        try:
            parsed = await narrator.parse_intent(text, lang)
            if parsed and parsed.get("action"):
                # Update comm profile from this message
                profiler = context.bot_data.get("profiler")
                if profiler:
                    await profiler.analyze_and_update(pool, str(player["id"]), text, player.get("comm_profile", {}))

                await _execute_turn(
                    update.message, context, player,
                    parsed["action"], parsed.get("target"),
                )
                return
        except Exception:
            logger.exception("Narrator intent parsing failed")

    # Fallback to keyword matching
    result = _parse_keywords(text)
    if result:
        action, target = result
        profiler = context.bot_data.get("profiler")
        if profiler:
            try:
                await profiler.analyze_and_update(pool, str(player["id"]), text, player.get("comm_profile", {}))
            except Exception:
                logger.exception("Profiler update failed")

        await _execute_turn(update.message, context, player, action, target)
        return

    # Not a game action — if narrator is available, respond in-character
    if narrator:
        try:
            state = GameState.from_db_row(game_row)
            aside = await narrator.generate_aside(text, state, lang)
            await update.message.reply_text(aside, parse_mode="Markdown")
            return
        except Exception:
            logger.exception("Narrator aside failed")

    await update.message.reply_text(get_text("free_text_no_narrator", lang))

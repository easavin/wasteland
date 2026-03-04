"""Free text message handler — interprets natural language input."""

from __future__ import annotations

import logging
import re
from datetime import date as _date

from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from bot.config import settings
from bot.db.queries.players import get_player_by_telegram_id
from bot.db.queries.game_states import get_active_game
from bot.engine.game_state import GameState
from bot.handlers.game import _execute_turn, _premium_keyboard
from bot.i18n import get_text

logger = logging.getLogger(__name__)

# Class name keywords that trigger class info cards (works without an active game)
_CLASS_KEYWORDS: dict[str, str] = {
    # English
    "scavenger": "scavenger",
    "warden": "warden",
    "trader": "trader",
    "diplomat": "diplomat",
    "medic": "medic",
    # Russian
    "старатель": "scavenger",
    "страж": "warden",
    "торговец": "trader",
    "дипломат": "diplomat",
    "медик": "medic",
}


def _detect_class_query(text: str) -> str | None:
    """Return the class_id if the message is asking about a specific class."""
    words = re.findall(r'\w+', text.lower())
    for word in words:
        if word in _CLASS_KEYWORDS:
            return _CLASS_KEYWORDS[word]
    return None


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
    "market": ("build", "market"),
    "radio": ("build", "radio_tower"),
    "radio_tower": ("build", "radio_tower"),
    "armory": ("build", "armory"),
    "vault": ("build", "vault"),
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
    "рынок": ("build", "market"),
    "радиовышка": ("build", "radio_tower"),
    "арсенал": ("build", "armory"),
    "хранилище": ("build", "vault"),
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


def _is_rate_limited(player: dict) -> bool:
    """Return True if this free (non-premium) player has exhausted today's turns."""
    if bool(player.get("is_premium")):
        return False
    today = _date.today()
    last_turn_date = player.get("last_turn_date")
    turns_today = player.get("turns_today") or 0
    if last_turn_date is None or last_turn_date < today:
        turns_today = 0
    return turns_today >= settings.free_turns_per_day


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
    user = update.effective_user
    text = update.message.text or ""
    player = await get_player_by_telegram_id(pool, user.id)

    # Intercept display name input (onboarding flow after class selection)
    if player and context.user_data.get("awaiting_display_name"):
        from bot.handlers.start import handle_display_name_input
        created = await handle_display_name_input(
            update, context, player, text,
        )
        if created:
            return
        # If not created, handle_display_name_input already replied (validation failed)
        return

    # Detect class info queries — these work even before starting a game
    class_id = _detect_class_query(text)
    if class_id:
        from bot.handlers.start import _detect_language
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        lang = player.get("language", "en") if player else _detect_language(user)
        info_text = get_text(f"class_info_{class_id}", lang)
        back_label = get_text("class_info_back", lang)
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(back_label, callback_data="class_info:back"),
        ]])
        await update.message.reply_text(info_text, reply_markup=keyboard, parse_mode="Markdown")
        return

    if not player:
        await update.message.reply_text(get_text("free_text_no_game", "en"))
        return

    lang = player.get("language", "en")
    game_row = await get_active_game(pool, str(player["id"]))
    if not game_row:
        await update.message.reply_text(get_text("free_text_no_game", lang))
        return

    narrator = context.bot_data.get("narrator")

    # Try AI intent parsing first
    if narrator:
        try:
            parsed = await narrator.parse_intent(text, lang)
            if parsed and parsed.get("action"):
                action = parsed["action"]
                target = parsed.get("target") or None

                # If AI returned "build" without a target, try keyword fallback
                if action == "build" and not target:
                    kw_result = _parse_keywords(text)
                    if kw_result and kw_result[0] == "build" and kw_result[1]:
                        target = kw_result[1]

                # Intercept "explore" for multi-step interactive exploration
                if action == "explore":
                    state = GameState.from_db_row(game_row)
                    from bot.handlers.explore import start_exploration
                    await start_exploration(update, context, player, state)
                    return

                # Update comm profile from this message
                profiler = context.bot_data.get("profiler")
                if profiler:
                    await profiler.analyze_and_update(pool, str(player["id"]), text, player.get("comm_profile", {}))

                await _execute_turn(
                    update.message, context, player,
                    action, target,
                )
                return
        except Exception:
            logger.exception("Narrator intent parsing failed")

    # Fallback to keyword matching
    result = _parse_keywords(text)
    if result:
        action, target = result

        # Intercept "explore" for multi-step interactive exploration
        if action == "explore":
            state = GameState.from_db_row(game_row)
            from bot.handlers.explore import start_exploration
            await start_exploration(update, context, player, state)
            return

        profiler = context.bot_data.get("profiler")
        if profiler:
            try:
                await profiler.analyze_and_update(pool, str(player["id"]), text, player.get("comm_profile", {}))
            except Exception:
                logger.exception("Profiler update failed")

        await _execute_turn(update.message, context, player, action, target)
        return

    # If the player has hit their daily turn cap, don't make any API calls —
    # return a hardcoded rate-limit message with the premium upgrade button.
    if _is_rate_limited(player):
        rate_text = get_text(
            "turn_rate_limited", lang,
            max_turns=settings.free_turns_per_day,
            price=settings.premium_price_stars,
        )
        await update.message.reply_text(rate_text, reply_markup=_premium_keyboard(lang), parse_mode="Markdown")
        return

    # Not a game action — if narrator is available, respond in-character
    if narrator:
        try:
            state = GameState.from_db_row(game_row)
            aside = await narrator.generate_aside(text, state, lang)
            try:
                await update.message.reply_text(aside, parse_mode="Markdown")
            except BadRequest:
                await update.message.reply_text(aside)
            return
        except Exception:
            logger.exception("Narrator aside failed")

    await update.message.reply_text(get_text("free_text_no_narrator", lang))

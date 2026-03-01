"""Core game handlers — turns, status, callbacks, and action routing."""

from __future__ import annotations

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.config import settings
from bot.db.queries.players import get_player_by_telegram_id, check_and_consume_turn
from bot.db.queries.game_states import get_active_game, end_game, create_game
from bot.db.queries.analytics import log_event
from bot.engine.factions import get_faction_status
from bot.engine.game_state import GameState
from bot.engine.turn_processor import process_turn
from bot.i18n import get_text

logger = logging.getLogger(__name__)

VALID_ACTIONS = {"build", "explore", "trade", "defend", "diplomacy", "rest"}


async def _reply(query_or_message, text: str, **kwargs) -> None:
    """Always send a new reply message — never edit existing ones.

    Accepts either a Message or a CallbackQuery as the first argument.
    This keeps the chat history intact so narration accumulates as a log.
    """
    if hasattr(query_or_message, "message"):
        # CallbackQuery — reply to the message the button was attached to
        await query_or_message.message.reply_text(text, **kwargs)
    else:
        # Plain Message (text command, voice, etc.)
        await query_or_message.reply_text(text, **kwargs)


# ------------------------------------------------------------------
# /status command
# ------------------------------------------------------------------

async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show full settlement status."""
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

    state = GameState.from_db_row(game_row)
    text = _format_full_status(state, lang)
    await update.message.reply_text(
        text,
        reply_markup=_status_keyboard(lang),
        parse_mode="Markdown",
    )


# ------------------------------------------------------------------
# Callback query handler — routes all button presses
# ------------------------------------------------------------------

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Dispatch inline keyboard button presses.

    Buttons are status/info only — game actions happen via text messages.
    All responses are sent as new messages so chat history stays intact.
    """
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, query.from_user.id)
    if not player:
        await query.message.reply_text(get_text("free_text_no_game", "en"))
        return

    lang = player.get("language", "en")
    player_id = str(player["id"])

    if data == "cmd:status":
        game_row = await get_active_game(pool, player_id)
        if not game_row:
            await query.message.reply_text(get_text("free_text_no_game", lang))
            return
        state = GameState.from_db_row(game_row)
        await query.message.reply_text(
            _format_full_status(state, lang),
            reply_markup=_status_keyboard(lang),
            parse_mode="Markdown",
        )


# ------------------------------------------------------------------
# Turn execution
# ------------------------------------------------------------------

async def _execute_turn(
    query_or_message,
    context: ContextTypes.DEFAULT_TYPE,
    player: dict,
    action: str,
    target: str | None = None,
) -> None:
    """Process a single game turn and reply with results."""
    pool = context.bot_data["db_pool"]
    lang = player.get("language", "en")
    player_id = str(player["id"])
    is_premium = bool(player.get("is_premium"))

    if action not in VALID_ACTIONS:
        text = get_text("turn_invalid_action", lang, action=action)
        await _reply(query_or_message, text, reply_markup=_status_keyboard(lang))
        return

    # Rate limit check
    can_play = await check_and_consume_turn(
        pool, player_id, is_premium, settings.free_turns_per_day,
    )
    if not can_play:
        text = get_text("turn_rate_limited", lang, max_turns=settings.free_turns_per_day)
        await _reply(query_or_message, text)
        return

    # Load active game
    game_row = await get_active_game(pool, player_id)
    if not game_row:
        text = get_text("free_text_no_game", lang)
        await _reply(query_or_message, text)
        return

    state = GameState.from_db_row(game_row)
    narrator = context.bot_data.get("narrator")

    # Process the turn
    result = await process_turn(
        state=state,
        action=action,
        target=target,
        pool=pool,
        narrator=narrator,
        language=lang,
        is_premium=is_premium,
    )

    # Build response
    response_parts = []

    # Narration
    response_parts.append(result.narration)

    # Delta summary
    if result.deltas:
        delta_line = " | ".join(
            f"{k}: {'+' if v > 0 else ''}{v}"
            for k, v in result.deltas.items()
            if k in ("population", "food", "scrap", "morale", "defense") and v != 0
        )
        if delta_line:
            response_parts.append(f"\n📊 {delta_line}")

    # Current resources
    s = result.new_state
    response_parts.append(
        f"\n👥{s.population} 🌾{s.food} 🔩{s.scrap} 😊{s.morale} 🛡{s.defense}"
        f"  (Week {s.turn_number}/50)"
    )

    text = "\n".join(response_parts)

    # Handle game outcome
    if result.outcome == "won":
        text += "\n\n" + get_text(
            "game_won", lang,
            settlement=s.settlement_name,
            population=s.population,
            morale=s.morale,
        )
    elif result.outcome == "lost":
        text += "\n\n" + get_text(
            "game_lost", lang,
            settlement=s.settlement_name,
        )

    # Always send as a new message so chat history stacks
    await _reply(query_or_message, text, reply_markup=_status_keyboard(lang), parse_mode="Markdown")


# ------------------------------------------------------------------
# /newgame command
# ------------------------------------------------------------------

async def handle_new_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Abandon current game and start fresh with full narrator onboarding."""
    pool = context.bot_data["db_pool"]
    user = update.effective_user
    player = await get_player_by_telegram_id(pool, user.id)
    if not player:
        await update.message.reply_text("Send /start first!")
        return

    lang = player.get("language", "en")
    player_id = str(player["id"])

    # Abandon current game if exists
    game_row = await get_active_game(pool, player_id)
    if game_row:
        await end_game(pool, str(game_row["id"]), "abandoned")

    # Create new game
    settlement = get_text(
        "settlement_default_name", lang,
        name=user.first_name or "Survivor",
    )
    game_row = await create_game(pool, player_id, settlement)
    state = GameState.from_db_row(game_row)
    await log_event(pool, player_id, "game_start", {"game_id": str(state.id)})

    # Message 1: narrator intro (atmospheric story, no buttons)
    narrator = context.bot_data.get("narrator")
    narration = None
    if narrator:
        try:
            narration = await narrator.generate_onboarding(
                settlement_name=settlement,
                language=lang,
                player_name=user.first_name or "Survivor",
            )
        except Exception:
            logger.exception("Narrator onboarding failed on new game")

    intro_text = narration or get_text(
        "welcome", lang,
        name=user.first_name or "Survivor",
        settlement=settlement,
    )
    await update.message.reply_text(intro_text, parse_mode="Markdown")

    # Message 2: tutorial guide + current status + status button
    guide = get_text("onboarding_guide", lang)
    status = _format_mini_status(state, lang)
    await update.message.reply_text(
        f"{guide}\n\n{status}",
        reply_markup=_status_keyboard(lang),
        parse_mode="Markdown",
    )



# ------------------------------------------------------------------
# Formatting helpers
# ------------------------------------------------------------------

def _format_full_status(state: GameState, lang: str) -> str:
    """Format a detailed settlement status message."""
    lines = [
        get_text("status_header", lang, settlement=state.settlement_name, turn=state.turn_number),
        "",
        get_text("status_resources", lang),
        f"  👥 Population: {state.population}",
        f"  🌾 Food: {state.food} {_bar(state.food, 200)}",
        f"  🔩 Scrap: {state.scrap}",
        f"  😊 Morale: {state.morale}/100 {_bar(state.morale, 100)}",
        f"  🛡 Defense: {state.defense}/100 {_bar(state.defense, 100)}",
        "",
        get_text("status_factions", lang),
        f"  ⚔️ Raiders: {get_faction_status(state.raiders_rep)} ({state.raiders_rep:+d})",
        f"  💰 Traders: {get_faction_status(state.traders_rep)} ({state.traders_rep:+d})",
        f"  📚 Remnants: {get_faction_status(state.remnants_rep)} ({state.remnants_rep:+d})",
    ]

    if state.buildings:
        lines.append("")
        lines.append(get_text("status_buildings", lang))
        for bname, count in state.buildings.items():
            if count > 0:
                lines.append(f"  {bname.title()} ×{count}")
    else:
        lines.append("")
        lines.append(get_text("status_no_buildings", lang))

    if state.food_zero_turns > 0:
        lines.append("")
        lines.append(f"⚠️ STARVATION: {state.food_zero_turns}/2 turns without food!")

    return "\n".join(lines)


def _bar(value: int, max_val: int, length: int = 10) -> str:
    """Render a simple text progress bar."""
    filled = max(0, min(length, round(value / max(max_val, 1) * length)))
    return "█" * filled + "░" * (length - filled)


def _status_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Single-button keyboard — status only. Actions happen via text."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("📊 " + get_text("action_status", lang), callback_data="cmd:status"),
    ]])


def _format_mini_status(state: GameState, lang: str) -> str:
    """Compact one-line resource bar."""
    return (
        f"👥{state.population} 🌾{state.food} 🔩{state.scrap} "
        f"😊{state.morale} 🛡{state.defense}  (Week {state.turn_number}/50)"
    )

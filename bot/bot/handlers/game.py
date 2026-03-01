"""Core game handlers — turns, status, callbacks, and action routing."""

from __future__ import annotations

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.config import settings
from bot.db.queries.players import get_player_by_telegram_id, check_and_consume_turn
from bot.db.queries.game_states import get_active_game, end_game, create_game
from bot.db.queries.analytics import log_event
from bot.engine.buildings import BUILDINGS
from bot.engine.factions import get_faction_status, FACTIONS
from bot.engine.game_state import GameState
from bot.engine.turn_processor import process_turn
from bot.i18n import get_text

logger = logging.getLogger(__name__)

VALID_ACTIONS = {"build", "explore", "trade", "defend", "diplomacy", "rest"}


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
        reply_markup=_action_keyboard(lang),
        parse_mode="Markdown",
    )


# ------------------------------------------------------------------
# Callback query handler — routes all button presses
# ------------------------------------------------------------------

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Dispatch inline keyboard button presses."""
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, query.from_user.id)
    if not player:
        await query.edit_message_text(get_text("free_text_no_game", "en"))
        return

    lang = player.get("language", "en")
    player_id = str(player["id"])

    # Route by prefix
    if data.startswith("turn:"):
        parts = data.split(":")
        action = parts[1] if len(parts) > 1 else ""
        target = parts[2] if len(parts) > 2 else None
        await _execute_turn(query, context, player, action, target)

    elif data.startswith("menu:build"):
        await _show_build_menu(query, context, player)

    elif data.startswith("menu:diplomacy"):
        await _show_diplomacy_menu(query, player)

    elif data == "cmd:status":
        game_row = await get_active_game(pool, player_id)
        if not game_row:
            await query.edit_message_text(get_text("free_text_no_game", lang))
            return
        state = GameState.from_db_row(game_row)
        await query.edit_message_text(
            _format_full_status(state, lang),
            reply_markup=_action_keyboard(lang),
            parse_mode="Markdown",
        )

    elif data == "menu:actions":
        await query.edit_message_text(
            get_text("status_resources", lang),
            reply_markup=_action_keyboard(lang),
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
        if hasattr(query_or_message, "edit_message_text"):
            await query_or_message.edit_message_text(text, reply_markup=_action_keyboard(lang))
        else:
            await query_or_message.reply_text(text, reply_markup=_action_keyboard(lang))
        return

    # Rate limit check
    can_play = await check_and_consume_turn(
        pool, player_id, is_premium, settings.free_turns_per_day,
    )
    if not can_play:
        text = get_text("turn_rate_limited", lang, max_turns=settings.free_turns_per_day)
        if hasattr(query_or_message, "edit_message_text"):
            await query_or_message.edit_message_text(text)
        else:
            await query_or_message.reply_text(text)
        return

    # Load active game
    game_row = await get_active_game(pool, player_id)
    if not game_row:
        text = get_text("free_text_no_game", lang)
        if hasattr(query_or_message, "edit_message_text"):
            await query_or_message.edit_message_text(text)
        else:
            await query_or_message.reply_text(text)
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
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 New Game", callback_data="cmd:newgame"),
        ]])
    elif result.outcome == "lost":
        text += "\n\n" + get_text(
            "game_lost", lang,
            settlement=s.settlement_name,
        )
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 New Game", callback_data="cmd:newgame"),
        ]])
    else:
        markup = _action_keyboard(lang)

    # Send response
    if hasattr(query_or_message, "edit_message_text"):
        await query_or_message.edit_message_text(
            text, reply_markup=markup, parse_mode="Markdown",
        )
    else:
        await query_or_message.reply_text(
            text, reply_markup=markup, parse_mode="Markdown",
        )


# ------------------------------------------------------------------
# /newgame command
# ------------------------------------------------------------------

async def handle_new_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Abandon current game and start fresh."""
    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, update.effective_user.id)
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
        name=update.effective_user.first_name or "Survivor",
    )
    game_row = await create_game(pool, player_id, settlement)
    state = GameState.from_db_row(game_row)

    await log_event(pool, player_id, "game_start", {"game_id": str(state.id)})

    text = get_text("new_game_abandoned", lang) + "\n\n"
    text += get_text(
        "welcome", lang,
        name=update.effective_user.first_name or "Survivor",
        settlement=settlement,
    )

    await update.message.reply_text(
        text,
        reply_markup=_action_keyboard(lang),
        parse_mode="Markdown",
    )


# ------------------------------------------------------------------
# Build menu
# ------------------------------------------------------------------

async def _show_build_menu(query, context, player: dict) -> None:
    """Show available buildings as inline buttons."""
    pool = context.bot_data["db_pool"]
    lang = player.get("language", "en")
    player_id = str(player["id"])

    buttons = []
    for bname, bdata in BUILDINGS.items():
        cost = bdata["cost"]
        max_count = bdata["max"]
        label = f"{bname.title()} ({cost}🔩, max {max_count})"
        buttons.append([InlineKeyboardButton(label, callback_data=f"turn:build:{bname}")])

    buttons.append([InlineKeyboardButton(
        get_text("action_back", lang), callback_data="menu:actions",
    )])

    await query.edit_message_text(
        get_text("build_menu_header", lang),
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown",
    )


# ------------------------------------------------------------------
# Diplomacy menu
# ------------------------------------------------------------------

async def _show_diplomacy_menu(query, player: dict) -> None:
    """Show faction diplomacy options."""
    lang = player.get("language", "en")
    buttons = []
    for fname, fdata in FACTIONS.items():
        label = fdata["name"].get(lang, fdata["name"]["en"])
        buttons.append([InlineKeyboardButton(
            f"🤝 {label}", callback_data=f"turn:diplomacy:{fname}",
        )])

    buttons.append([InlineKeyboardButton(
        get_text("action_back", lang), callback_data="menu:actions",
    )])

    await query.edit_message_text(
        "Choose a faction to negotiate with:",
        reply_markup=InlineKeyboardMarkup(buttons),
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


def _action_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Standard action buttons."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🏗 " + get_text("action_build", lang), callback_data="menu:build"),
            InlineKeyboardButton("🔍 " + get_text("action_explore", lang), callback_data="turn:explore"),
        ],
        [
            InlineKeyboardButton("💰 " + get_text("action_trade", lang), callback_data="turn:trade"),
            InlineKeyboardButton("🛡 " + get_text("action_defend", lang), callback_data="turn:defend"),
        ],
        [
            InlineKeyboardButton("🤝 " + get_text("action_diplomacy", lang), callback_data="menu:diplomacy"),
            InlineKeyboardButton("😴 " + get_text("action_rest", lang), callback_data="turn:rest"),
        ],
        [
            InlineKeyboardButton("📊 " + get_text("action_status", lang), callback_data="cmd:status"),
        ],
    ])

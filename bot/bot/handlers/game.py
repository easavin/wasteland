"""Core game handlers — turns, status, callbacks, and action routing."""

from __future__ import annotations

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from bot.config import settings
from bot.db.queries.players import get_player_by_telegram_id, check_and_consume_turn
from bot.db.queries.game_states import get_active_game, end_game, create_game
from bot.db.queries.analytics import log_event
from bot.engine.classes import PLAYER_CLASSES, get_starting_resources, get_starting_rep_overrides, get_starvation_threshold
from bot.engine.factions import get_faction_status
from bot.engine.game_state import GameState
from bot.engine.progression import xp_progress_in_level
from bot.engine.turn_processor import process_turn
from bot.handlers.payment import send_premium_invoice
from bot.i18n import get_text

logger = logging.getLogger(__name__)

VALID_ACTIONS = {"build", "explore", "trade", "defend", "diplomacy", "rest"}


async def _reply(query_or_message, text: str, **kwargs) -> None:
    """Always send a new reply message — never edit existing ones.

    Accepts either a Message or a CallbackQuery as the first argument.
    This keeps the chat history intact so narration accumulates as a log.
    If Markdown parsing fails, retries without parse_mode.
    """
    target = query_or_message.message if hasattr(query_or_message, "message") else query_or_message
    try:
        await target.reply_text(text, **kwargs)
    except BadRequest as e:
        if "parse entities" in str(e).lower() or "can't parse" in str(e).lower():
            logger.warning("Markdown parse failed, retrying without parse_mode: %s", e)
            kwargs.pop("parse_mode", None)
            await target.reply_text(text, **kwargs)
        else:
            raise


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

    # Route class selection to the start handler
    if data.startswith("class:"):
        from bot.handlers.start import handle_class_selection
        await handle_class_selection(update, context)
        return

    # Route class info / back to the start handler
    if data.startswith("info:") or data.startswith("class_info:"):
        from bot.handlers.start import handle_class_info
        await handle_class_info(update, context)
        return

    # Route skill upgrades to the skills handler
    if data.startswith("skill:"):
        from bot.handlers.skills import handle_skill_callback
        await handle_skill_callback(update, context)
        return

    # Route shop purchases to the shop handler
    if data.startswith("shop:"):
        from bot.handlers.shop import handle_shop_callback
        await handle_shop_callback(update, context)
        return

    # Route combat challenge accept/decline
    if data.startswith("challenge:"):
        from bot.handlers.combat import handle_challenge_callback
        await handle_challenge_callback(update, context)
        return

    # Route NPC minigame interactions
    if data.startswith("npc:"):
        from bot.handlers.npc_games import handle_npc_callback
        await handle_npc_callback(update, context)
        return

    # Route inventory equip/use callbacks
    if data.startswith("inv:"):
        from bot.handlers.inventory import handle_inventory_callback
        await handle_inventory_callback(update, context)
        return

    # Route exploration choices
    if data.startswith("explore:"):
        from bot.handlers.explore import handle_explore_callback
        await handle_explore_callback(update, context)
        return

    # Route codex navigation
    if data.startswith("codex:"):
        from bot.handlers.codex import handle_codex_callback
        await handle_codex_callback(update, context)
        return

    # Route daily missions claim
    if data.startswith("dispatch:"):
        from bot.handlers.dispatch import handle_dispatch_callback
        await handle_dispatch_callback(update, context)
        return

    # Route leaderboard category switching
    if data.startswith("top:"):
        from bot.handlers.leaderboard import handle_top_callback
        await handle_top_callback(update, context)
        return

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

    elif data == "cmd:premium":
        await send_premium_invoice(
            context.bot,
            query.message.chat_id,
            query.from_user.id,
            lang,
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
        text = get_text(
            "turn_rate_limited", lang,
            max_turns=settings.free_turns_per_day,
            price=settings.premium_price_stars,
        )
        await _reply(query_or_message, text, reply_markup=_premium_keyboard(lang), parse_mode="Markdown")
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
            if k in ("population", "food", "scrap", "morale", "defense", "gold") and v != 0
        )
        if delta_line:
            response_parts.append(f"\n📊 {delta_line}")

    # XP earned
    if result.xp_earned > 0:
        response_parts.append(f"✨ +{result.xp_earned} XP")

    # Level-up notifications
    if result.new_levels:
        for lvl in result.new_levels:
            response_parts.append(f"\n🎉 *LEVEL UP! You reached level {lvl}!*")

    # Item drop notification
    if result.dropped_item:
        from bot.engine.items import get_item_name, get_rarity_emoji, get_item
        item_spec = get_item(result.dropped_item)
        if item_spec:
            item_name = get_item_name(result.dropped_item, lang)
            rarity = item_spec["rarity"]
            emoji = get_rarity_emoji(rarity)
            response_parts.append(f"\n🎁 Found: {emoji} *{item_name}*")

    # Codex discovery notification
    if result.codex_entry:
        from bot.engine.codex import CODEX_ENTRIES, get_category_emoji
        ce = CODEX_ENTRIES.get(result.codex_entry, {})
        ce_name = ce.get("name", {}).get(lang, result.codex_entry)
        ce_emoji = get_category_emoji(ce.get("category", ""))
        response_parts.append(f"\n📖 Codex: {ce_emoji} *{ce_name}*")

    # Current resources
    s = result.new_state
    cls_info = PLAYER_CLASSES.get(s.player_class, {})
    cls_emoji = cls_info.get("emoji", "")
    xp_in, xp_needed = xp_progress_in_level(s)

    response_parts.append(
        f"\n{cls_emoji} L{s.level} ({xp_in}/{xp_needed} XP) | Zone {s.zone}"
        f"\n👥{s.population} 🌾{s.food} 🔩{s.scrap} 💰{s.gold}"
        f" 😊{s.morale} 🛡{s.defense}"
        f"  (Week {s.turn_number})"
    )

    text = "\n".join(response_parts)

    # Handle game outcome
    if result.outcome == "lost":
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
    """Abandon current game and start fresh with class selection."""
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
        await update.message.reply_text(get_text("new_game_abandoned", lang))

    # Present class selection — intro first, then the selection keyboard
    await update.message.reply_text(
        get_text("pre_class_intro", lang),
        parse_mode="Markdown",
    )
    await update.message.reply_text(
        get_text("class_selection", lang),
        reply_markup=_class_keyboard(lang),
        parse_mode="Markdown",
    )


# ------------------------------------------------------------------
# Formatting helpers
# ------------------------------------------------------------------

def _format_full_status(state: GameState, lang: str) -> str:
    """Format a detailed settlement status message."""
    cls_info = PLAYER_CLASSES.get(state.player_class, {})
    cls_emoji = cls_info.get("emoji", "")
    cls_name = cls_info.get("name", {}).get(lang, state.player_class.title() if state.player_class else "Unknown")
    xp_in, xp_needed = xp_progress_in_level(state)

    lines = [
        get_text("status_header_rpg", lang, settlement=state.settlement_name, turn=state.turn_number),
        f"{cls_emoji} *{cls_name}* — ⭐ Level {state.level} ({xp_in}/{xp_needed} XP)",
        f"🗺 Zone {state.zone}",
        "",
        get_text("status_resources", lang),
        f"  👥 Population: {state.population}",
        f"  🌾 Food: {state.food} {_bar(state.food, 200)}",
        f"  🔩 Scrap: {state.scrap}",
        f"  💰 Gold: {state.gold}",
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

    if state.skill_points > 0:
        lines.append("")
        lines.append(f"🔮 *{state.skill_points} skill point(s) available!* Use /skills")

    starvation_threshold = get_starvation_threshold(state.player_class)
    if state.food_zero_turns > 0:
        lines.append("")
        lines.append(f"⚠️ STARVATION: {state.food_zero_turns}/{starvation_threshold} turns without food!")

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


def _premium_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Keyboard shown when the daily turn limit is hit."""
    label = "⭐ Get Premium" if lang != "ru" else "⭐ Оформить Премиум"
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(label, callback_data="cmd:premium"),
    ]])


def _class_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Build a keyboard with one row per class: select button + ℹ️ info button."""
    from bot.engine.classes import PLAYER_CLASSES
    buttons = []
    for class_id, cls_info in PLAYER_CLASSES.items():
        emoji = cls_info["emoji"]
        name = cls_info["name"].get(lang, cls_info["name"]["en"])
        buttons.append([
            InlineKeyboardButton(
                f"{emoji} {name}",
                callback_data=f"class:{class_id}",
            ),
            InlineKeyboardButton(
                "ℹ️",
                callback_data=f"info:{class_id}",
            ),
        ])
    return InlineKeyboardMarkup(buttons)


def _format_mini_status(state: GameState, lang: str) -> str:
    """Compact one-line resource bar."""
    cls_info = PLAYER_CLASSES.get(state.player_class, {})
    cls_emoji = cls_info.get("emoji", "")
    xp_in, xp_needed = xp_progress_in_level(state)

    return (
        f"{cls_emoji} L{state.level} ({xp_in}/{xp_needed} XP)"
        f"\n👥{state.population} 🌾{state.food} 🔩{state.scrap} 💰{state.gold}"
        f" 😊{state.morale} 🛡{state.defense}  (Week {state.turn_number})"
    )

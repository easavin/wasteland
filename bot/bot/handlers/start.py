"""Handler for /start — player onboarding and game creation with class selection."""

from __future__ import annotations

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.db.queries.players import get_or_create_player, get_player_by_telegram_id
from bot.db.queries.game_states import create_game, get_active_game
from bot.db.queries.analytics import log_event
from bot.engine.classes import PLAYER_CLASSES, get_starting_resources, get_starting_rep_overrides
from bot.engine.game_state import GameState
from bot.engine.factions import get_faction_status
from bot.engine.progression import xp_progress_in_level
from bot.i18n import get_text

logger = logging.getLogger(__name__)


def _detect_language(user) -> str:
    code = getattr(user, "language_code", None) or ""
    return "ru" if code.startswith("ru") else "en"


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Create (or retrieve) a player and start a new game if needed."""
    user = update.effective_user
    pool = context.bot_data["db_pool"]
    lang = _detect_language(user)

    # Upsert player
    player = await get_or_create_player(
        pool,
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        language=lang,
    )
    player_id = str(player["id"])
    lang = player.get("language", lang)

    # Check for existing active game
    game_row = await get_active_game(pool, player_id)

    if game_row:
        # Welcome back — show status
        state = GameState.from_db_row(game_row)
        text = get_text(
            "welcome_back", lang,
            name=user.first_name or "Survivor",
            settlement=state.settlement_name,
            turn=state.turn_number,
        )
        text += "\n\n" + _format_mini_status(state, lang)
        await update.message.reply_text(
            text,
            reply_markup=_action_keyboard(lang),
            parse_mode="Markdown",
        )
        return

    # No active game — show storytelling intro, then class selection
    await log_event(pool, player_id, "bot_start", {})

    await update.message.reply_text(
        get_text("pre_class_intro", lang),
        parse_mode="Markdown",
    )
    await update.message.reply_text(
        get_text("class_selection", lang),
        reply_markup=_class_keyboard(lang),
        parse_mode="Markdown",
    )


async def handle_class_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard callback for class selection."""
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if not data.startswith("class:"):
        return

    class_id = data[6:]  # e.g. "class:scavenger" -> "scavenger"
    if class_id not in PLAYER_CLASSES:
        return

    pool = context.bot_data["db_pool"]
    user = query.from_user

    # Get player
    player = await get_player_by_telegram_id(pool, user.id)
    if not player:
        await query.message.reply_text("Send /start first!")
        return

    player_id = str(player["id"])
    lang = player.get("language", "en")

    # Check if they already have an active game (race condition guard)
    game_row = await get_active_game(pool, player_id)
    if game_row:
        state = GameState.from_db_row(game_row)
        await query.message.reply_text(
            get_text("welcome_back", lang,
                name=user.first_name or "Survivor",
                settlement=state.settlement_name,
                turn=state.turn_number,
            ),
        )
        return

    # Create game with class-specific starting resources
    settlement = get_text(
        "settlement_default_name", lang,
        name=user.first_name or "Survivor",
    )
    starting_resources = get_starting_resources(class_id)
    starting_rep = get_starting_rep_overrides(class_id)

    game_row = await create_game(
        pool, player_id, settlement,
        player_class=class_id,
        **starting_resources,
        **starting_rep,
    )
    state = GameState.from_db_row(game_row)

    await log_event(pool, player_id, "game_start", {
        "game_id": str(state.id),
        "class": class_id,
    })

    # Generate welcome with narrator if available
    cls_info = PLAYER_CLASSES[class_id]
    cls_name = cls_info["name"].get(lang, cls_info["name"]["en"])

    narrator = context.bot_data.get("narrator")
    if narrator:
        try:
            narration = await narrator.generate_onboarding(
                settlement_name=settlement,
                language=lang,
                player_name=user.first_name or "Survivor",
                player_class=class_id,
            )
        except Exception:
            logger.exception("Narrator onboarding failed")
            narration = None
    else:
        narration = None

    if narration:
        intro_text = narration
    else:
        intro_text = get_text(
            "welcome", lang,
            name=user.first_name or "Survivor",
            settlement=settlement,
        )

    # Add class info
    intro_text += f"\n\n{cls_info['emoji']} *{cls_name}*"

    # Message 1: atmospheric intro
    await query.message.reply_text(intro_text, parse_mode="Markdown")

    # Message 2: tutorial guide + current status + action keyboard
    guide = get_text("onboarding_guide", lang)
    status = _format_mini_status(state, lang)
    await query.message.reply_text(
        f"{guide}\n\n{status}",
        reply_markup=_action_keyboard(lang),
        parse_mode="Markdown",
    )


def _format_mini_status(state: GameState, lang: str) -> str:
    """Compact resource bar for inline display."""
    cls_info = PLAYER_CLASSES.get(state.player_class, {})
    cls_emoji = cls_info.get("emoji", "")
    cls_name = cls_info.get("name", {}).get(lang, state.player_class.title() if state.player_class else "Unknown")

    xp_in, xp_needed = xp_progress_in_level(state)

    lines = [
        get_text("status_header_rpg", lang,
                 settlement=state.settlement_name,
                 turn=state.turn_number),
        f"{cls_emoji} {cls_name} — ⭐ Level {state.level} ({xp_in}/{xp_needed} XP)",
        "",
        f"👥 {state.population}  🌾 {state.food}  🔩 {state.scrap}  💰 {state.gold}",
        f"😊 {state.morale}/100  🛡 {state.defense}/100",
        "",
        f"⚔️ {get_faction_status(state.raiders_rep)}  "
        f"💰 {get_faction_status(state.traders_rep)}  "
        f"📚 {get_faction_status(state.remnants_rep)}",
    ]

    if state.buildings:
        bldgs = ", ".join(f"{k}×{v}" for k, v in state.buildings.items() if v > 0)
        if bldgs:
            lines.append(f"🏗 {bldgs}")

    return "\n".join(lines)


def _class_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Build a keyboard with one row per class: select button + ℹ️ info button."""
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


async def handle_class_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show detailed stats/pros/cons for a class, with a back button."""
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    pool = context.bot_data["db_pool"]
    user = query.from_user
    player = await get_player_by_telegram_id(pool, user.id)
    lang = player.get("language", "en") if player else _detect_language(user)

    if data.startswith("info:"):
        class_id = data[5:]
        if class_id not in PLAYER_CLASSES:
            return
        text = get_text(f"class_info_{class_id}", lang)
        back_label = get_text("class_info_back", lang)
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(back_label, callback_data="class_info:back"),
        ]])
        await query.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")

    elif data == "class_info:back":
        await query.message.reply_text(
            get_text("class_selection", lang),
            reply_markup=_class_keyboard(lang),
            parse_mode="Markdown",
        )


def _action_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Status-only keyboard. Game actions happen via typed text messages."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("📊 " + get_text("action_status", lang), callback_data="cmd:status"),
    ]])

"""Handler for /start — player onboarding and game creation."""

from __future__ import annotations

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.db.queries.players import get_or_create_player
from bot.db.queries.game_states import create_game, get_active_game
from bot.db.queries.analytics import log_event
from bot.engine.game_state import GameState
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

    # Create new game
    settlement = get_text(
        "settlement_default_name", lang,
        name=user.first_name or "Survivor",
    )
    game_row = await create_game(pool, player_id, settlement)
    state = GameState.from_db_row(game_row)

    # Log analytics
    await log_event(pool, player_id, "bot_start", {})
    await log_event(pool, player_id, "game_start", {"game_id": str(state.id)})

    # Generate welcome with narrator if available
    narrator = context.bot_data.get("narrator")
    if narrator:
        try:
            narration = await narrator.generate_onboarding(
                settlement_name=settlement,
                language=lang,
                player_name=user.first_name or "Survivor",
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

    # Message 1: atmospheric intro — no buttons, just story
    await update.message.reply_text(intro_text, parse_mode="Markdown")

    # Message 2: tutorial guide + current status + action keyboard
    guide = get_text("onboarding_guide", lang)
    status = _format_mini_status(state, lang)
    await update.message.reply_text(
        f"{guide}\n\n{status}",
        reply_markup=_action_keyboard(lang),
        parse_mode="Markdown",
    )


def _format_mini_status(state: GameState, lang: str) -> str:
    """Compact resource bar for inline display."""
    from bot.engine.factions import get_faction_status

    lines = [
        get_text("status_header", lang, settlement=state.settlement_name, turn=state.turn_number),
        "",
        f"👥 {state.population}  🌾 {state.food}  🔩 {state.scrap}",
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


def _action_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Status-only keyboard. Game actions happen via typed text messages."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("📊 " + get_text("action_status", lang), callback_data="cmd:status"),
    ]])

"""Handler for /help and /language commands."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import settings
from bot.db.queries.players import get_player_by_telegram_id, update_player_language
from bot.i18n import get_text

logger = logging.getLogger(__name__)


async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, update.effective_user.id)
    lang = player.get("language", "en") if player else "en"

    await update.message.reply_text(
        get_text("help_text", lang, max_turns=settings.free_turns_per_day),
        parse_mode="Markdown",
    )


async def handle_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle language between en and ru."""
    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, update.effective_user.id)
    if not player:
        await update.message.reply_text("Send /start first!")
        return

    current = player.get("language", "en")
    new_lang = "ru" if current == "en" else "en"
    await update_player_language(pool, str(player["id"]), new_lang)

    label = "Russian 🇷🇺" if new_lang == "ru" else "English 🇬🇧"
    await update.message.reply_text(f"Language switched to {label}.")

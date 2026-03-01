"""Voice message handler — transcription and action routing."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.db.queries.players import get_player_by_telegram_id
from bot.db.queries.game_states import get_active_game
from bot.db.queries.analytics import log_event
from bot.handlers.game import _execute_turn
from bot.handlers.messages import _parse_keywords
from bot.i18n import get_text

logger = logging.getLogger(__name__)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Transcribe a voice message and route to game action."""
    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, update.effective_user.id)
    if not player:
        await update.message.reply_text(get_text("free_text_no_game", "en"))
        return

    lang = player.get("language", "en")
    player_id = str(player["id"])

    game_row = await get_active_game(pool, player_id)
    if not game_row:
        await update.message.reply_text(get_text("free_text_no_game", lang))
        return

    voice = update.message.voice
    if not voice:
        return

    # Download voice file
    try:
        voice_file = await context.bot.get_file(voice.file_id)
        file_bytes = await voice_file.download_as_bytearray()
    except Exception:
        logger.exception("Failed to download voice file")
        await update.message.reply_text(get_text("free_text_no_narrator", lang))
        return

    # Try transcription via narrator/Gemini
    narrator = context.bot_data.get("narrator")
    if narrator:
        try:
            result = await narrator.transcribe_voice(bytes(file_bytes), lang)
            if result and result.get("action"):
                # Log voice usage
                await log_event(pool, player_id, "voice_used", {
                    "transcription": result.get("transcription", ""),
                    "action": result["action"],
                })

                # Update comm profile from voice transcription
                profiler = context.bot_data.get("profiler")
                if profiler and result.get("transcription"):
                    try:
                        await profiler.analyze_and_update(
                            pool, player_id,
                            result["transcription"],
                            player.get("comm_profile", {}),
                        )
                    except Exception:
                        pass

                await update.message.reply_text(
                    f"🎤 _{result.get('transcription', '...')}_\n",
                    parse_mode="Markdown",
                )
                await _execute_turn(
                    update.message, context, player,
                    result["action"], result.get("target"),
                )
                return
        except Exception:
            logger.exception("Voice transcription failed")

    # Fallback — no narrator available
    await update.message.reply_text(get_text("free_text_no_narrator", lang))

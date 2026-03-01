"""Wasteland Chronicles Telegram Bot — Entry Point."""

import logging

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    CallbackQueryHandler,
    filters,
)

from bot.config import settings
from bot.db.pool import init_db_pool, close_db_pool
from bot.handlers import start, game, help as help_handler, payment, voice, messages
from bot.narrator.gemini_client import GeminiNarrator
from bot.narrator.profiler import PlayerProfiler
from bot.utils.logger import setup_logging

logger = logging.getLogger(__name__)


async def post_init(application) -> None:
    """Called after Application.initialize() — set up DB pool and narrator."""
    # Database
    pool = await init_db_pool(settings.database_url)
    application.bot_data["db_pool"] = pool

    # AI narrator (gracefully optional)
    if settings.gemini_api_key:
        try:
            profiler = PlayerProfiler()
            narrator = GeminiNarrator(profiler=profiler)
            application.bot_data["narrator"] = narrator
            application.bot_data["profiler"] = profiler
            logger.info("Gemini narrator initialized (model: %s)", settings.gemini_model)
        except Exception:
            logger.exception("Failed to initialize Gemini narrator — running without AI")
            application.bot_data["narrator"] = None
            application.bot_data["profiler"] = None
    else:
        logger.warning("No GEMINI_API_KEY set — running without AI narrator")
        application.bot_data["narrator"] = None
        application.bot_data["profiler"] = None


async def post_shutdown(application) -> None:
    """Called on shutdown — close DB pool."""
    pool = application.bot_data.get("db_pool")
    if pool:
        await close_db_pool(pool)


def main() -> None:
    setup_logging()
    logger.info("Starting Wasteland Chronicles bot...")

    app = (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .concurrent_updates(True)
        .build()
    )

    # --- Command handlers ---
    app.add_handler(CommandHandler("start", start.handle_start))
    app.add_handler(CommandHandler("help", help_handler.handle_help))
    app.add_handler(CommandHandler("status", game.handle_status))
    app.add_handler(CommandHandler("newgame", game.handle_new_game))
    app.add_handler(CommandHandler("premium", payment.handle_premium))
    app.add_handler(CommandHandler("language", help_handler.handle_language))

    # --- Callback queries (inline keyboard buttons) ---
    app.add_handler(CallbackQueryHandler(game.handle_callback))

    # --- Payment handlers ---
    app.add_handler(PreCheckoutQueryHandler(payment.handle_pre_checkout))
    app.add_handler(
        MessageHandler(filters.SUCCESSFUL_PAYMENT, payment.handle_successful_payment)
    )

    # --- Voice messages ---
    app.add_handler(MessageHandler(filters.VOICE, voice.handle_voice))

    # --- Free text messages (must be last) ---
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, messages.handle_free_text)
    )

    logger.info("Bot handlers registered. Starting polling...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

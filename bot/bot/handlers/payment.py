"""Payment handlers — Telegram Stars and premium management."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from telegram import Update, LabeledPrice
from telegram.ext import ContextTypes

from bot.config import settings
from bot.db.queries.players import get_player_by_telegram_id, update_player_premium
from bot.db.queries.payments import create_payment, complete_payment
from bot.db.queries.analytics import log_event
from bot.i18n import get_text

logger = logging.getLogger(__name__)


async def handle_premium(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show premium options or send invoice."""
    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, update.effective_user.id)
    if not player:
        await update.message.reply_text("Send /start first!")
        return

    lang = player.get("language", "en")

    # Check if already premium
    if player.get("is_premium") and player.get("premium_expires"):
        expires = player["premium_expires"]
        if isinstance(expires, datetime) and expires > datetime.now(timezone.utc):
            await update.message.reply_text(
                f"⭐ Premium active until {expires.strftime('%Y-%m-%d')}",
            )
            return

    # Send Stars invoice
    desc = (
        "30 days of unlimited turns and richer AI narration. "
        "Your settlement's story deepens."
    )
    if lang == "ru":
        desc = (
            "30 дней безлимитных ходов и более глубокого повествования ИИ. "
            "История вашего поселения углубляется."
        )

    await context.bot.send_invoice(
        chat_id=update.effective_chat.id,
        title="Wasteland Chronicles Premium",
        description=desc,
        payload=f"premium_{update.effective_user.id}_{settings.premium_duration_days}",
        provider_token="",  # Empty for Telegram Stars
        currency="XTR",
        prices=[LabeledPrice("Premium (30 days)", settings.premium_price_stars)],
    )

    await log_event(pool, str(player["id"]), "payment_started", {
        "method": "stars",
        "amount": settings.premium_price_stars,
    })


async def handle_pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Approve pre-checkout queries for Stars payments."""
    await update.pre_checkout_query.answer(ok=True)


async def handle_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process successful Stars payment — activate premium."""
    pool = context.bot_data["db_pool"]
    payment_info = update.message.successful_payment

    player = await get_player_by_telegram_id(pool, update.effective_user.id)
    if not player:
        logger.error("Payment received for unknown player: %s", update.effective_user.id)
        return

    player_id = str(player["id"])

    # Calculate premium expiry
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=settings.premium_duration_days)

    # If already premium, extend from current expiry
    if player.get("is_premium") and player.get("premium_expires"):
        current_expires = player["premium_expires"]
        if isinstance(current_expires, datetime) and current_expires > now:
            expires = current_expires + timedelta(days=settings.premium_duration_days)

    # Update player premium status
    await update_player_premium(pool, player_id, True, expires)

    # Record payment in DB
    payment_row = await create_payment(
        pool,
        player_id=player_id,
        payment_type="stars",
        amount=payment_info.total_amount,
        currency=payment_info.currency,
        stars_amount=payment_info.total_amount,
        premium_days=settings.premium_duration_days,
    )
    await complete_payment(
        pool,
        payment_id=str(payment_row["id"]),
        telegram_charge_id=payment_info.telegram_payment_charge_id,
        provider_charge_id=payment_info.provider_payment_charge_id,
    )

    # Log analytics
    await log_event(pool, player_id, "payment_completed", {
        "method": "stars",
        "amount": payment_info.total_amount,
        "premium_until": expires.isoformat(),
    })

    await update.message.reply_text(
        f"⭐ Premium activated until {expires.strftime('%Y-%m-%d')}!\n"
        "Unlimited turns and richer narration unlocked."
    )

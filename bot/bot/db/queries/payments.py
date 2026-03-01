"""Payment database queries."""

import logging
from decimal import Decimal

import asyncpg

logger = logging.getLogger(__name__)


async def create_payment(
    pool: asyncpg.Pool,
    player_id: str,
    payment_type: str,
    amount: Decimal | float,
    currency: str,
    stars_amount: int | None = None,
    premium_days: int = 30,
) -> dict:
    """Insert a new pending payment record and return it.

    Args:
        player_id: The player's UUID.
        payment_type: ``'stars'`` or ``'cryptopay'``.
        amount: Monetary amount (stored as ``DECIMAL(12,2)``).
        currency: ISO currency code, e.g. ``'XTR'``, ``'USDT'``.
        stars_amount: Number of Telegram Stars (only for ``stars`` payments).
        premium_days: Number of days of premium granted on completion.
    """
    row = await pool.fetchrow(
        """
        INSERT INTO payments (
            player_id, payment_type, amount, currency,
            stars_amount, premium_days
        ) VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING *
        """,
        player_id,
        payment_type,
        Decimal(str(amount)),
        currency,
        stars_amount,
        premium_days,
    )
    return dict(row)


async def complete_payment(
    pool: asyncpg.Pool,
    payment_id: str,
    telegram_charge_id: str | None = None,
    provider_charge_id: str | None = None,
) -> None:
    """Mark a payment as completed and record charge identifiers.

    Args:
        payment_id: The payment's UUID.
        telegram_charge_id: Telegram's internal charge ID (Stars payments).
        provider_charge_id: The payment provider's transaction ID.
    """
    await pool.execute(
        """
        UPDATE payments
           SET status              = 'completed',
               completed_at        = NOW(),
               telegram_charge_id  = COALESCE($1, telegram_charge_id),
               provider_charge_id  = COALESCE($2, provider_charge_id)
         WHERE id = $3
        """,
        telegram_charge_id,
        provider_charge_id,
        payment_id,
    )


async def get_player_payments(
    pool: asyncpg.Pool,
    player_id: str,
) -> list[dict]:
    """Return all payment records for *player_id*, newest first."""
    rows = await pool.fetch(
        """
        SELECT *
          FROM payments
         WHERE player_id = $1
         ORDER BY created_at DESC
        """,
        player_id,
    )
    return [dict(r) for r in rows]

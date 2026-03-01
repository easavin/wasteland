"""Player-related database queries."""

import json
import logging
from datetime import date

import asyncpg

logger = logging.getLogger(__name__)


async def get_or_create_player(
    pool: asyncpg.Pool,
    telegram_id: int,
    username: str | None,
    first_name: str | None,
    language: str = "en",
) -> dict:
    """Upsert a player row and return the full record as a dict.

    If the player already exists the ``username``, ``first_name``, and
    ``updated_at`` columns are refreshed.  The ``language`` is only set on
    first insert so that a returning player keeps their chosen language.
    """
    row = await pool.fetchrow(
        """
        INSERT INTO players (telegram_id, username, first_name, language)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (telegram_id) DO UPDATE
            SET username   = COALESCE(EXCLUDED.username, players.username),
                first_name = COALESCE(EXCLUDED.first_name, players.first_name),
                updated_at = NOW()
        RETURNING *
        """,
        telegram_id,
        username,
        first_name,
        language,
    )
    return dict(row)


async def get_player_by_telegram_id(
    pool: asyncpg.Pool,
    telegram_id: int,
) -> dict | None:
    """Fetch a single player by their Telegram user ID.

    Returns ``None`` when no matching row exists.
    """
    row = await pool.fetchrow(
        "SELECT * FROM players WHERE telegram_id = $1",
        telegram_id,
    )
    return dict(row) if row else None


async def update_player_language(
    pool: asyncpg.Pool,
    player_id: str,
    language: str,
) -> None:
    """Set the preferred language for a player."""
    await pool.execute(
        "UPDATE players SET language = $1, updated_at = NOW() WHERE id = $2",
        language,
        player_id,
    )


async def update_player_premium(
    pool: asyncpg.Pool,
    player_id: str,
    is_premium: bool,
    expires,
) -> None:
    """Update the premium status and expiry for a player.

    Args:
        player_id: The player's UUID (``players.id``).
        is_premium: Whether the player currently has premium.
        expires: ``datetime`` when premium expires, or ``None``.
    """
    await pool.execute(
        """
        UPDATE players
           SET is_premium      = $1,
               premium_expires = $2,
               updated_at      = NOW()
         WHERE id = $3
        """,
        is_premium,
        expires,
        player_id,
    )


async def update_comm_profile(
    pool: asyncpg.Pool,
    player_id: str,
    comm_profile: dict,
) -> None:
    """Replace the JSONB communication-style profile for a player."""
    await pool.execute(
        """
        UPDATE players
           SET comm_profile = $1::jsonb,
               updated_at  = NOW()
         WHERE id = $2
        """,
        json.dumps(comm_profile),
        player_id,
    )


async def check_and_consume_turn(
    pool: asyncpg.Pool,
    player_id: str,
    is_premium: bool,
    max_turns: int,
) -> bool:
    """Atomically check whether the player may take a turn and consume it.

    Turn counters are reset when ``last_turn_date`` is earlier than today.

    For premium players the function always succeeds (premium has no daily
    cap), but ``turns_today`` is still incremented for analytics.

    Returns:
        ``True`` if the turn was consumed (player may proceed).
        ``False`` if the daily limit has been reached.
    """
    today = date.today()

    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                SELECT turns_today, last_turn_date
                  FROM players
                 WHERE id = $1
                   FOR UPDATE
                """,
                player_id,
            )

            if row is None:
                return False

            turns_today = row["turns_today"]
            last_turn_date = row["last_turn_date"]

            # Reset counter on a new calendar day.
            if last_turn_date is None or last_turn_date < today:
                turns_today = 0

            # Premium players bypass the cap but still track usage.
            if not is_premium and turns_today >= max_turns:
                return False

            await conn.execute(
                """
                UPDATE players
                   SET turns_today   = $1,
                       last_turn_date = $2,
                       updated_at     = NOW()
                 WHERE id = $3
                """,
                turns_today + 1,
                today,
                player_id,
            )
            return True

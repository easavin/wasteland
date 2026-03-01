"""Combat challenge queries."""

from __future__ import annotations

import asyncpg


async def create_challenge(
    pool: asyncpg.Pool,
    challenger_game_id: str,
    defender_game_id: str,
    challenge_type: str = "siege",
) -> dict:
    """Create a combat challenge. Returns the challenge row."""
    row = await pool.fetchrow(
        """
        INSERT INTO combat_challenges (challenger_game_id, defender_game_id, challenge_type)
        VALUES ($1, $2, $3)
        RETURNING *
        """,
        challenger_game_id,
        defender_game_id,
        challenge_type,
    )
    return dict(row)


async def get_pending_challenge(
    pool: asyncpg.Pool,
    defender_game_id: str,
) -> dict | None:
    """Get a pending challenge for this defender."""
    row = await pool.fetchrow(
        """
        SELECT c.*, gs.display_name as challenger_name, gs.settlement_name as challenger_settlement
          FROM combat_challenges c
          JOIN game_states gs ON gs.id = c.challenger_game_id
         WHERE c.defender_game_id = $1 AND c.status = 'pending'
         ORDER BY c.created_at DESC
         LIMIT 1
        """,
        defender_game_id,
    )
    return dict(row) if row else None


async def accept_challenge(
    pool: asyncpg.Pool,
    challenge_id: str,
    defender_game_id: str,
) -> bool:
    """Mark challenge as accepted. Returns True if successful."""
    result = await pool.execute(
        """
        UPDATE combat_challenges SET status = 'accepted'
         WHERE id = $1 AND defender_game_id = $2 AND status = 'pending'
        """,
        challenge_id,
        defender_game_id,
    )
    return result == "UPDATE 1"


async def decline_challenge(
    pool: asyncpg.Pool,
    challenge_id: str,
    defender_game_id: str,
) -> bool:
    """Decline a challenge."""
    result = await pool.execute(
        """
        UPDATE combat_challenges SET status = 'declined'
         WHERE id = $1 AND defender_game_id = $2 AND status = 'pending'
        """,
        challenge_id,
        defender_game_id,
    )
    return result == "UPDATE 1"


async def resolve_challenge(
    pool: asyncpg.Pool,
    challenge_id: str,
    outcome: dict,
) -> None:
    """Mark challenge resolved with outcome JSON."""
    await pool.execute(
        """
        UPDATE combat_challenges SET status = 'resolved', resolved_at = NOW(), outcome = $1
         WHERE id = $2
        """,
        asyncpg.Json(outcome),
        challenge_id,
    )

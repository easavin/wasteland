"""Chat message queries."""

from __future__ import annotations

import asyncpg


async def insert_chat_message(
    pool: asyncpg.Pool,
    world_id: str,
    sender_game_id: str,
    player_id: str,
    text: str,
    *,
    zone: int | None = None,
    guild_id: str | None = None,
) -> dict:
    """Insert a chat message. Returns the inserted row."""
    row = await pool.fetchrow(
        """
        INSERT INTO chat_messages (world_id, zone, guild_id, sender_game_id, player_id, text)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING *
        """,
        world_id,
        zone,
        guild_id,
        sender_game_id,
        player_id,
        text[:2000],  # Limit length
    )
    return dict(row)


async def get_recent_chat(
    pool: asyncpg.Pool,
    world_id: str,
    *,
    zone: int | None = None,
    guild_id: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """Fetch recent chat messages with sender display info."""
    if guild_id:
        rows = await pool.fetch(
            """
            SELECT cm.*, gs.display_name, gs.settlement_name,
                   p.first_name, p.username
              FROM chat_messages cm
              JOIN game_states gs ON gs.id = cm.sender_game_id
              JOIN players p ON p.id = cm.player_id
             WHERE cm.guild_id = $1
             ORDER BY cm.created_at DESC
             LIMIT $2
            """,
            guild_id,
            limit,
        )
    elif zone is not None:
        rows = await pool.fetch(
            """
            SELECT cm.*, gs.display_name, gs.settlement_name,
                   p.first_name, p.username
              FROM chat_messages cm
              JOIN game_states gs ON gs.id = cm.sender_game_id
              JOIN players p ON p.id = cm.player_id
             WHERE cm.world_id = $1 AND cm.zone = $2
             ORDER BY cm.created_at DESC
             LIMIT $3
            """,
            world_id,
            zone,
            limit,
        )
    else:
        rows = await pool.fetch(
            """
            SELECT cm.*, gs.display_name, gs.settlement_name,
                   p.first_name, p.username
              FROM chat_messages cm
              JOIN game_states gs ON gs.id = cm.sender_game_id
              JOIN players p ON p.id = cm.player_id
             WHERE cm.world_id = $1 AND cm.zone IS NULL AND cm.guild_id IS NULL
             ORDER BY cm.created_at DESC
             LIMIT $2
            """,
            world_id,
            limit,
        )
    return [dict(r) for r in reversed(rows)]

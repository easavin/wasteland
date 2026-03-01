"""World/realm queries for shared multiplayer."""

from __future__ import annotations

import asyncpg


async def get_default_world(pool: asyncpg.Pool) -> dict | None:
    """Return the default world, or None if none exists."""
    row = await pool.fetchrow(
        "SELECT * FROM worlds WHERE is_default = TRUE LIMIT 1",
    )
    return dict(row) if row else None


async def get_world_by_id(pool: asyncpg.Pool, world_id: str) -> dict | None:
    """Return a world by ID, or None."""
    row = await pool.fetchrow(
        "SELECT * FROM worlds WHERE id = $1",
        world_id,
    )
    return dict(row) if row else None

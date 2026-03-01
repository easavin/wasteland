"""NPC-related database queries."""

from __future__ import annotations

import asyncpg


async def get_next_npc_telegram_id(pool: asyncpg.Pool) -> int:
    """Return the next negative telegram_id for a new NPC."""
    row = await pool.fetchrow(
        """
        SELECT COALESCE(MIN(telegram_id), 0) - 1 AS next_id
          FROM players
         WHERE telegram_id < 0
        """
    )
    return row["next_id"] if row else -1


async def create_npc(
    pool: asyncpg.Pool,
    *,
    display_name: str,
    settlement_name: str,
    world_id: str,
    zone: int = 1,
    population: int = 50,
    food: int = 100,
    scrap: int = 80,
    gold: int = 50,
) -> dict:
    """Create an NPC player and their game state. Returns the game_states row."""
    async with pool.acquire() as conn:
        async with conn.transaction():
            next_id = await conn.fetchval(
                """
                SELECT COALESCE(MIN(telegram_id), 0) - 1
                  FROM players WHERE telegram_id < 0
                """
            )
            telegram_id = next_id if next_id is not None else -1

            player = await conn.fetchrow(
                """
                INSERT INTO players (telegram_id, username, first_name, is_npc)
                VALUES ($1, $2, $3, TRUE)
                RETURNING *
                """,
                telegram_id,
                f"npc_{display_name.lower().replace(' ', '_')}"[:255],
                display_name[:255],
            )
            player_id = str(player["id"])

            game = await conn.fetchrow(
                """
                INSERT INTO game_states (
                    player_id, settlement_name, display_name, world_id, zone,
                    population, food, scrap, gold
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING *
                """,
                player_id,
                settlement_name,
                display_name,
                world_id,
                zone,
                population,
                food,
                scrap,
                gold,
            )
            return dict(game)


async def list_npcs_in_zone(
    pool: asyncpg.Pool,
    world_id: str,
    zone: int,
) -> list[dict]:
    """List NPCs in a world+zone for player discovery."""
    rows = await pool.fetch(
        """
        SELECT gs.id AS game_id, gs.display_name, gs.settlement_name,
               gs.population, gs.gold, p.id AS player_id
          FROM game_states gs
          JOIN players p ON p.id = gs.player_id
         WHERE gs.world_id = $1
           AND gs.zone = $2
           AND gs.status = 'active'
           AND p.is_npc = TRUE
         ORDER BY gs.display_name
        """,
        world_id,
        zone,
    )
    return [dict(r) for r in rows]


async def get_npc_by_game_id(pool: asyncpg.Pool, game_id: str) -> dict | None:
    """Get NPC player + game by game_states.id. Returns None if not an NPC."""
    row = await pool.fetchrow(
        """
        SELECT gs.*, p.id AS player_id, p.username, p.first_name
          FROM game_states gs
          JOIN players p ON p.id = gs.player_id
         WHERE gs.id = $1 AND gs.status = 'active' AND p.is_npc = TRUE
        """,
        game_id,
    )
    return dict(row) if row else None


async def list_npc_quests(pool: asyncpg.Pool, npc_player_id: str) -> list[dict]:
    """List active quests for an NPC."""
    rows = await pool.fetch(
        """
        SELECT * FROM npc_quests
         WHERE npc_player_id = $1 AND is_active = TRUE
         ORDER BY quest_key
        """,
        npc_player_id,
    )
    return [dict(r) for r in rows]


async def get_player_quest_progress(
    pool: asyncpg.Pool,
    player_id: str,
    quest_id: str,
) -> dict | None:
    """Get a player's progress on a specific quest."""
    row = await pool.fetchrow(
        """
        SELECT * FROM player_quest_progress
         WHERE player_id = $1 AND quest_id = $2
        """,
        player_id,
        quest_id,
    )
    return dict(row) if row else None


async def start_quest(
    pool: asyncpg.Pool,
    player_id: str,
    quest_id: str,
) -> bool:
    """Start a quest for a player. Returns False if already active/completed."""
    try:
        await pool.execute(
            """
            INSERT INTO player_quest_progress (player_id, quest_id, status)
            VALUES ($1, $2, 'active')
            ON CONFLICT (player_id, quest_id) DO NOTHING
            """,
            player_id,
            quest_id,
        )
        return True
    except Exception:
        return False


async def complete_quest(
    pool: asyncpg.Pool,
    player_id: str,
    quest_id: str,
) -> bool:
    """Mark a quest as completed."""
    result = await pool.execute(
        """
        UPDATE player_quest_progress
           SET status = 'completed', completed_at = NOW()
         WHERE player_id = $1 AND quest_id = $2 AND status = 'active'
        """,
        player_id,
        quest_id,
    )
    return result == "UPDATE 1"

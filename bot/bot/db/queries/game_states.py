"""Game-state database queries."""

import json
import logging

import asyncpg

logger = logging.getLogger(__name__)

# Columns that accept JSONB values and must be serialised before binding.
_JSONB_COLUMNS = frozenset({
    "buildings",
    "active_effects",
    "narrator_memory",
    "skills",
    "milestones",
    "inventory",
    "codex",
})

# All mutable columns on ``game_states`` that callers may pass to
# :func:`update_game_state`.  This whitelist prevents accidental writes to
# primary-key / foreign-key columns.
_UPDATABLE_COLUMNS = frozenset({
    "status",
    "turn_number",
    "settlement_name",
    "display_name",
    "player_class",
    "population",
    "food",
    "scrap",
    "morale",
    "defense",
    "gold",
    "food_zero_turns",
    "raiders_rep",
    "traders_rep",
    "remnants_rep",
    "style_aggression",
    "style_commerce",
    "style_exploration",
    "style_diplomacy",
    "buildings",
    "active_effects",
    "narrator_memory",
    "xp",
    "level",
    "skill_points",
    "skills",
    "milestones",
    "zone",
    "inventory",
    "codex",
    "ended_at",
})


async def create_game(
    pool: asyncpg.Pool,
    player_id: str,
    settlement_name: str,
    *,
    player_class: str = "",
    display_name: str | None = None,
    world_id: str | None = None,
    population: int = 50,
    food: int = 100,
    scrap: int = 80,
    morale: int = 70,
    defense: int = 30,
    gold: int = 0,
    raiders_rep: int = 0,
    traders_rep: int = 0,
    remnants_rep: int = 0,
) -> dict:
    """Insert a new game with (optionally overridden) starting values.

    The schema enforces a unique partial index so that a player may only have
    one ``active`` game at a time.  If an active game already exists the insert
    will raise :class:`asyncpg.UniqueViolationError`.
    """
    row = await pool.fetchrow(
        """
        INSERT INTO game_states (
            player_id, settlement_name, player_class,
            display_name, world_id,
            population, food, scrap, morale, defense, gold,
            raiders_rep, traders_rep, remnants_rep
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
        RETURNING *
        """,
        player_id,
        settlement_name,
        player_class,
        display_name,
        world_id,
        population,
        food,
        scrap,
        morale,
        defense,
        gold,
        raiders_rep,
        traders_rep,
        remnants_rep,
    )
    return dict(row)


async def get_active_game(
    pool: asyncpg.Pool,
    player_id: str,
) -> dict | None:
    """Return the currently active game for *player_id*, or ``None``."""
    row = await pool.fetchrow(
        """
        SELECT *
          FROM game_states
         WHERE player_id = $1
           AND status = 'active'
        """,
        player_id,
    )
    return dict(row) if row else None


async def update_game_state(
    pool: asyncpg.Pool,
    game_id: str,
    **kwargs,
) -> None:
    """Update arbitrary columns on a game_states row.

    Only columns listed in ``_UPDATABLE_COLUMNS`` are accepted; any unknown
    key raises :class:`ValueError`.  JSONB values are automatically serialised.

    Example::

        await update_game_state(pool, game_id, food=80, morale=55,
                                narrator_memory=[{"turn": 1, "note": "..."}])
    """
    if not kwargs:
        return

    unknown = set(kwargs) - _UPDATABLE_COLUMNS
    if unknown:
        raise ValueError(f"Cannot update unknown columns: {unknown}")

    # Build a dynamic SET clause with positional parameters.
    set_parts: list[str] = []
    values: list = []
    idx = 1

    for col, val in kwargs.items():
        if col in _JSONB_COLUMNS:
            set_parts.append(f"{col} = ${idx}::jsonb")
            values.append(json.dumps(val))
        else:
            set_parts.append(f"{col} = ${idx}")
            values.append(val)
        idx += 1

    # Always bump updated_at so the trigger fires consistently.
    set_parts.append(f"updated_at = NOW()")

    values.append(game_id)
    game_id_placeholder = f"${idx}"

    query = (
        f"UPDATE game_states SET {', '.join(set_parts)} "
        f"WHERE id = {game_id_placeholder}"
    )

    await pool.execute(query, *values)


async def get_settlement_by_id(
    pool: asyncpg.Pool,
    game_id: str,
) -> dict | None:
    """Return a game_states row by ID for cross-player lookups."""
    row = await pool.fetchrow(
        "SELECT * FROM game_states WHERE id = $1",
        game_id,
    )
    return dict(row) if row else None


async def get_settlements_in_zone(
    pool: asyncpg.Pool,
    world_id: str | None,
    zone: int,
) -> list[dict]:
    """Return active settlements in a world+zone for chat/broadcast."""
    if world_id:
        rows = await pool.fetch(
            """
            SELECT gs.*, p.telegram_id, p.username, p.first_name, p.is_npc
              FROM game_states gs
              JOIN players p ON p.id = gs.player_id
             WHERE gs.world_id = $1
               AND gs.zone = $2
               AND gs.status = 'active'
               AND p.telegram_id > 0
            """,
            world_id,
            zone,
        )
    else:
        rows = await pool.fetch(
            """
            SELECT gs.*, p.telegram_id, p.username, p.first_name, p.is_npc
              FROM game_states gs
              JOIN players p ON p.id = gs.player_id
             WHERE gs.zone = $1
               AND gs.status = 'active'
               AND p.telegram_id > 0
            """,
            zone,
        )
    return [dict(r) for r in rows]


async def get_settlements_in_world(
    pool: asyncpg.Pool,
    world_id: str,
) -> list[dict]:
    """Return all active settlements in a world (for global chat broadcast)."""
    rows = await pool.fetch(
        """
        SELECT gs.*, p.telegram_id, p.username, p.first_name, p.is_npc
          FROM game_states gs
          JOIN players p ON p.id = gs.player_id
         WHERE gs.world_id = $1
           AND gs.status = 'active'
           AND p.telegram_id > 0
        """,
        world_id,
    )
    return [dict(r) for r in rows]


async def end_game(
    pool: asyncpg.Pool,
    game_id: str,
    status: str,
) -> None:
    """Mark a game as finished.

    Args:
        game_id: The game's UUID.
        status: One of ``'won'``, ``'lost'``, or ``'abandoned'``.
    """
    if status not in ("won", "lost", "abandoned"):
        raise ValueError(f"Invalid end-game status: {status!r}")

    await pool.execute(
        """
        UPDATE game_states
           SET status     = $1,
               ended_at   = NOW(),
               updated_at = NOW()
         WHERE id = $2
        """,
        status,
        game_id,
    )

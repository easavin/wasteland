"""Guild queries for shared world."""

from __future__ import annotations

from datetime import datetime, timedelta

import asyncpg


async def get_guild_member_telegram_ids(
    pool: asyncpg.Pool,
    guild_id: str,
) -> list[int]:
    """Get telegram_ids of all guild members for broadcast."""
    rows = await pool.fetch(
        """
        SELECT p.telegram_id FROM guild_members gm
        JOIN game_states gs ON gs.id = gm.game_id
        JOIN players p ON p.id = gs.player_id
        WHERE gm.guild_id = $1 AND p.telegram_id > 0
        """,
        guild_id,
    )
    return [r["telegram_id"] for r in rows if r.get("telegram_id")]


async def get_guild_membership(
    pool: asyncpg.Pool,
    game_id: str,
) -> dict | None:
    """Return guild membership for a game, with guild name. None if not in a guild."""
    row = await pool.fetchrow(
        """
        SELECT gm.*, g.name as guild_name, g.leader_game_id, g.world_id
          FROM guild_members gm
          JOIN guilds g ON g.id = gm.guild_id
         WHERE gm.game_id = $1
        """,
        game_id,
    )
    if row:
        d = dict(row)
        d["guild_name"] = d.get("guild_name", "")
        return d
    return None


async def list_guild_members(
    pool: asyncpg.Pool,
    guild_id: str,
) -> list[dict]:
    """List all members of a guild with their telegram_id for broadcast."""
    rows = await pool.fetch(
        """
        SELECT gm.*, gs.display_name, gs.settlement_name, p.telegram_id, p.username, p.first_name
          FROM guild_members gm
          JOIN game_states gs ON gs.id = gm.game_id
          JOIN players p ON p.id = gs.player_id
         WHERE gm.guild_id = $1
         ORDER BY
             CASE gm.role WHEN 'leader' THEN 1 WHEN 'officer' THEN 2 ELSE 3 END,
             gm.joined_at
        """,
        guild_id,
    )
    return [dict(r) for r in rows]


async def create_guild(
    pool: asyncpg.Pool,
    world_id: str,
    name: str,
    leader_game_id: str,
) -> dict:
    """Create a guild and add the leader. Returns the guild row."""
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                INSERT INTO guilds (world_id, name, leader_game_id)
                VALUES ($1, $2, $3)
                RETURNING *
                """,
                world_id,
                name[:50],
                leader_game_id,
            )
            guild = dict(row)
            await conn.execute(
                """
                INSERT INTO guild_members (guild_id, game_id, role)
                VALUES ($1, $2, 'leader')
                """,
                guild["id"],
                leader_game_id,
            )
            return guild


async def get_guild_by_name(
    pool: asyncpg.Pool,
    world_id: str,
    name: str,
) -> dict | None:
    """Get a guild by world + name."""
    row = await pool.fetchrow(
        "SELECT * FROM guilds WHERE world_id = $1 AND LOWER(name) = LOWER($2)",
        world_id,
        name,
    )
    return dict(row) if row else None


async def get_pending_invite(
    pool: asyncpg.Pool,
    invitee_game_id: str,
) -> dict | None:
    """Get a pending guild invite for this game."""
    row = await pool.fetchrow(
        """
        SELECT gi.*, g.name as guild_name, gs.display_name as inviter_name
          FROM guild_invites gi
          JOIN guilds g ON g.id = gi.guild_id
          JOIN game_states gs ON gs.id = gi.inviter_game_id
         WHERE gi.invitee_game_id = $1
           AND gi.status = 'pending'
           AND gi.expires_at > NOW()
         ORDER BY gi.created_at DESC
         LIMIT 1
        """,
        invitee_game_id,
    )
    return dict(row) if row else None


async def create_invite(
    pool: asyncpg.Pool,
    guild_id: str,
    inviter_game_id: str,
    invitee_game_id: str,
    expires_hours: int = 24,
) -> dict:
    """Create a guild invite."""
    expires = datetime.utcnow() + timedelta(hours=expires_hours)
    row = await pool.fetchrow(
        """
        INSERT INTO guild_invites (guild_id, inviter_game_id, invitee_game_id, expires_at)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (guild_id, invitee_game_id) DO UPDATE
            SET inviter_game_id = EXCLUDED.inviter_game_id,
                status = 'pending',
                expires_at = EXCLUDED.expires_at
        RETURNING *
        """,
        guild_id,
        inviter_game_id,
        invitee_game_id,
        expires,
    )
    return dict(row)


async def accept_invite(pool: asyncpg.Pool, invite_id: str, invitee_game_id: str) -> bool:
    """Accept a guild invite. Returns True if successful."""
    async with pool.acquire() as conn:
        async with conn.transaction():
            inv = await conn.fetchrow(
                """
                SELECT * FROM guild_invites
                 WHERE id = $1 AND invitee_game_id = $2 AND status = 'pending' AND expires_at > NOW()
                 FOR UPDATE
                """,
                invite_id,
                invitee_game_id,
            )
            if not inv:
                return False
            await conn.execute(
                "UPDATE guild_invites SET status = 'accepted' WHERE id = $1",
                invite_id,
            )
            await conn.execute(
                """
                INSERT INTO guild_members (guild_id, game_id, role)
                VALUES ($1, $2, 'member')
                ON CONFLICT (game_id) DO NOTHING
                """,
                inv["guild_id"],
                invitee_game_id,
            )
            return True


async def decline_invite(pool: asyncpg.Pool, invite_id: str, invitee_game_id: str) -> bool:
    """Decline a guild invite."""
    result = await pool.execute(
        """
        UPDATE guild_invites SET status = 'declined'
         WHERE id = $1 AND invitee_game_id = $2 AND status = 'pending'
        """,
        invite_id,
        invitee_game_id,
    )
    return result == "UPDATE 1"


async def leave_guild(pool: asyncpg.Pool, game_id: str) -> tuple[bool, str | None]:
    """Leave current guild. Returns (success, message).
    If leader and guild has other members, must transfer first."""
    membership = await get_guild_membership(pool, game_id)
    if not membership:
        return (False, "not_in_guild")

    guild_id = str(membership["guild_id"])
    is_leader = str(membership["leader_game_id"]) == game_id
    members = await list_guild_members(pool, guild_id)

    if is_leader and len(members) > 1:
        return (False, "leader_must_transfer")

    await pool.execute(
        "DELETE FROM guild_members WHERE guild_id = $1 AND game_id = $2",
        guild_id,
        game_id,
    )
    if is_leader and len(members) == 1:
        await pool.execute("DELETE FROM guilds WHERE id = $1", guild_id)
    return (True, None)

"""NPC bonds database queries.

NPC bonds track the relationship level between a player and each NPC.
Bonds grow from minigame interactions and unlock perks at higher tiers.
"""

from __future__ import annotations

import logging
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)

# Bond tiers and their requirements
BOND_TIERS = {
    0: {"name": {"en": "Stranger", "ru": "Незнакомец"}, "min_xp": 0},
    1: {"name": {"en": "Acquaintance", "ru": "Знакомый"}, "min_xp": 50},
    2: {"name": {"en": "Ally", "ru": "Союзник"}, "min_xp": 150},
    3: {"name": {"en": "Trusted", "ru": "Доверенный"}, "min_xp": 350},
    4: {"name": {"en": "Bonded", "ru": "Связанный"}, "min_xp": 700},
    5: {"name": {"en": "Soulbound", "ru": "Духовная связь"}, "min_xp": 1200},
}


def get_bond_tier(bond_xp: int) -> int:
    """Return the tier level for a given bond XP amount."""
    tier = 0
    for t, info in BOND_TIERS.items():
        if bond_xp >= info["min_xp"]:
            tier = t
    return tier


def get_tier_name(tier: int, lang: str) -> str:
    """Return localised name for a bond tier."""
    info = BOND_TIERS.get(tier, BOND_TIERS[0])
    return info["name"].get(lang, info["name"]["en"])


async def get_bond(pool: asyncpg.Pool, player_id: str, npc_id: str) -> dict | None:
    """Get a player's bond with a specific NPC."""
    row = await pool.fetchrow(
        "SELECT * FROM npc_bonds WHERE player_id = $1 AND npc_id = $2",
        player_id, npc_id,
    )
    return dict(row) if row else None


async def get_all_bonds(pool: asyncpg.Pool, player_id: str) -> list[dict]:
    """Get all NPC bonds for a player."""
    rows = await pool.fetch(
        "SELECT * FROM npc_bonds WHERE player_id = $1 ORDER BY bond_xp DESC",
        player_id,
    )
    return [dict(r) for r in rows]


async def add_bond_xp(
    pool: asyncpg.Pool,
    player_id: str,
    npc_id: str,
    xp_amount: int,
) -> dict:
    """Add XP to an NPC bond (upsert). Returns the updated bond."""
    row = await pool.fetchrow(
        """
        INSERT INTO npc_bonds (player_id, npc_id, bond_xp, interactions)
        VALUES ($1, $2, $3, 1)
        ON CONFLICT (player_id, npc_id)
        DO UPDATE SET bond_xp = npc_bonds.bond_xp + $3,
                      interactions = npc_bonds.interactions + 1,
                      last_interaction = NOW()
        RETURNING *
        """,
        player_id, npc_id, xp_amount,
    )
    return dict(row)


async def get_bond_perks(pool: asyncpg.Pool, player_id: str) -> dict[str, Any]:
    """Calculate aggregate perks from all NPC bonds.

    Returns a dict of bonus keys, e.g.:
        {"trade_discount_pct": 5, "minigame_bonus_pct": 10, "defense_bonus": 2}
    """
    bonds = await get_all_bonds(pool, player_id)
    perks: dict[str, Any] = {}

    for bond in bonds:
        npc_id = str(bond["npc_id"])
        tier = get_bond_tier(bond["bond_xp"])

        if tier >= 1:
            # Tier 1: +5% minigame rewards
            perks["minigame_bonus_pct"] = perks.get("minigame_bonus_pct", 0) + 5

        if tier >= 2:
            # Tier 2: NPC-specific perk
            if "trader" in npc_id.lower() or npc_id == "old_trader":
                perks["trade_discount_pct"] = perks.get("trade_discount_pct", 0) + 5
            elif "doc" in npc_id.lower() or npc_id == "doc":
                perks["heal_bonus"] = perks.get("heal_bonus", 0) + 2
            elif "sentry" in npc_id.lower() or npc_id == "sentry":
                perks["defense_bonus"] = perks.get("defense_bonus", 0) + 2

        if tier >= 3:
            # Tier 3: +5% more minigame rewards
            perks["minigame_bonus_pct"] = perks.get("minigame_bonus_pct", 0) + 5

        if tier >= 4:
            # Tier 4: passive resource bonus
            perks["passive_scrap_per_turn"] = perks.get("passive_scrap_per_turn", 0) + 1

        if tier >= 5:
            # Tier 5: XP bonus
            perks["xp_bonus_pct"] = perks.get("xp_bonus_pct", 0) + 3

    return perks

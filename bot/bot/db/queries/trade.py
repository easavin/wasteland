"""Trade / marketplace queries."""

from __future__ import annotations

import asyncpg

VALID_RESOURCES = ("food", "scrap", "gold")


async def list_market_offers(
    pool: asyncpg.Pool,
    world_id: str,
    limit: int = 20,
) -> list[dict]:
    """List open marketplace offers (buyer_game_id is null)."""
    rows = await pool.fetch(
        """
        SELECT t.*, gs.display_name as seller_name, gs.settlement_name
          FROM trade_offers t
          JOIN game_states gs ON gs.id = t.seller_game_id
         WHERE t.world_id = $1 AND t.status = 'open' AND t.buyer_game_id IS NULL
         ORDER BY t.created_at DESC
         LIMIT $2
        """,
        world_id,
        limit,
    )
    return [dict(r) for r in rows]


async def create_offer(
    pool: asyncpg.Pool,
    world_id: str,
    seller_game_id: str,
    resource: str,
    amount: int,
    price_gold: int,
    buyer_game_id: str | None = None,
) -> dict:
    """Create a trade offer. Returns the offer row."""
    row = await pool.fetchrow(
        """
        INSERT INTO trade_offers (world_id, seller_game_id, resource, amount, price_gold, buyer_game_id)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING *
        """,
        world_id,
        seller_game_id,
        resource,
        amount,
        price_gold,
        buyer_game_id,
    )
    return dict(row)


async def get_offer(pool: asyncpg.Pool, offer_id: str) -> dict | None:
    """Get a trade offer by ID."""
    row = await pool.fetchrow(
        """
        SELECT t.*, gs.display_name as seller_name
          FROM trade_offers t
          JOIN game_states gs ON gs.id = t.seller_game_id
         WHERE t.id = $1
        """,
        offer_id,
    )
    return dict(row) if row else None


async def execute_trade(
    pool: asyncpg.Pool,
    offer_id: str,
    buyer_game_id: str,
) -> tuple[bool, str | None]:
    """Execute a trade (marketplace or direct). Returns (success, error_message)."""
    async with pool.acquire() as conn:
        async with conn.transaction():
            offer = await conn.fetchrow(
                """
                SELECT * FROM trade_offers
                 WHERE id = $1 AND status = 'open'
                 FOR UPDATE
                """,
                offer_id,
            )
            if not offer:
                return (False, "offer_not_found")
            if offer["buyer_game_id"] is not None and str(offer["buyer_game_id"]) != buyer_game_id:
                return (False, "offer_not_for_you")

            seller_id = str(offer["seller_game_id"])
            resource = offer["resource"]
            amount = int(offer["amount"])
            price = int(offer["price_gold"])

            if resource not in ("food", "scrap", "gold"):
                return (False, "invalid_resource")

            # Lock buyer and seller
            buyer_row = await conn.fetchrow(
                "SELECT * FROM game_states WHERE id = $1 FOR UPDATE",
                buyer_game_id,
            )
            seller_row = await conn.fetchrow(
                "SELECT * FROM game_states WHERE id = $1 FOR UPDATE",
                seller_id,
            )
            if not buyer_row or not seller_row:
                return (False, "game_not_found")

            buyer_gold = int(buyer_row["gold"])
            seller_resource = int(seller_row.get(resource, 0))

            if buyer_gold < price:
                return (False, "not_enough_gold")
            if seller_resource < amount:
                return (False, "seller_insufficient")

            # Buyer: pay gold, receive resource
            await conn.execute(
                f"""
                UPDATE game_states SET gold = gold - $1, {resource} = COALESCE({resource}, 0) + $2, updated_at = NOW()
                 WHERE id = $3
                """,
                price,
                amount,
                buyer_game_id,
            )
            # Seller: receive gold, give resource
            await conn.execute(
                f"""
                UPDATE game_states SET gold = gold + $1, {resource} = {resource} - $2, updated_at = NOW()
                 WHERE id = $3
                """,
                price,
                amount,
                seller_id,
            )

            await conn.execute(
                """
                UPDATE trade_offers SET status = 'completed', completed_at = NOW()
                 WHERE id = $1
                """,
                offer_id,
            )
            return (True, None)


async def cancel_offer(
    pool: asyncpg.Pool,
    offer_id: str,
    game_id: str,
) -> bool:
    """Cancel own offer. Returns True if cancelled."""
    result = await pool.execute(
        """
        UPDATE trade_offers SET status = 'cancelled'
         WHERE id = $1 AND seller_game_id = $2 AND status = 'open'
        """,
        offer_id,
        game_id,
    )
    return result == "UPDATE 1"

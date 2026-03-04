"""Comeback notification job — sends messages to inactive players.

Uses python-telegram-bot's JobQueue to periodically check for players
who haven't played in a while and sends them a personalized nudge.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Comeback tiers — each has a different delay and reward
COMEBACK_TIERS = [
    {"days": 1, "tier": 0, "reward_scrap": 20, "reward_food": 15},
    {"days": 3, "tier": 1, "reward_scrap": 40, "reward_food": 30, "reward_gold": 5},
    {"days": 7, "tier": 2, "reward_scrap": 80, "reward_food": 50, "reward_gold": 15},
]


async def check_comeback_players(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Periodic job: find inactive players and send comeback notifications.

    Runs once per hour. Checks for players who haven't been active for
    1, 3, or 7 days and sends them escalating comeback messages.
    """
    pool = context.bot_data.get("db_pool")
    if not pool:
        return

    now = datetime.now(timezone.utc)

    for tier_config in COMEBACK_TIERS:
        days = tier_config["days"]
        tier = tier_config["tier"]
        cutoff = now - timedelta(days=days)
        # Also set an upper bound so we don't re-send to the same tier
        upper = now - timedelta(days=days - 0.5)  # half-day window

        try:
            rows = await pool.fetch(
                """
                SELECT p.telegram_id, p.language, p.comeback_tier,
                       gs.settlement_name, gs.display_name, gs.level
                  FROM players p
                  JOIN game_states gs ON gs.player_id = p.id AND gs.status = 'active'
                 WHERE p.last_active_at < $1
                   AND p.last_active_at > $2
                   AND p.comeback_tier <= $3
                   AND p.telegram_id > 0
                   AND p.is_banned = FALSE
                 LIMIT 50
                """,
                cutoff, upper, tier,
            )
        except Exception:
            logger.exception("Failed to query comeback players for tier %d", tier)
            continue

        for row in rows:
            tg_id = row["telegram_id"]
            lang = row.get("language", "en")
            name = row.get("display_name") or row.get("settlement_name") or "Survivor"
            level = row.get("level", 1)

            # Build reward description
            reward_parts = []
            if tier_config.get("reward_scrap"):
                reward_parts.append(f"🔩 +{tier_config['reward_scrap']}")
            if tier_config.get("reward_food"):
                reward_parts.append(f"🌾 +{tier_config['reward_food']}")
            if tier_config.get("reward_gold"):
                reward_parts.append(f"💰 +{tier_config['reward_gold']}")
            reward_str = " | ".join(reward_parts)

            if lang == "ru":
                text = (
                    f"🏚 *{name}*, твоё поселение ждёт!\n\n"
                    f"Ты не заходил(а) уже {days} дн.\n"
                    f"Возвращайся и получи бонус:\n{reward_str}\n\n"
                    f"Твой уровень: {level}. Пустошь не ждёт!"
                )
            else:
                text = (
                    f"🏚 *{name}*, your settlement awaits!\n\n"
                    f"You haven't played in {days} day(s).\n"
                    f"Come back and claim your bonus:\n{reward_str}\n\n"
                    f"Your level: {level}. The wasteland won't wait!"
                )

            try:
                await context.bot.send_message(
                    chat_id=tg_id,
                    text=text,
                    parse_mode="Markdown",
                )
                # Update comeback tier so we don't resend
                await pool.execute(
                    "UPDATE players SET comeback_tier = $1, updated_at = NOW() WHERE telegram_id = $2",
                    tier + 1, tg_id,
                )
                logger.info("Sent comeback notification to %d (tier %d)", tg_id, tier)
            except Exception:
                logger.debug("Could not send comeback to %d", tg_id)


async def apply_comeback_reward(pool, player_id: str, days_away: int) -> dict[str, int] | None:
    """Apply comeback reward to a returning player.

    Called when a player returns after inactivity. Returns the reward dict,
    or None if no reward applies.
    """
    # Find the highest applicable tier
    applicable = None
    for tier_config in reversed(COMEBACK_TIERS):
        if days_away >= tier_config["days"]:
            applicable = tier_config
            break

    if applicable is None:
        return None

    rewards: dict[str, int] = {}
    if applicable.get("reward_scrap"):
        rewards["scrap"] = applicable["reward_scrap"]
    if applicable.get("reward_food"):
        rewards["food"] = applicable["reward_food"]
    if applicable.get("reward_gold"):
        rewards["gold"] = applicable["reward_gold"]

    # Apply to game state
    game = await pool.fetchrow(
        "SELECT id FROM game_states WHERE player_id = $1 AND status = 'active'",
        player_id,
    )
    if game:
        set_parts = []
        values = []
        idx = 1
        for key, val in rewards.items():
            set_parts.append(f"{key} = {key} + ${idx}")
            values.append(val)
            idx += 1
        values.append(str(game["id"]))

        if set_parts:
            query = f"UPDATE game_states SET {', '.join(set_parts)}, updated_at = NOW() WHERE id = ${idx}"
            await pool.execute(query, *values)

    # Reset comeback tier
    await pool.execute(
        "UPDATE players SET comeback_tier = 0, updated_at = NOW() WHERE id = $1",
        player_id,
    )

    return rewards

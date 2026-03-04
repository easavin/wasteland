"""Idle/offline reward calculator.

When a player returns after being away, they receive passive rewards
based on their buildings, equipped items, and how long they were offline.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Maximum hours of idle rewards (caps at 8 hours)
MAX_IDLE_HOURS = 8

# Minimum minutes of absence before idle rewards trigger
MIN_IDLE_MINUTES = 30

# Base idle rates (per hour, before bonuses)
_BASE_IDLE_RATES: dict[str, float] = {
    "food": 2.0,
    "scrap": 1.5,
    "gold": 0.5,
}

# Building bonuses to idle rates (per building level)
_BUILDING_IDLE_BONUSES: dict[str, dict[str, float]] = {
    "farm": {"food": 1.0},
    "workshop": {"scrap": 0.8},
    "market": {"gold": 0.3},
    "vault": {"gold": 0.2},
    "shelter": {"food": 0.5},
}


def calculate_idle_rewards(
    buildings: dict[str, int],
    equipped_bonuses: dict[str, Any],
    last_active_at: datetime | None,
    now: datetime | None = None,
) -> dict[str, int] | None:
    """Calculate idle rewards based on time away.

    Parameters
    ----------
    buildings:
        Player's building dict (name -> count).
    equipped_bonuses:
        Aggregated passive bonuses from equipped items.
    last_active_at:
        When the player was last active (timezone-aware datetime).
    now:
        Current time (defaults to utcnow).

    Returns
    -------
    dict or None:
        Resource rewards dict, or None if too little time has passed.
    """
    if last_active_at is None:
        return None

    if now is None:
        now = datetime.now(timezone.utc)

    # Ensure timezone-aware comparison
    if last_active_at.tzinfo is None:
        last_active_at = last_active_at.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    elapsed = now - last_active_at
    elapsed_minutes = elapsed.total_seconds() / 60.0

    if elapsed_minutes < MIN_IDLE_MINUTES:
        return None

    # Cap at MAX_IDLE_HOURS
    hours = min(elapsed_minutes / 60.0, MAX_IDLE_HOURS)

    # Calculate rates
    rates = dict(_BASE_IDLE_RATES)

    # Building bonuses
    for bname, count in buildings.items():
        bonuses = _BUILDING_IDLE_BONUSES.get(bname)
        if bonuses and count > 0:
            for resource, rate_per_level in bonuses.items():
                rates[resource] = rates.get(resource, 0) + rate_per_level * count

    # Equipped item bonuses (per-turn bonuses give partial idle benefit)
    if equipped_bonuses:
        for key, val in equipped_bonuses.items():
            if key == "food_per_turn":
                rates["food"] += val * 0.3
            elif key == "scrap_per_turn":
                rates["scrap"] += val * 0.3
            elif key == "gold_per_turn":
                rates["gold"] += val * 0.3
            elif key == "all_per_turn":
                rates["food"] += val * 0.2
                rates["scrap"] += val * 0.2
                rates["gold"] += val * 0.2

    # Calculate final rewards
    rewards: dict[str, int] = {}
    for resource, rate in rates.items():
        amount = int(rate * hours)
        if amount > 0:
            rewards[resource] = amount

    return rewards if rewards else None


def format_idle_rewards(rewards: dict[str, int], hours: float, lang: str) -> str:
    """Format idle rewards as a display string."""
    emoji_map = {"food": "🌾", "scrap": "🔩", "gold": "💰"}

    hours_display = f"{hours:.1f}" if hours < 1 else str(int(hours))

    if lang == "ru":
        header = f"💤 *Пока тебя не было ({hours_display}ч):*"
    else:
        header = f"💤 *While you were away ({hours_display}h):*"

    parts = [header]
    for resource, amount in rewards.items():
        emoji = emoji_map.get(resource, "")
        parts.append(f"  {emoji} +{amount} {resource}")

    return "\n".join(parts)

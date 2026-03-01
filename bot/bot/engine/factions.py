"""Faction definitions, reputation tracking, and status labels."""

from __future__ import annotations

from math import ceil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot.engine.game_state import GameState


# ---------------------------------------------------------------------------
# Faction catalog
# ---------------------------------------------------------------------------

FACTIONS: dict[str, dict] = {
    "raiders": {
        "name": {"en": "Raiders", "ru": "Рейдеры"},
        "description": {
            "en": (
                "Ruthless scavengers who respect only strength.  "
                "Hostile by default, but can be pacified through shows of force "
                "or bribed into temporary truces."
            ),
            "ru": (
                "Беспощадные мародёры, уважающие только силу.  "
                "Враждебны по умолчанию, но могут быть умиротворены."
            ),
        },
        "rep_field": "raiders_rep",
    },
    "traders": {
        "name": {"en": "Traders", "ru": "Торговцы"},
        "description": {
            "en": (
                "Nomadic merchants who deal in food, tech, and information.  "
                "Building a good relationship unlocks better trade deals."
            ),
            "ru": (
                "Кочевые торговцы, торгующие едой, технологиями и информацией.  "
                "Хорошие отношения открывают лучшие сделки."
            ),
        },
        "rep_field": "traders_rep",
    },
    "remnants": {
        "name": {"en": "Remnants", "ru": "Остатки"},
        "description": {
            "en": (
                "Survivors of the old world who hoard pre-Collapse knowledge.  "
                "Cautious and secretive, they reward explorers and diplomats."
            ),
            "ru": (
                "Выжившие старого мира, хранящие знания.  "
                "Осторожны и скрытны, но ценят исследователей и дипломатов."
            ),
        },
        "rep_field": "remnants_rep",
    },
}


# ---------------------------------------------------------------------------
# Reputation helpers
# ---------------------------------------------------------------------------


def update_faction_rep(
    state: GameState,
    action: str,
    target: str | None,
) -> dict[str, int]:
    """Compute faction reputation changes for a given action.

    Returns a dict with keys like ``"raiders_rep"``, ``"traders_rep"``,
    ``"remnants_rep"`` whose values are signed integers to be added to
    current reputations.

    Diplomat class passive ("silver_tongue"): all *positive* rep gains are
    multiplied by 1.5 (rounded up).
    """
    changes: dict[str, int] = {
        "raiders_rep": 0,
        "traders_rep": 0,
        "remnants_rep": 0,
    }

    if action == "trade":
        changes["traders_rep"] += 5

    elif action == "defend":
        # Standing strong displeases raiders, earns remnant respect.
        changes["raiders_rep"] -= 5
        changes["remnants_rep"] += 3

    elif action == "diplomacy":
        # Targeted diplomacy: big boost to one faction, small penalty to others.
        if target in FACTIONS:
            rep_key = FACTIONS[target]["rep_field"]
            changes[rep_key] += 10
            for faction_id, faction_info in FACTIONS.items():
                if faction_id != target:
                    changes[faction_info["rep_field"]] -= 3
        else:
            # Generic diplomacy -- mild positive across the board.
            changes["traders_rep"] += 2
            changes["remnants_rep"] += 2

    elif action == "explore":
        # Explorers earn the respect of the knowledge-hoarding Remnants.
        changes["remnants_rep"] += 2

    elif action == "raid":
        # Military / raiding actions.
        changes["raiders_rep"] += 5
        changes["traders_rep"] -= 3
        changes["remnants_rep"] -= 5

    # Diplomat passive: +50% to all positive rep gains.
    if state.player_class == "diplomat":
        for key, val in changes.items():
            if val > 0:
                changes[key] = ceil(val * 1.5)

    return changes


def get_faction_status(rep: int) -> str:
    """Translate a numeric reputation into a human-readable status label.

    Thresholds
    ----------
    * ``rep > 50``   -> ``"allied"``
    * ``20 < rep <= 50`` -> ``"friendly"``
    * ``-20 <= rep <= 20`` -> ``"neutral"``
    * ``-50 <= rep < -20`` -> ``"unfriendly"``
    * ``rep < -50``  -> ``"hostile"``
    """
    if rep > 50:
        return "allied"
    if rep > 20:
        return "friendly"
    if rep >= -20:
        return "neutral"
    if rep >= -50:
        return "unfriendly"
    return "hostile"

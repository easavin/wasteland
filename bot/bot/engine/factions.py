"""Faction definitions, reputation tracking, and status labels."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot.engine.game_state import GameState


# ---------------------------------------------------------------------------
# Faction catalog
# ---------------------------------------------------------------------------

FACTIONS: dict[str, dict] = {
    "raiders": {
        "name": {"en": "Raiders", "ru": "\u0420\u0435\u0439\u0434\u0435\u0440\u044b"},
        "description": {
            "en": (
                "Ruthless scavengers who respect only strength.  "
                "Hostile by default, but can be pacified through shows of force "
                "or bribed into temporary truces."
            ),
            "ru": (
                "\u0411\u0435\u0441\u043f\u043e\u0449\u0430\u0434\u043d\u044b\u0435 \u043c\u0430\u0440\u043e\u0434\u0451\u0440\u044b, \u0443\u0432\u0430\u0436\u0430\u044e\u0449\u0438\u0435 \u0442\u043e\u043b\u044c\u043a\u043e \u0441\u0438\u043b\u0443.  "
                "\u0412\u0440\u0430\u0436\u0434\u0435\u0431\u043d\u044b \u043f\u043e \u0443\u043c\u043e\u043b\u0447\u0430\u043d\u0438\u044e, \u043d\u043e \u043c\u043e\u0433\u0443\u0442 \u0431\u044b\u0442\u044c \u0443\u043c\u0438\u0440\u043e\u0442\u0432\u043e\u0440\u0435\u043d\u044b."
            ),
        },
        "rep_field": "raiders_rep",
    },
    "traders": {
        "name": {"en": "Traders", "ru": "\u0422\u043e\u0440\u0433\u043e\u0432\u0446\u044b"},
        "description": {
            "en": (
                "Nomadic merchants who deal in food, tech, and information.  "
                "Building a good relationship unlocks better trade deals."
            ),
            "ru": (
                "\u041a\u043e\u0447\u0435\u0432\u044b\u0435 \u0442\u043e\u0440\u0433\u043e\u0432\u0446\u044b, \u0442\u043e\u0440\u0433\u0443\u044e\u0449\u0438\u0435 \u0435\u0434\u043e\u0439, \u0442\u0435\u0445\u043d\u043e\u043b\u043e\u0433\u0438\u044f\u043c\u0438 \u0438 \u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u0435\u0439.  "
                "\u0425\u043e\u0440\u043e\u0448\u0438\u0435 \u043e\u0442\u043d\u043e\u0448\u0435\u043d\u0438\u044f \u043e\u0442\u043a\u0440\u044b\u0432\u0430\u044e\u0442 \u043b\u0443\u0447\u0448\u0438\u0435 \u0441\u0434\u0435\u043b\u043a\u0438."
            ),
        },
        "rep_field": "traders_rep",
    },
    "remnants": {
        "name": {"en": "Remnants", "ru": "\u041e\u0441\u0442\u0430\u0442\u043a\u0438"},
        "description": {
            "en": (
                "Survivors of the old world who hoard pre-Collapse knowledge.  "
                "Cautious and secretive, they reward explorers and diplomats."
            ),
            "ru": (
                "\u0412\u044b\u0436\u0438\u0432\u0448\u0438\u0435 \u0441\u0442\u0430\u0440\u043e\u0433\u043e \u043c\u0438\u0440\u0430, \u0445\u0440\u0430\u043d\u044f\u0449\u0438\u0435 \u0437\u043d\u0430\u043d\u0438\u044f.  "
                "\u041e\u0441\u0442\u043e\u0440\u043e\u0436\u043d\u044b \u0438 \u0441\u043a\u0440\u044b\u0442\u043d\u044b, \u043d\u043e \u0446\u0435\u043d\u044f\u0442 \u0438\u0441\u0441\u043b\u0435\u0434\u043e\u0432\u0430\u0442\u0435\u043b\u0435\u0439 \u0438 \u0434\u0438\u043f\u043b\u043e\u043c\u0430\u0442\u043e\u0432."
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

"""Building catalog, validation, construction, and per-turn effect calculation."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot.engine.game_state import GameState


# ---------------------------------------------------------------------------
# Building catalog
# ---------------------------------------------------------------------------
# Each entry defines:
#   cost        - scrap required to construct
#   effects     - dict of per-turn resource deltas while the building stands
#   max_count   - maximum number of this building a settlement may have
#   description - flavour text (kept in both languages for tooltips)
# ---------------------------------------------------------------------------

BUILDINGS: dict[str, dict] = {
    "farm": {
        "cost": 30,
        "effects": {"food": 15},
        "max_count": 5,
        "description": {
            "en": "Irrigated plots that yield food each turn.",
            "ru": "\u041e\u0440\u043e\u0448\u0430\u0435\u043c\u044b\u0435 \u0443\u0447\u0430\u0441\u0442\u043a\u0438, \u0434\u0430\u044e\u0449\u0438\u0435 \u0435\u0434\u0443 \u043a\u0430\u0436\u0434\u044b\u0439 \u0445\u043e\u0434.",
        },
    },
    "watchtower": {
        "cost": 25,
        "effects": {"defense": 5},
        "max_count": 4,
        "description": {
            "en": "A vantage point that strengthens settlement defense.",
            "ru": "\u041d\u0430\u0431\u043b\u044e\u0434\u0430\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0431\u0430\u0448\u043d\u044f, \u0443\u043a\u0440\u0435\u043f\u043b\u044f\u044e\u0449\u0430\u044f \u043e\u0431\u043e\u0440\u043e\u043d\u0443.",
        },
    },
    "workshop": {
        "cost": 40,
        "effects": {"scrap": 10},
        "max_count": 3,
        "description": {
            "en": "Salvagers refine junk into usable scrap each turn.",
            "ru": "\u041c\u0430\u0441\u0442\u0435\u0440\u0441\u043a\u0430\u044f, \u043f\u0435\u0440\u0435\u0440\u0430\u0431\u0430\u0442\u044b\u0432\u0430\u044e\u0449\u0430\u044f \u043c\u0443\u0441\u043e\u0440 \u0432 \u043f\u043e\u043b\u0435\u0437\u043d\u044b\u0439 \u0445\u043b\u0430\u043c.",
        },
    },
    "barracks": {
        "cost": 35,
        "effects": {"defense": 3},
        "max_count": 2,
        "description": {
            "en": "Military quarters that boost defense and allow more settlers.",
            "ru": "\u041a\u0430\u0437\u0430\u0440\u043c\u044b: \u0443\u043b\u0443\u0447\u0448\u0430\u044e\u0442 \u043e\u0431\u043e\u0440\u043e\u043d\u0443 \u0438 \u0432\u043c\u0435\u0441\u0442\u0438\u043c\u043e\u0441\u0442\u044c.",
        },
    },
    "shelter": {
        "cost": 20,
        "effects": {"morale": 2},
        "max_count": 4,
        "description": {
            "en": "Basic housing that improves morale.",
            "ru": "\u0423\u043a\u0440\u044b\u0442\u0438\u0435, \u043f\u043e\u0432\u044b\u0448\u0430\u044e\u0449\u0435\u0435 \u043c\u043e\u0440\u0430\u043b\u044c.",
        },
    },
    "clinic": {
        "cost": 45,
        "effects": {"morale": 3},
        "max_count": 2,
        "description": {
            "en": "Medical facility that improves morale and population growth.",
            "ru": "\u041a\u043b\u0438\u043d\u0438\u043a\u0430: \u043f\u043e\u0432\u044b\u0448\u0430\u0435\u0442 \u043c\u043e\u0440\u0430\u043b\u044c \u0438 \u0440\u043e\u0441\u0442 \u043d\u0430\u0441\u0435\u043b\u0435\u043d\u0438\u044f.",
        },
    },
}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def validate_build(
    state: GameState,
    building_name: str,
) -> tuple[bool, str]:
    """Check whether the settlement can construct *building_name*.

    Returns
    -------
    (True, "")
        Construction is allowed.
    (False, reason)
        Construction is blocked; *reason* is a human-readable explanation.
    """
    if building_name not in BUILDINGS:
        return False, f"Unknown building: {building_name}"

    spec = BUILDINGS[building_name]
    current_count = state.buildings.get(building_name, 0)

    if current_count >= spec["max_count"]:
        return (
            False,
            f"Maximum {spec['max_count']} {building_name}(s) already built.",
        )

    if state.scrap < spec["cost"]:
        return (
            False,
            f"Not enough scrap: need {spec['cost']}, have {state.scrap}.",
        )

    return True, ""


def apply_build(
    state: GameState,
    building_name: str,
) -> dict[str, int]:
    """Deduct scrap, increment the building counter, and return deltas.

    **Mutates** ``state.buildings`` in place (adds the building).  The scrap
    cost is returned as a negative delta so the caller can merge it with other
    deltas before final application.
    """
    spec = BUILDINGS[building_name]

    # Deduct construction cost via delta.
    deltas: dict[str, int] = {"scrap": -spec["cost"]}

    # Record the new building.
    state.buildings[building_name] = state.buildings.get(building_name, 0) + 1

    return deltas


def calculate_building_effects(buildings: dict[str, int]) -> dict[str, int]:
    """Sum the per-turn effects of all buildings the settlement currently owns.

    Parameters
    ----------
    buildings:
        Mapping of ``building_name -> count`` (e.g. ``{"farm": 2, "clinic": 1}``).

    Returns
    -------
    dict:
        Aggregated per-turn deltas (e.g. ``{"food": 30, "morale": 3}``).
    """
    totals: dict[str, int] = {}

    for name, count in buildings.items():
        spec = BUILDINGS.get(name)
        if spec is None:
            continue
        for resource, amount in spec["effects"].items():
            totals[resource] = totals.get(resource, 0) + amount * count

    # Clinic special: each clinic grants +1 population growth per turn.
    clinic_count = buildings.get("clinic", 0)
    if clinic_count > 0:
        totals["population"] = totals.get("population", 0) + clinic_count

    return totals

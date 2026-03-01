"""Building catalog, validation, construction, and per-turn effect calculation."""

from __future__ import annotations

from math import ceil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot.engine.game_state import GameState

from bot.engine.skills import get_skill_effect


# ---------------------------------------------------------------------------
# Building catalog
# ---------------------------------------------------------------------------
# Each entry defines:
#   cost        - scrap required to construct
#   effects     - dict of per-turn resource deltas while the building stands
#   max_count   - maximum number of this building a settlement may have
#   min_level   - minimum player level to unlock this building
#   description - flavour text (kept in both languages for tooltips)
# ---------------------------------------------------------------------------

BUILDINGS: dict[str, dict] = {
    "farm": {
        "cost": 30,
        "effects": {"food": 15},
        "max_count": 5,
        "min_level": 1,
        "description": {
            "en": "Irrigated plots that yield food each turn.",
            "ru": "Орошаемые участки, дающие еду каждый ход.",
        },
    },
    "watchtower": {
        "cost": 25,
        "effects": {"defense": 5},
        "max_count": 4,
        "min_level": 1,
        "description": {
            "en": "A vantage point that strengthens settlement defense.",
            "ru": "Наблюдательная башня, укрепляющая оборону.",
        },
    },
    "workshop": {
        "cost": 40,
        "effects": {"scrap": 10},
        "max_count": 3,
        "min_level": 1,
        "description": {
            "en": "Salvagers refine junk into usable scrap each turn.",
            "ru": "Мастерская, перерабатывающая мусор в полезный хлам.",
        },
    },
    "barracks": {
        "cost": 35,
        "effects": {"defense": 3},
        "max_count": 2,
        "min_level": 1,
        "description": {
            "en": "Military quarters that boost defense and allow more settlers.",
            "ru": "Казармы: улучшают оборону и вместимость.",
        },
    },
    "shelter": {
        "cost": 20,
        "effects": {"morale": 2},
        "max_count": 4,
        "min_level": 1,
        "description": {
            "en": "Basic housing that improves morale.",
            "ru": "Укрытие, повышающее мораль.",
        },
    },
    "clinic": {
        "cost": 45,
        "effects": {"morale": 3},
        "max_count": 2,
        "min_level": 1,
        "description": {
            "en": "Medical facility that improves morale and population growth.",
            "ru": "Клиника: повышает мораль и рост населения.",
        },
    },
    # --- New buildings unlocked by level ---
    "market": {
        "cost": 35,
        "effects": {"gold": 3},
        "max_count": 3,
        "min_level": 3,
        "description": {
            "en": "Trading post that generates gold each turn.",
            "ru": "Торговый пост, приносящий золото каждый ход.",
        },
    },
    "radio_tower": {
        "cost": 50,
        "effects": {"defense": 4, "morale": 2},
        "max_count": 2,
        "min_level": 7,
        "description": {
            "en": "Broadcasts boost morale and improve early-warning defense.",
            "ru": "Радиовышка: поднимает мораль и улучшает раннее предупреждение.",
        },
    },
    "armory": {
        "cost": 60,
        "effects": {"defense": 8},
        "max_count": 2,
        "min_level": 12,
        "description": {
            "en": "Heavy weapons storage that significantly boosts defense.",
            "ru": "Арсенал: значительно усиливает оборону.",
        },
    },
    "vault": {
        "cost": 80,
        "effects": {"gold": 5},
        "max_count": 1,
        "min_level": 20,
        "description": {
            "en": "Secure vault that generates substantial gold income.",
            "ru": "Хранилище: приносит значительный доход в золоте.",
        },
    },
}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def _effective_cost(state: GameState, spec: dict) -> int:
    """Return the scrap cost after Scrap Mastery skill discount."""
    base = spec["cost"]
    discount_pct = get_skill_effect(state, "scrap_mastery")
    if discount_pct > 0:
        return max(1, ceil(base * (1.0 - discount_pct / 100.0)))
    return base


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

    # Level gate
    if state.level < spec["min_level"]:
        return (
            False,
            f"{building_name} requires level {spec['min_level']} (you are level {state.level}).",
        )

    current_count = state.buildings.get(building_name, 0)

    if current_count >= spec["max_count"]:
        return (
            False,
            f"Maximum {spec['max_count']} {building_name}(s) already built.",
        )

    cost = _effective_cost(state, spec)
    if state.scrap < cost:
        return (
            False,
            f"Not enough scrap: need {cost}, have {state.scrap}.",
        )

    return True, ""


def apply_build(
    state: GameState,
    building_name: str,
) -> dict[str, int]:
    """Deduct scrap, increment the building counter, and return deltas.

    **Mutates** ``state.buildings`` in place (adds the building).  The scrap
    cost is returned as a negative delta so the caller can merge it with other
    deltas before final application.  Skill: Scrap Mastery discount is applied.
    """
    spec = BUILDINGS[building_name]
    cost = _effective_cost(state, spec)

    # Deduct construction cost via delta.
    deltas: dict[str, int] = {"scrap": -cost}

    # Record the new building.
    state.buildings[building_name] = state.buildings.get(building_name, 0) + 1

    return deltas


def calculate_building_effects(
    buildings: dict[str, int],
    state: GameState | None = None,
) -> dict[str, int]:
    """Sum the per-turn effects of all buildings the settlement currently owns.

    Parameters
    ----------
    buildings:
        Mapping of ``building_name -> count`` (e.g. ``{"farm": 2, "clinic": 1}``).
    state:
        Optional game state — if provided, skill bonuses are applied.

    Returns
    -------
    dict:
        Aggregated per-turn deltas (e.g. ``{"food": 30, "morale": 3}``).
    """
    totals: dict[str, int] = {}

    # Skill: Fortification Expert — extra per defense-producing building
    fort_bonus = int(get_skill_effect(state, "fortification_expert")) if state else 0

    for name, count in buildings.items():
        spec = BUILDINGS.get(name)
        if spec is None:
            continue
        for resource, amount in spec["effects"].items():
            totals[resource] = totals.get(resource, 0) + amount * count
            # Apply fortification expert bonus to defense-producing buildings
            if resource == "defense" and fort_bonus > 0:
                totals["defense"] = totals.get("defense", 0) + fort_bonus * count

    # Clinic special: each clinic grants +1 population growth per turn.
    clinic_count = buildings.get("clinic", 0)
    if clinic_count > 0:
        totals["population"] = totals.get("population", 0) + clinic_count

    return totals


def get_available_buildings(level: int) -> list[str]:
    """Return building names available at the given player level."""
    return [
        name for name, spec in BUILDINGS.items()
        if spec["min_level"] <= level
    ]

"""Per-turn resource calculations and action bonuses."""

from __future__ import annotations

import random
from math import ceil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot.engine.game_state import GameState


def calculate_base_deltas(state: GameState) -> dict[str, int]:
    """Compute the passive per-turn resource changes.

    These deltas are applied every turn regardless of the player's chosen
    action.  They model baseline survival costs:

    * Food consumed = ceil(population * 0.5)
    * Population grows by +2 when morale > 60, shrinks by -2 when morale < 30
    * Morale drifts toward 50 at a rate of 2 per turn
    * Defense decays by -3 per turn (entropy, wear)
    """
    deltas: dict[str, int] = {
        "population": 0,
        "food": 0,
        "scrap": 0,
        "morale": 0,
        "defense": 0,
    }

    # --- Food consumption ---
    food_consumed = ceil(state.population * 0.5)
    deltas["food"] -= food_consumed

    # --- Population growth / shrinkage ---
    if state.morale > 60:
        deltas["population"] += 2
    elif state.morale < 30:
        deltas["population"] -= 2

    # --- Morale drift toward 50 ---
    if state.morale > 50:
        deltas["morale"] -= min(2, state.morale - 50)
    elif state.morale < 50:
        deltas["morale"] += min(2, 50 - state.morale)

    # --- Defense decay ---
    deltas["defense"] -= 3

    return deltas


def apply_action_bonus(
    action: str,
    target: str | None,
    state: GameState,
) -> dict[str, int]:
    """Return additional resource deltas from the player's chosen action.

    The ``"build"`` action is mostly handled by the buildings module; we only
    add the base morale bump here.

    Parameters
    ----------
    action:
        One of ``build``, ``explore``, ``trade``, ``defend``,
        ``diplomacy``, ``rest``.
    target:
        Optional qualifier (e.g. building name for "build", faction name
        for "diplomacy").
    state:
        Current game state, used for conditional bonuses.
    """
    deltas: dict[str, int] = {
        "population": 0,
        "food": 0,
        "scrap": 0,
        "morale": 0,
        "defense": 0,
    }

    if action == "build":
        # Building-specific deltas are computed in buildings.apply_build;
        # here we just give a base morale boost for construction activity.
        deltas["morale"] += 5

    elif action == "explore":
        # Scavenge the wastes for scrap.
        scrap_found = random.randint(15, 30)
        deltas["scrap"] += scrap_found
        deltas["morale"] += 3

        # 20 % chance of a dangerous encounter.
        if random.random() < 0.20:
            deltas["population"] -= 3

    elif action == "trade":
        deltas["food"] += 20
        deltas["scrap"] -= 15
        # Traders appreciate repeat customers.
        if state.traders_rep > 30:
            deltas["food"] += 5  # bonus goods from friendly traders

    elif action == "defend":
        deltas["defense"] += 15
        deltas["morale"] += 5

    elif action == "diplomacy":
        # Diplomatic gifts cost food.
        deltas["food"] -= 10
        deltas["morale"] += 5

    elif action == "rest":
        deltas["morale"] += 10
        # A restful turn yields a small food production bonus (foraging).
        deltas["food"] += 5

    return deltas

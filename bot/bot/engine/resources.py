"""Per-turn resource calculations and action bonuses."""

from __future__ import annotations

import random
from math import ceil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot.engine.game_state import GameState

from bot.engine.skills import get_skill_effect


def calculate_base_deltas(state: GameState) -> dict[str, int]:
    """Compute the passive per-turn resource changes.

    These deltas are applied every turn regardless of the player's chosen
    action.  They model baseline survival costs:

    * Food consumed = ceil(population * 0.5)
    * Population grows by +2 when morale > 60, shrinks by -2 when morale < 30
    * Morale drifts toward 50 at a rate of 2 per turn
    * Defense decays by -3 per turn (entropy, wear)

    Class passives:
    * Warden ("fortified"): defense decay reduced to -1
    """
    deltas: dict[str, int] = {
        "population": 0,
        "food": 0,
        "scrap": 0,
        "morale": 0,
        "defense": 0,
        "gold": 0,
    }

    # --- Food consumption ---
    food_consumed = ceil(state.population * 0.5)
    # Skill: Iron Stomach reduces food consumption by X%
    iron_stomach_pct = get_skill_effect(state, "iron_stomach")
    if iron_stomach_pct > 0:
        food_consumed = max(1, ceil(food_consumed * (1.0 - iron_stomach_pct / 100.0)))
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

    # --- Defense decay (class-aware) ---
    if state.player_class == "warden":
        deltas["defense"] -= 1  # Warden passive: fortified
    else:
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
        "gold": 0,
    }
    pc = state.player_class

    if action == "build":
        # Building-specific deltas are computed in buildings.apply_build;
        # here we just give a base morale boost for construction activity.
        deltas["morale"] += 5

    elif action == "explore":
        # Scavenge the wastes for scrap.
        scrap_found = random.randint(15, 30)
        # Scavenger passive: +20% scrap
        if pc == "scavenger":
            scrap_found = ceil(scrap_found * 1.2)
        # Skill: Salvage Expert adds flat scrap
        scrap_found += int(get_skill_effect(state, "salvage_expert"))
        deltas["scrap"] += scrap_found
        deltas["morale"] += 3
        # Scavenger affinity: +1 morale
        if pc == "scavenger":
            deltas["morale"] += 1

        # 20% chance of a dangerous encounter.
        if random.random() < 0.20:
            pop_loss = 3
            # Medic passive: -1 population loss from events
            if pc == "medic":
                pop_loss = max(0, pop_loss - 1)
            # Skill: Field Medic reduces pop loss
            pop_loss = max(0, pop_loss - int(get_skill_effect(state, "field_medic")))
            deltas["population"] -= pop_loss

        # Explore earns gold
        gold_earned = 2
        # Skill: Black Market adds gold from explore
        gold_earned += int(get_skill_effect(state, "black_market"))
        deltas["gold"] += gold_earned

    elif action == "trade":
        food_gained = 20
        scrap_cost = 15
        # Trader passive: +10 food, reduced scrap cost
        if pc == "trader":
            food_gained += 10
            scrap_cost = 10
        # Skill: Haggler adds extra food from trade
        food_gained += int(get_skill_effect(state, "haggler"))
        deltas["food"] += food_gained
        deltas["scrap"] -= scrap_cost
        # Traders appreciate repeat customers.
        if state.traders_rep > 30:
            deltas["food"] += 5  # bonus goods from friendly traders

        # Trade earns gold
        gold_earned = 5
        # Skill: Black Market adds gold from trade
        gold_earned += int(get_skill_effect(state, "black_market"))
        deltas["gold"] += gold_earned

    elif action == "defend":
        defense_bonus = 15
        # Warden affinity: +5 extra defense
        if pc == "warden":
            defense_bonus += 5
        # Skill: Patrol Routes adds extra defense
        defense_bonus += int(get_skill_effect(state, "patrol_routes"))
        deltas["defense"] += defense_bonus
        deltas["morale"] += 5

    elif action == "diplomacy":
        # Diplomatic gifts cost food.
        food_cost = 10
        # Diplomat passive: costs 5 food instead of 10
        if pc == "diplomat":
            food_cost = 5
        deltas["food"] -= food_cost
        morale_gain = 5
        # Diplomat affinity: +3 morale
        if pc == "diplomat":
            morale_gain += 3
        deltas["morale"] += morale_gain

    elif action == "rest":
        morale_gain = 10
        food_gain = 5
        # Medic affinity: +5 morale, +3 food
        if pc == "medic":
            morale_gain += 5
            food_gain += 3
        # Skill: Inspiring Leader boosts rest morale
        morale_gain += int(get_skill_effect(state, "inspiring_leader"))
        deltas["morale"] += morale_gain
        deltas["food"] += food_gain

    return deltas

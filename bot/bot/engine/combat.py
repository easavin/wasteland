"""Combat resolution for settlement vs settlement PvP."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot.engine.game_state import GameState


def _get_attack_power(gs: "GameState") -> int:
    """Derive attack from level, population, barracks."""
    base = gs.level * 2 + gs.population // 10
    barracks = (gs.buildings or {}).get("barracks", 0)
    return max(1, base + barracks * 5)


def _get_defense_power(gs: "GameState") -> int:
    """Use defense stat + watchtower/barracks bonus."""
    base = gs.defense
    watchtower = (gs.buildings or {}).get("watchtower", 0)
    barracks = (gs.buildings or {}).get("barracks", 0)
    return max(1, base + watchtower * 5 + barracks * 3)


def resolve_siege(
    challenger: dict,
    defender: dict,
) -> dict:
    """Resolve a siege battle. Returns outcome dict.

    outcome: {
        winner_game_id, loser_game_id,
        challenger_pop_delta, defender_pop_delta,
        challenger_morale_delta, defender_morale_delta,
        gold_transferred, scrap_transferred,
        narration
    }
    """
    c_attack = _get_attack_power(_dict_to_game_state(challenger))
    c_def = _get_defense_power(_dict_to_game_state(challenger))
    d_attack = _get_attack_power(_dict_to_game_state(defender))
    d_def = _get_defense_power(_dict_to_game_state(defender))

    # Roll: each side gets random 0.8-1.2 of their power
    c_roll = c_attack * (0.8 + random.random() * 0.4)
    d_roll = d_def * (0.8 + random.random() * 0.4)
    challenger_score = c_roll - d_roll

    c_roll2 = d_attack * (0.8 + random.random() * 0.4)
    d_roll2 = c_def * (0.8 + random.random() * 0.4)
    defender_score = c_roll2 - d_roll2

    challenger_id = str(challenger.get("id", ""))
    defender_id = str(defender.get("id", ""))

    if challenger_score > defender_score:
        winner_id = challenger_id
        loser_id = defender_id
    else:
        winner_id = defender_id
        loser_id = challenger_id

    # Damage: loser takes pop and morale loss
    pop_loss = random.randint(2, 8)
    morale_loss = random.randint(5, 15)
    gold_loot = min(
        (defender if winner_id == challenger_id else challenger).get("gold", 0),
        random.randint(5, 25),
    )
    scrap_loot = min(
        (defender if winner_id == challenger_id else challenger).get("scrap", 0),
        random.randint(10, 40),
    )

    c_pop = -pop_loss if loser_id == challenger_id else 0
    d_pop = -pop_loss if loser_id == defender_id else 0
    c_morale = -morale_loss if loser_id == challenger_id else 5
    d_morale = -morale_loss if loser_id == defender_id else 5

    if winner_id == challenger_id:
        c_gold = gold_loot
        d_gold = -gold_loot
        c_scrap = scrap_loot
        d_scrap = -scrap_loot
    else:
        c_gold = -gold_loot
        d_gold = gold_loot
        c_scrap = -scrap_loot
        d_scrap = scrap_loot

    return {
        "winner_game_id": winner_id,
        "loser_game_id": loser_id,
        "challenger_pop_delta": c_pop,
        "defender_pop_delta": d_pop,
        "challenger_morale_delta": c_morale,
        "defender_morale_delta": d_morale,
        "challenger_gold_delta": c_gold,
        "defender_gold_delta": d_gold,
        "challenger_scrap_delta": c_scrap,
        "defender_scrap_delta": d_scrap,
    }


def _dict_to_game_state(d: dict) -> "GameState":
    """Build a minimal GameState from a dict for combat calc."""
    from bot.engine.game_state import GameState
    gs = GameState()
    gs.level = int(d.get("level", 1))
    gs.population = int(d.get("population", 50))
    gs.defense = int(d.get("defense", 30))
    gs.buildings = d.get("buildings") or {}
    if isinstance(gs.buildings, str):
        import json
        gs.buildings = json.loads(gs.buildings) if gs.buildings else {}
    return gs

"""Level, XP, zone, and milestone progression system."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot.engine.game_state import GameState


# ---------------------------------------------------------------------------
# XP / Level formulas
# ---------------------------------------------------------------------------

def xp_for_level(level: int) -> int:
    """Return the *cumulative* XP required to reach *level*.

    Formula: 100*n + 50*n*(n-1)
        L1  = 100
        L2  = 300
        L3  = 600
        L5  = 1,500
        L10 = 5,500
        L20 = 20,000
    """
    return 100 * level + 50 * level * (level - 1)


def xp_to_next_level(state: GameState) -> int:
    """Return how much more XP the player needs for the next level."""
    needed = xp_for_level(state.level + 1)
    return max(0, needed - state.xp)


def xp_progress_in_level(state: GameState) -> tuple[int, int]:
    """Return (current_xp_in_level, xp_needed_for_level).

    Useful for displaying a progress bar like  "420 / 600 XP".
    """
    prev = xp_for_level(state.level)
    nxt = xp_for_level(state.level + 1)
    current_in_level = state.xp - prev
    level_size = nxt - prev
    return max(0, current_in_level), level_size


# ---------------------------------------------------------------------------
# XP calculation per turn
# ---------------------------------------------------------------------------

_ACTION_XP: dict[str, int] = {
    "build": 8,
    "explore": 5,
    "trade": 3,
    "defend": 3,
    "diplomacy": 5,
    "rest": 2,
}


def calculate_xp_for_turn(
    action: str,
    event: dict | None,
    deltas: dict[str, int],
    state: GameState,
) -> int:
    """Compute total XP earned this turn."""
    xp = 10  # base XP for any turn

    # Action bonus
    xp += _ACTION_XP.get(action, 0)

    # Surviving a negative event
    if event and any(v < 0 for v in event.get("deltas", {}).values()):
        xp += 5

    return xp


# ---------------------------------------------------------------------------
# Milestone XP (one-time awards)
# ---------------------------------------------------------------------------

def check_milestones(state: GameState) -> list[tuple[str, int]]:
    """Return a list of ``(milestone_id, xp_reward)`` for newly achieved milestones.

    Does NOT mutate state — caller is responsible for appending to
    ``state.milestones``.
    """
    achieved: list[tuple[str, int]] = []
    existing = set(state.milestones)

    # Population milestones: every 25 past 50
    for threshold in range(75, state.population + 1, 25):
        mid = f"pop_{threshold}"
        if mid not in existing:
            achieved.append((mid, 50))

    # First-of-each-building milestones
    for bname, count in state.buildings.items():
        if count > 0:
            mid = f"first_{bname}"
            if mid not in existing:
                achieved.append((mid, 20))

    # Allied with any faction (rep > 50)
    for fname, rep in [
        ("raiders", state.raiders_rep),
        ("traders", state.traders_rep),
        ("remnants", state.remnants_rep),
    ]:
        if rep > 50:
            mid = f"allied_{fname}"
            if mid not in existing:
                achieved.append((mid, 100))

    return achieved


# ---------------------------------------------------------------------------
# Level-up processing
# ---------------------------------------------------------------------------

def process_level_ups(state: GameState, xp_earned: int) -> list[int]:
    """Add *xp_earned* to state and process any level-ups.

    Returns a list of new levels reached (may be multiple if XP is large).
    Mutates ``state.xp``, ``state.level``, ``state.skill_points``, ``state.gold``.
    """
    state.xp += xp_earned
    new_levels: list[int] = []

    while state.xp >= xp_for_level(state.level + 1):
        state.level += 1
        new_levels.append(state.level)

        # Rewards per level
        state.gold += 5

        # Skill point every 5 levels
        if state.level % 5 == 0:
            state.skill_points += 1

    return new_levels


# ---------------------------------------------------------------------------
# Gold calculation per turn
# ---------------------------------------------------------------------------

def calculate_gold_for_turn(action: str, event: dict | None) -> int:
    """Compute gold earned this turn from action and events."""
    gold = 0

    if action == "trade":
        gold += 5
    elif action == "explore":
        gold += 2

    # Some events may have gold deltas — handled separately in event system
    return gold


# ---------------------------------------------------------------------------
# Zone system
# ---------------------------------------------------------------------------

def get_zone(level: int) -> int:
    """Return the current zone based on player level."""
    if level < 10:
        return 1
    if level < 15:
        return 2
    if level < 20:
        return 3
    if level < 30:
        return 4
    return 5


def get_zone_difficulty_multiplier(zone: int) -> float:
    """Event delta multiplier by zone — higher zones = harsher events."""
    return {1: 1.0, 2: 1.2, 3: 1.4, 4: 1.6, 5: 2.0}.get(zone, 1.0)

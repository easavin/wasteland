"""Win and loss condition checks."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot.engine.game_state import GameState


def check_win(state: GameState) -> bool:
    """Return ``True`` if the player has achieved victory.

    Victory conditions (all must be met):
      * Reached turn 50 or later
      * Population >= 100
      * Morale >= 60
    """
    return (
        state.turn_number >= 50
        and state.population >= 100
        and state.morale >= 60
    )


def check_loss(state: GameState) -> tuple[bool, str]:
    """Return ``(is_lost, reason)`` indicating whether the game has ended in defeat.

    Loss conditions (any one triggers defeat):
      * Population drops to zero  ->  ``"population_zero"``
      * Food has been at zero for 2 or more consecutive turns  ->  ``"starvation"``

    If the game is not lost the returned reason is an empty string.
    """
    if state.population <= 0:
        return True, "population_zero"

    if state.food_zero_turns >= 2:
        return True, "starvation"

    return False, ""

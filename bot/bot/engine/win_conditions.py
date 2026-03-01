"""Win and loss condition checks."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot.engine.game_state import GameState


def check_win(state: GameState) -> bool:
    """Return ``True`` if the player has achieved victory.

    The game is now unlimited — there is no win condition.
    """
    return False


def check_loss(
    state: GameState,
    starvation_threshold: int = 2,
) -> tuple[bool, str]:
    """Return ``(is_lost, reason)`` indicating whether the game has ended in defeat.

    Loss conditions (any one triggers defeat):
      * Population drops to zero  ->  ``"population_zero"``
      * Food has been at zero for *starvation_threshold* or more consecutive
        turns  ->  ``"starvation"``  (default 2; Medic class uses 3)

    If the game is not lost the returned reason is an empty string.
    """
    if state.population <= 0:
        return True, "population_zero"

    if state.food_zero_turns >= starvation_threshold:
        return True, "starvation"

    return False, ""

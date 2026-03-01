"""Core turn-processing pipeline.

Orchestrates a single game turn: computes deltas, rolls events, updates
faction reputation, checks win/loss, generates narration, and persists
everything to the database.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import asyncpg

from bot.engine.buildings import (
    apply_build,
    calculate_building_effects,
    validate_build,
)
from bot.engine.events import roll_random_event
from bot.engine.factions import update_faction_rep
from bot.engine.game_state import GameState, TurnResult
from bot.engine.resources import apply_action_bonus, calculate_base_deltas
from bot.engine.win_conditions import check_loss, check_win

logger = logging.getLogger(__name__)

# Actions that map to player-style axes for the EMA update.
_ACTION_STYLE_MAP: dict[str, str] = {
    "build": "style_diplomacy",
    "explore": "style_exploration",
    "trade": "style_commerce",
    "defend": "style_aggression",
    "diplomacy": "style_diplomacy",
    # "rest" intentionally absent -- no style signal
}

_EMA_ALPHA = 0.2  # new = (1 - alpha) * old + alpha * signal


# ---------------------------------------------------------------------------
# Delta helpers
# ---------------------------------------------------------------------------

def _merge_deltas(base: dict[str, int], extra: dict[str, int]) -> None:
    """Add *extra* deltas into *base* in-place."""
    for key, value in extra.items():
        base[key] = base.get(key, 0) + value


def _apply_deltas_to_state(state: GameState, deltas: dict[str, int]) -> None:
    """Mutate *state* by adding every applicable delta."""
    resource_keys = ("population", "food", "scrap", "morale", "defense")
    for key in resource_keys:
        if key in deltas:
            setattr(state, key, getattr(state, key) + deltas[key])

    # Faction reputation deltas
    for rep_key in ("raiders_rep", "traders_rep", "remnants_rep"):
        if rep_key in deltas:
            setattr(state, rep_key, getattr(state, rep_key) + deltas[rep_key])


def _update_player_style(state: GameState, action: str) -> None:
    """Apply exponential moving average to the player-style axis corresponding
    to *action*.  If the action has no style mapping (e.g. ``"rest"``), this
    is a no-op.
    """
    style_attr = _ACTION_STYLE_MAP.get(action)
    if style_attr is None:
        return
    old = getattr(state, style_attr)
    new = (1.0 - _EMA_ALPHA) * old + _EMA_ALPHA * 1.0
    setattr(state, style_attr, new)


# ---------------------------------------------------------------------------
# Fallback narration (used when narrator is None)
# ---------------------------------------------------------------------------

def _plain_narration(
    state: GameState,
    deltas: dict[str, int],
    event: dict | None,
    action: str,
    target: str | None,
    outcome: str,
) -> str:
    """Generate a simple text summary without an AI narrator."""
    parts: list[str] = []

    # Action description
    if target:
        parts.append(f"Action: {action} ({target})")
    else:
        parts.append(f"Action: {action}")

    # Delta summary
    delta_strs = []
    for key in ("population", "food", "scrap", "morale", "defense"):
        val = deltas.get(key, 0)
        if val != 0:
            sign = "+" if val > 0 else ""
            delta_strs.append(f"{key} {sign}{val}")
    if delta_strs:
        parts.append("Changes: " + ", ".join(delta_strs))

    # Event
    if event:
        parts.append(f"Event: {event['name']} -- {event.get('narration_hint', '')}")

    # Current resources
    parts.append(
        f"Status: pop={state.population}, food={state.food}, "
        f"scrap={state.scrap}, morale={state.morale}, defense={state.defense}"
    )

    # Outcome
    if outcome == "won":
        parts.append("*** VICTORY! Your settlement has thrived. ***")
    elif outcome == "lost":
        parts.append("*** DEFEAT. The wasteland claims another settlement. ***")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

async def _persist_turn(
    pool: asyncpg.Pool,
    state: GameState,
    action: str,
    target: str | None,
    snapshot_before: dict[str, int],
    deltas: dict[str, int],
    event: dict | None,
    narration: str,
    language: str,
) -> None:
    """Write updated game_state, insert turn_history row, and log an
    analytics event.  Runs inside a single transaction for consistency.
    """
    async with pool.acquire() as conn:
        async with conn.transaction():
            # 1. Update game_states row.
            await conn.execute(
                """
                UPDATE game_states
                   SET status          = $1,
                       turn_number     = $2,
                       population      = $3,
                       food            = $4,
                       scrap           = $5,
                       morale          = $6,
                       defense         = $7,
                       food_zero_turns = $8,
                       raiders_rep     = $9,
                       traders_rep     = $10,
                       remnants_rep    = $11,
                       style_aggression  = $12,
                       style_commerce    = $13,
                       style_exploration = $14,
                       style_diplomacy   = $15,
                       buildings       = $16::jsonb,
                       active_effects  = $17::jsonb,
                       narrator_memory = $18::jsonb,
                       updated_at      = NOW(),
                       ended_at        = CASE WHEN $1 IN ('won','lost') THEN NOW() ELSE ended_at END
                 WHERE id = $19
                """,
                state.status,
                state.turn_number,
                state.population,
                state.food,
                state.scrap,
                state.morale,
                state.defense,
                state.food_zero_turns,
                state.raiders_rep,
                state.traders_rep,
                state.remnants_rep,
                state.style_aggression,
                state.style_commerce,
                state.style_exploration,
                state.style_diplomacy,
                json.dumps(state.buildings),
                json.dumps(state.active_effects),
                json.dumps(state.narrator_memory),
                state.id,
            )

            # 2. Insert turn_history row.
            await conn.execute(
                """
                INSERT INTO turn_history (
                    game_id, turn_number, player_action, action_target,
                    pop_before, food_before, scrap_before, morale_before, defense_before,
                    pop_delta, food_delta, scrap_delta, morale_delta, defense_delta,
                    event_id, event_outcome, narration, narration_lang
                ) VALUES (
                    $1, $2, $3, $4,
                    $5, $6, $7, $8, $9,
                    $10, $11, $12, $13, $14,
                    $15, $16, $17, $18
                )
                """,
                state.id,
                state.turn_number,
                action,
                target,
                snapshot_before.get("population", 0),
                snapshot_before.get("food", 0),
                snapshot_before.get("scrap", 0),
                snapshot_before.get("morale", 0),
                snapshot_before.get("defense", 0),
                deltas.get("population", 0),
                deltas.get("food", 0),
                deltas.get("scrap", 0),
                deltas.get("morale", 0),
                deltas.get("defense", 0),
                event["id"] if event else None,
                event.get("narration_hint", "") if event else None,
                narration,
                language,
            )

            # 3. Analytics event.
            analytics_data: dict[str, Any] = {
                "game_id": state.id,
                "turn": state.turn_number,
                "action": action,
                "target": target,
                "deltas": {k: v for k, v in deltas.items() if v != 0},
            }
            if event:
                analytics_data["event_id"] = event["id"]

            await conn.execute(
                """
                INSERT INTO analytics_events (player_id, event_type, event_data)
                VALUES ($1, 'turn_completed', $2::jsonb)
                """,
                state.player_id,
                json.dumps(analytics_data),
            )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def process_turn(
    state: GameState,
    action: str,
    target: str | None,
    pool: asyncpg.Pool | None,
    narrator: Any | None,
    language: str = "en",
    is_premium: bool = False,
) -> TurnResult:
    """Process a single game turn and return the result.

    Parameters
    ----------
    state:
        The current (mutable) game state.  **Will be mutated in place.**
    action:
        Player's chosen action (``build``, ``explore``, ``trade``,
        ``defend``, ``diplomacy``, ``rest``).
    target:
        Optional qualifier -- building name for ``"build"``, faction name
        for ``"diplomacy"``, etc.
    pool:
        asyncpg connection pool.  May be ``None`` in tests -- persistence
        is skipped.
    narrator:
        AI narrator object with an ``async generate(...)`` method.
        May be ``None`` for Phase 1 testing (plain-text fallback is used).
    language:
        ``"en"`` or ``"ru"``.
    is_premium:
        Whether the player has premium (may unlock richer narration).

    Returns
    -------
    TurnResult:
        Contains narration, mutated state, outcome, event info, and deltas.
    """
    # Step 1 -- Increment turn number.
    state.turn_number += 1
    turn = state.turn_number

    # Step 2 -- Snapshot resources *before* changes.
    snapshot_before = state.snapshot_resources()

    # Step 3 -- Base per-turn deltas (food consumption, morale drift, etc.).
    all_deltas: dict[str, int] = calculate_base_deltas(state)

    # Step 4 -- Building per-turn effects.
    building_effects = calculate_building_effects(state.buildings)
    _merge_deltas(all_deltas, building_effects)

    # Step 5 -- Action bonus.
    action_deltas = apply_action_bonus(action, target, state)
    _merge_deltas(all_deltas, action_deltas)

    # Step 6 -- Handle "build" action (validate + apply).
    build_error: str | None = None
    if action == "build":
        can_build, reason = validate_build(state, target or "")
        if can_build:
            build_deltas = apply_build(state, target or "")
            _merge_deltas(all_deltas, build_deltas)
        else:
            build_error = reason
            logger.warning(
                "Build rejected for game %s: %s", state.id, reason,
            )

    # Step 7 -- Random event.
    event = roll_random_event(state, turn)

    # Step 8 -- Merge event deltas.
    if event:
        _merge_deltas(all_deltas, event["deltas"])

    # Step 9 -- Faction reputation.
    rep_changes = update_faction_rep(state, action, target)
    _merge_deltas(all_deltas, rep_changes)

    # Step 10 -- Apply all deltas to state.
    _apply_deltas_to_state(state, all_deltas)

    # Step 11 -- Clamp resources within legal ranges.
    state.clamp_resources()

    # Step 12 -- Starvation tracker.
    if state.food <= 0:
        state.food_zero_turns += 1
    else:
        state.food_zero_turns = 0

    # Step 13 -- Update player style (EMA).
    _update_player_style(state, action)

    # Step 14 -- Check win / loss.
    outcome: str = "continue"
    if check_win(state):
        outcome = "won"
        state.status = "won"
    else:
        is_lost, loss_reason = check_loss(state)
        if is_lost:
            outcome = "lost"
            state.status = "lost"

    # Build a concise delta dict (only non-zero entries) for narration.
    display_deltas: dict[str, int] = {
        k: v for k, v in all_deltas.items() if v != 0
    }

    # Step 15 -- Generate narration.
    narration: str
    if narrator is not None:
        try:
            narration = await narrator.generate(
                state=state,
                deltas=display_deltas,
                event=event,
                action=action,
                target=target,
                language=language,
                is_premium=is_premium,
                build_error=build_error,
            )
        except Exception:
            logger.exception("Narrator failed; falling back to plain text")
            narration = _plain_narration(
                state, display_deltas, event, action, target, outcome,
            )
    else:
        narration = _plain_narration(
            state, display_deltas, event, action, target, outcome,
        )

    # Step 16 -- Update narrator memory (keep last 5 summaries).
    summary = (
        f"T{turn}: {action}"
        + (f"({target})" if target else "")
        + f" | pop={state.population} food={state.food} scrap={state.scrap}"
        + f" morale={state.morale} def={state.defense}"
    )
    if event:
        summary += f" | event={event['id']}"
    state.narrator_memory.append(summary)
    state.narrator_memory = state.narrator_memory[-5:]

    # Step 17 -- Persist to database (skip if pool is None -- test mode).
    if pool is not None:
        try:
            await _persist_turn(
                pool=pool,
                state=state,
                action=action,
                target=target,
                snapshot_before=snapshot_before,
                deltas=all_deltas,
                event=event,
                narration=narration,
                language=language,
            )
        except Exception:
            logger.exception("Failed to persist turn %d for game %s", turn, state.id)
            # We still return the result even if persistence fails so the
            # player sees the narration.  A retry / reconciliation mechanism
            # can handle this later.

    # Step 18 -- Return result.
    return TurnResult(
        narration=narration,
        new_state=state,
        outcome=outcome,
        event=event,
        deltas=display_deltas,
    )

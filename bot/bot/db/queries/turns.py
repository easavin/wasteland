"""Turn-history database queries."""

import logging

import asyncpg

logger = logging.getLogger(__name__)


async def insert_turn(
    pool: asyncpg.Pool,
    game_id: str,
    turn_number: int,
    player_action: str,
    action_target: str | None,
    pop_before: int,
    food_before: int,
    scrap_before: int,
    morale_before: int,
    defense_before: int,
    pop_delta: int,
    food_delta: int,
    scrap_delta: int,
    morale_delta: int,
    defense_delta: int,
    event_id: str | None,
    event_outcome: str | None,
    narration: str,
    narration_lang: str,
    voice_input: bool,
    voice_text: str | None,
) -> dict:
    """Record a single turn in the history and return the inserted row."""
    row = await pool.fetchrow(
        """
        INSERT INTO turn_history (
            game_id, turn_number, player_action, action_target,
            pop_before, food_before, scrap_before, morale_before, defense_before,
            pop_delta, food_delta, scrap_delta, morale_delta, defense_delta,
            event_id, event_outcome,
            narration, narration_lang,
            voice_input, voice_text
        ) VALUES (
            $1, $2, $3, $4,
            $5, $6, $7, $8, $9,
            $10, $11, $12, $13, $14,
            $15, $16,
            $17, $18,
            $19, $20
        )
        RETURNING *
        """,
        game_id,
        turn_number,
        player_action,
        action_target,
        pop_before,
        food_before,
        scrap_before,
        morale_before,
        defense_before,
        pop_delta,
        food_delta,
        scrap_delta,
        morale_delta,
        defense_delta,
        event_id,
        event_outcome,
        narration,
        narration_lang,
        voice_input,
        voice_text,
    )
    return dict(row)


async def get_turns_for_game(
    pool: asyncpg.Pool,
    game_id: str,
) -> list[dict]:
    """Return every turn for *game_id*, ordered by turn number ascending."""
    rows = await pool.fetch(
        """
        SELECT *
          FROM turn_history
         WHERE game_id = $1
         ORDER BY turn_number ASC
        """,
        game_id,
    )
    return [dict(r) for r in rows]

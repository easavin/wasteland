"""Handler for /dispatch command — view and claim daily missions."""

from __future__ import annotations

import logging
import random
from datetime import date, datetime, timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from bot.db.queries.players import get_player_by_telegram_id
from bot.db.queries.game_states import get_active_game, update_game_state
from bot.engine.game_state import GameState
from bot.engine.daily_missions import (
    generate_daily_missions,
    format_missions_display,
    are_all_complete,
    MISSION_STRINGS,
)
from bot.engine.items import add_item_to_inventory, roll_item_drop
from bot.i18n import get_text

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DB helpers for daily_missions table
# ---------------------------------------------------------------------------

async def _get_today_missions(pool, player_id: str) -> dict | None:
    """Fetch today's mission row for a player, or None."""
    today = date.today()
    row = await pool.fetchrow(
        """
        SELECT * FROM daily_missions
         WHERE player_id = $1
           AND mission_date = $2
        """,
        player_id, today,
    )
    return dict(row) if row else None


async def _upsert_missions(pool, player_id: str, missions: list[dict], bonus_claimed: bool = False) -> None:
    """Insert or update today's missions."""
    import json
    today = date.today()
    await pool.execute(
        """
        INSERT INTO daily_missions (player_id, mission_date, missions, bonus_claimed)
        VALUES ($1, $2, $3::jsonb, $4)
        ON CONFLICT (player_id, mission_date)
        DO UPDATE SET missions = $3::jsonb,
                      bonus_claimed = $4,
                      updated_at = NOW()
        """,
        player_id, today, json.dumps(missions), bonus_claimed,
    )


# ---------------------------------------------------------------------------
# /dispatch command
# ---------------------------------------------------------------------------

async def handle_dispatch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/dispatch — view today's daily missions with progress."""
    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, update.effective_user.id)
    if not player:
        await update.message.reply_text(get_text("free_text_no_game", "en"))
        return

    lang = player.get("language", "en")
    player_id = str(player["id"])

    game_row = await get_active_game(pool, player_id)
    if not game_row:
        no_game = MISSION_STRINGS["dispatch_no_game"].get(lang, MISSION_STRINGS["dispatch_no_game"]["en"])
        await update.message.reply_text(no_game)
        return

    # Get or generate today's missions
    mission_row = await _get_today_missions(pool, player_id)
    if mission_row is None:
        missions = generate_daily_missions()
        await _upsert_missions(pool, player_id, missions)
        bonus_claimed = False
    else:
        missions = mission_row["missions"]
        if isinstance(missions, str):
            import json
            missions = json.loads(missions)
        bonus_claimed = mission_row.get("bonus_claimed", False)

    # Format display
    text = format_missions_display(missions, lang)

    # Add claim button if all complete
    keyboard = None
    if are_all_complete(missions):
        if bonus_claimed:
            claimed_text = MISSION_STRINGS["dispatch_bonus_claimed"].get(lang, MISSION_STRINGS["dispatch_bonus_claimed"]["en"])
            text += f"\n\n{claimed_text}"
        else:
            all_done = MISSION_STRINGS["dispatch_all_complete"].get(lang, MISSION_STRINGS["dispatch_all_complete"]["en"])
            text += f"\n\n{all_done}"
            btn_label = MISSION_STRINGS["dispatch_claim_button"].get(lang, MISSION_STRINGS["dispatch_claim_button"]["en"])
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(btn_label, callback_data="dispatch:claim"),
            ]])

    try:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")
    except BadRequest:
        await update.message.reply_text(text, reply_markup=keyboard)


# ---------------------------------------------------------------------------
# Callback handler for dispatch:claim
# ---------------------------------------------------------------------------

async def handle_dispatch_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle dispatch:claim callback — award completion bonus."""
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data != "dispatch:claim":
        return

    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, query.from_user.id)
    if not player:
        return

    lang = player.get("language", "en")
    player_id = str(player["id"])

    mission_row = await _get_today_missions(pool, player_id)
    if not mission_row:
        return

    missions = mission_row["missions"]
    if isinstance(missions, str):
        import json
        missions = json.loads(missions)

    if mission_row.get("bonus_claimed", False):
        claimed = MISSION_STRINGS["dispatch_bonus_claimed"].get(lang, MISSION_STRINGS["dispatch_bonus_claimed"]["en"])
        await query.message.reply_text(claimed)
        return

    if not are_all_complete(missions):
        return

    # Award dispatch bonus: +50 XP, +10 gold, +1 random uncommon item
    game_row = await get_active_game(pool, player_id)
    if not game_row:
        return

    state = GameState.from_db_row(game_row)
    state.xp += 50
    state.gold += 10

    # Roll an uncommon item
    from bot.engine.items import ITEMS
    uncommon_items = [iid for iid, spec in ITEMS.items()
                      if spec["rarity"] == "uncommon"]
    if uncommon_items:
        bonus_item = random.choice(uncommon_items)
        state.inventory = add_item_to_inventory(state.inventory, bonus_item)

    await update_game_state(
        pool, state.id,
        xp=state.xp, gold=state.gold, inventory=state.inventory,
    )

    # Mark bonus as claimed
    await _upsert_missions(pool, player_id, missions, bonus_claimed=True)

    # Also apply individual mission rewards
    for mission in missions:
        reward = mission.get("reward", {})
        for key, val in reward.items():
            if key == "scrap":
                state.scrap += val
            elif key == "food":
                state.food += val
            elif key == "gold":
                state.gold += val
            elif key == "morale_bonus":
                state.morale += val
        state.clamp_resources()

    await update_game_state(
        pool, state.id,
        food=state.food, scrap=state.scrap, gold=state.gold, morale=state.morale,
    )

    reward_text = MISSION_STRINGS["dispatch_bonus_reward"].get(lang, MISSION_STRINGS["dispatch_bonus_reward"]["en"])
    try:
        await query.message.reply_text(reward_text, parse_mode="Markdown")
    except BadRequest:
        await query.message.reply_text(reward_text)

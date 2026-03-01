"""Combat / PvP challenge handlers."""

from __future__ import annotations

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.db.queries.players import get_player_by_telegram_id
from bot.db.queries.game_states import get_active_game, get_settlement_by_id, update_game_state
from bot.db.queries.combat import (
    create_challenge,
    get_pending_challenge,
    accept_challenge,
    decline_challenge,
    resolve_challenge,
)
from bot.engine.combat import resolve_siege
from bot.handlers.chat import _get_player_by_username
from bot.utils.display import get_display_name
from bot.i18n import get_text

logger = logging.getLogger(__name__)


async def handle_challenge(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /challenge @username [siege|raid]."""
    args = context.args or []
    if len(args) < 1:
        await update.message.reply_text(get_text("challenge_usage", "en"))
        return

    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, update.effective_user.id)
    if not player:
        await update.message.reply_text(get_text("free_text_no_game", "en"))
        return

    game_row = await get_active_game(pool, str(player["id"]))
    if not game_row:
        await update.message.reply_text(get_text("free_text_no_game", player.get("language", "en")))
        return

    target_player = await _get_player_by_username(pool, args[0])
    if not target_player:
        await update.message.reply_text(get_text("challenge_not_found", player.get("language", "en")))
        return
    if target_player.get("is_npc"):
        await update.message.reply_text(get_text("challenge_npc", player.get("language", "en")))
        return

    target_game = await get_active_game(pool, str(target_player["id"]))
    if not target_game:
        await update.message.reply_text(get_text("challenge_no_game", player.get("language", "en")))
        return

    if str(target_game["id"]) == str(game_row["id"]):
        await update.message.reply_text(get_text("challenge_self", player.get("language", "en")))
        return

    if str(target_game.get("world_id")) != str(game_row.get("world_id")):
        await update.message.reply_text(get_text("challenge_wrong_world", player.get("language", "en")))
        return

    ctype = (args[1].lower() if len(args) > 1 else "siege")
    if ctype not in ("siege", "raid"):
        ctype = "siege"

    challenge = await create_challenge(
        pool,
        str(game_row["id"]),
        str(target_game["id"]),
        ctype,
    )

    challenger_name = get_display_name(game_row=game_row, player_row=player)
    msg = get_text("challenge_sent", player.get("language", "en"), target=target_game.get("display_name") or "?")

    target_lang = target_player.get("language", "en")
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            get_text("challenge_accept_btn", target_lang),
            callback_data=f"challenge:accept:{challenge['id']}",
        ),
        InlineKeyboardButton(
            get_text("challenge_decline_btn", target_lang),
            callback_data=f"challenge:decline:{challenge['id']}",
        ),
    ]])
    try:
        await context.bot.send_message(
            chat_id=target_player["telegram_id"],
            text=get_text("challenge_received", target_lang, challenger=challenger_name, ctype=ctype),
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.warning("Challenge notification failed: %s", e)

    await update.message.reply_text(msg)


async def handle_challenge_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle challenge accept/decline from inline buttons."""
    query = update.callback_query
    await query.answer()
    data = (query.data or "").split(":")

    if len(data) < 3 or data[0] != "challenge":
        return

    action = data[1]
    challenge_id = data[2]
    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, query.from_user.id)
    if not player:
        return

    game_row = await get_active_game(pool, str(player["id"]))
    if not game_row:
        return

    lang = player.get("language", "en")

    if action == "accept":
        ok = await accept_challenge(pool, challenge_id, str(game_row["id"]))
        if not ok:
            await query.message.reply_text(get_text("challenge_expired", lang))
            return

        # Resolve combat
        chall = await pool.fetchrow(
            "SELECT * FROM combat_challenges WHERE id = $1",
            challenge_id,
        )
        if chall and str(chall["defender_game_id"]) == str(game_row["id"]):
            challenger_row = await get_settlement_by_id(pool, str(chall["challenger_game_id"]))
            defender_row = dict(game_row)
            challenger_row = dict(challenger_row) if challenger_row else {}
            outcome = resolve_siege(challenger_row, defender_row)

            await resolve_challenge(pool, challenge_id, outcome)

            # Apply deltas
            c_pop = max(0, challenger_row.get("population", 50) + outcome.get("challenger_pop_delta", 0))
            c_morale = max(0, min(100, challenger_row.get("morale", 70) + outcome.get("challenger_morale_delta", 0)))
            c_gold = max(0, challenger_row.get("gold", 0) + outcome.get("challenger_gold_delta", 0))
            c_scrap = max(0, challenger_row.get("scrap", 0) + outcome.get("challenger_scrap_delta", 0))
            await update_game_state(
                pool, str(chall["challenger_game_id"]),
                population=c_pop, morale=c_morale, gold=c_gold, scrap=c_scrap,
            )
            d_pop = max(0, game_row.get("population", 50) + outcome.get("defender_pop_delta", 0))
            d_morale = max(0, min(100, game_row.get("morale", 70) + outcome.get("defender_morale_delta", 0)))
            d_gold = max(0, game_row.get("gold", 0) + outcome.get("defender_gold_delta", 0))
            d_scrap = max(0, game_row.get("scrap", 0) + outcome.get("defender_scrap_delta", 0))
            await update_game_state(
                pool, str(game_row["id"]),
                population=d_pop, morale=d_morale, gold=d_gold, scrap=d_scrap,
            )

            winner_id = outcome["winner_game_id"]
            if str(winner_id) == str(chall["challenger_game_id"]):
                winner_name = challenger_row.get("display_name") or "Challenger"
                loser_name = game_row.get("display_name") or "Defender"
            else:
                winner_name = game_row.get("display_name") or "Defender"
                loser_name = challenger_row.get("display_name") or "Challenger"

            result_text = get_text("challenge_result", lang, winner=winner_name, loser=loser_name)

            # Notify both
            challenger_tg = await pool.fetchrow(
                "SELECT p.telegram_id FROM game_states gs JOIN players p ON p.id = gs.player_id WHERE gs.id = $1",
                chall["challenger_game_id"],
            )
            if challenger_tg:
                try:
                    await context.bot.send_message(chat_id=challenger_tg["telegram_id"], text=result_text)
                except Exception:
                    pass

            await query.message.reply_text(result_text)
    elif action == "decline":
        await decline_challenge(pool, challenge_id, str(game_row["id"]))
        await query.message.reply_text(get_text("challenge_declined", lang))


async def handle_challenge_accept(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /challenge accept — accept pending challenge."""
    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, update.effective_user.id)
    if not player:
        await update.message.reply_text(get_text("free_text_no_game", "en"))
        return

    game_row = await get_active_game(pool, str(player["id"]))
    if not game_row:
        await update.message.reply_text(get_text("free_text_no_game", player.get("language", "en")))
        return

    pending = await get_pending_challenge(pool, str(game_row["id"]))
    if not pending:
        await update.message.reply_text(get_text("challenge_none_pending", player.get("language", "en")))
        return

    # Create a synthetic callback for the shared logic
    class FakeQuery:
        message = update.message
        from_user = update.effective_user
        data = f"challenge:accept:{pending['id']}"
        async def answer(self):
            pass

    fake_update = Update(update.update_id, message=update.message)
    fake_update.callback_query = FakeQuery()
    await handle_challenge_callback(fake_update, context)


async def handle_challenge_decline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /challenge decline."""
    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, update.effective_user.id)
    if not player:
        await update.message.reply_text(get_text("free_text_no_game", "en"))
        return

    game_row = await get_active_game(pool, str(player["id"]))
    if not game_row:
        await update.message.reply_text(get_text("free_text_no_game", player.get("language", "en")))
        return

    pending = await get_pending_challenge(pool, str(game_row["id"]))
    if not pending:
        await update.message.reply_text(get_text("challenge_none_pending", player.get("language", "en")))
        return

    await decline_challenge(pool, str(pending["id"]), str(game_row["id"]))
    await update.message.reply_text(get_text("challenge_declined", player.get("language", "en")))

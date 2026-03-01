"""Quest / NPC interaction handlers."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.db.queries.players import get_player_by_telegram_id
from bot.db.queries.game_states import get_active_game
from bot.db.queries.npcs import (
    list_npcs_in_zone,
    get_npc_by_game_id,
    list_npc_quests,
    get_player_quest_progress,
    start_quest,
    complete_quest,
)
from bot.i18n import get_text

logger = logging.getLogger(__name__)


async def handle_quest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /quest [npc_name] or /quest accept <key> <npc>."""
    args = (context.args or [])
    if args and args[0].lower() == "accept":
        context.args = args[1:]
        await handle_quest_accept(update, context)
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

    world_id = game_row.get("world_id")
    zone = game_row.get("zone", 1)
    if not world_id:
        await update.message.reply_text(get_text("chat_no_world", player.get("language", "en")))
        return

    args = (context.args or [])
    lang = player.get("language", "en")

    if not args:
        npcs = await list_npcs_in_zone(pool, str(world_id), zone)
        if not npcs:
            await update.message.reply_text(get_text("quest_no_npcs", lang))
            return

        lines = [get_text("quest_list_header", lang) + "\n"]
        for n in npcs:
            name = n.get("display_name") or n.get("settlement_name") or "?"
            lines.append(f"• *{name}* — /quest {name.split()[0]}")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
        return

    npc_name = " ".join(args).strip()
    npcs = await list_npcs_in_zone(pool, str(world_id), zone)
    target = None
    for n in npcs:
        if (n.get("display_name") or n.get("settlement_name") or "").lower().startswith(npc_name.lower()):
            target = n
            break
        if npc_name.lower() in (n.get("display_name") or "").lower():
            target = n
            break

    if not target:
        await update.message.reply_text(get_text("quest_npc_not_found", lang))
        return

    quests = await list_npc_quests(pool, str(target["player_id"]))
    name = target.get("display_name") or target.get("settlement_name") or "?"
    if not quests:
        await update.message.reply_text(
            get_text("quest_npc_no_quests", lang, name=name),
        )
        return

    lines = [get_text("quest_npc_header", lang, name=name) + "\n"]
    for q in quests:
        progress = await get_player_quest_progress(pool, str(player["id"]), str(q["id"]))
        if progress:
            if progress.get("status") == "completed":
                lines.append(f"✓ *{q['name']}* — " + get_text("quest_completed", lang))
            else:
                lines.append(f"⟳ *{q['name']}* — " + get_text("quest_active", lang))
        else:
            lines.append(f"• *{q['name']}* — /quest accept {q['quest_key']} {name.split()[0]}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def handle_quest_accept(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /quest accept <quest_key> <npc_name> — accept a quest."""
    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, update.effective_user.id)
    if not player:
        await update.message.reply_text(get_text("free_text_no_game", "en"))
        return

    game_row = await get_active_game(pool, str(player["id"]))
    if not game_row:
        await update.message.reply_text(get_text("free_text_no_game", player.get("language", "en")))
        return

    world_id = game_row.get("world_id")
    zone = game_row.get("zone", 1)
    if not world_id:
        await update.message.reply_text(get_text("chat_no_world", player.get("language", "en")))
        return

    args = (context.args or [])
    if len(args) < 2:
        await update.message.reply_text(get_text("quest_accept_usage", player.get("language", "en")))
        return

    quest_key = args[0]
    npc_name = " ".join(args[1:])
    lang = player.get("language", "en")

    npcs = await list_npcs_in_zone(pool, str(world_id), zone)
    target = None
    for n in npcs:
        if (n.get("display_name") or n.get("settlement_name") or "").lower().startswith(npc_name.lower()):
            target = n
            break
        if npc_name.lower() in (n.get("display_name") or "").lower():
            target = n
            break

    if not target:
        await update.message.reply_text(get_text("quest_npc_not_found", lang))
        return

    quests = await list_npc_quests(pool, str(target["player_id"]))
    quest = next((q for q in quests if q.get("quest_key") == quest_key), None)
    if not quest:
        await update.message.reply_text(get_text("quest_not_found", lang))
        return

    ok = await start_quest(pool, str(player["id"]), str(quest["id"]))
    if ok:
        await update.message.reply_text(
            get_text("quest_accepted", lang, name=quest.get("name", quest_key)),
        )
    else:
        await update.message.reply_text(get_text("quest_already_active", lang))

"""Guild handlers — create, join, leave, roster, invite."""

from __future__ import annotations

import logging
import re

from telegram import Update
from telegram.ext import ContextTypes

from bot.db.queries.players import get_player_by_telegram_id
from bot.db.queries.game_states import get_active_game, get_settlement_by_id
from bot.db.queries.guilds import (
    get_guild_membership,
    list_guild_members,
    create_guild,
    get_guild_by_name,
    get_pending_invite,
    create_invite,
    accept_invite,
    decline_invite,
    leave_guild,
    get_guild_member_telegram_ids,
)
from bot.utils.display import get_display_name
from bot.i18n import get_text
from bot.handlers.chat import _get_player_by_username

logger = logging.getLogger(__name__)

GUILD_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_\-\s]{2,30}$")
MAX_GUILD_MEMBERS = 50


async def handle_guild(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /guild <subcommand> [args]. /guild [msg] without subcommand goes to guild chat."""
    args = (context.args or [])[:10]
    if not args:
        # /guild without args — show help or guild info
        await _show_guild_help_or_info(update, context)
        return

    sub = args[0].lower()
    if sub == "create":
        await _guild_create(update, context, args[1:])
    elif sub == "invite":
        await _guild_invite(update, context, args[1:])
    elif sub == "accept":
        await _guild_accept(update, context)
    elif sub == "decline":
        await _guild_decline(update, context)
    elif sub == "leave":
        await _guild_leave(update, context)
    elif sub == "roster":
        await _guild_roster(update, context)
    elif sub == "info":
        await _guild_info(update, context)
    else:
        # Could be a guild chat message: /guild Hello everyone
        # Route to guild chat handler
        context.args = args  # Restore full message as args
        from bot.handlers.chat import handle_guild_chat
        await handle_guild_chat(update, context)


async def _show_guild_help_or_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, update.effective_user.id)
    if not player:
        await update.message.reply_text(get_text("free_text_no_game", "en"))
        return

    game_row = await get_active_game(pool, str(player["id"]))
    if not game_row:
        await update.message.reply_text(get_text("free_text_no_game", player.get("language", "en")))
        return

    membership = await get_guild_membership(pool, str(game_row["id"]))
    lang = player.get("language", "en")
    if membership:
        await _guild_info(update, context)
    else:
        await update.message.reply_text(get_text("guild_help", lang))


async def _guild_create(update: Update, context: ContextTypes.DEFAULT_TYPE, args: list) -> None:
    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, update.effective_user.id)
    if not player:
        await update.message.reply_text(get_text("free_text_no_game", "en"))
        return

    game_row = await get_active_game(pool, str(player["id"]))
    if not game_row:
        await update.message.reply_text(get_text("free_text_no_game", player.get("language", "en")))
        return

    if await get_guild_membership(pool, str(game_row["id"])):
        await update.message.reply_text(get_text("guild_already_in", player.get("language", "en")))
        return

    name = " ".join(args).strip() if args else ""
    if not name or not GUILD_NAME_PATTERN.match(name):
        await update.message.reply_text(get_text("guild_name_invalid", player.get("language", "en")))
        return

    world_id = game_row.get("world_id")
    if not world_id:
        await update.message.reply_text(get_text("chat_no_world", player.get("language", "en")))
        return

    existing = await get_guild_by_name(pool, str(world_id), name)
    if existing:
        await update.message.reply_text(get_text("guild_name_taken", player.get("language", "en")))
        return

    guild = await create_guild(pool, str(world_id), name, str(game_row["id"]))
    await update.message.reply_text(
        get_text("guild_created", player.get("language", "en"), name=guild["name"]),
    )


async def _guild_invite(update: Update, context: ContextTypes.DEFAULT_TYPE, args: list) -> None:
    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, update.effective_user.id)
    if not player:
        await update.message.reply_text(get_text("free_text_no_game", "en"))
        return

    game_row = await get_active_game(pool, str(player["id"]))
    if not game_row:
        await update.message.reply_text(get_text("free_text_no_game", player.get("language", "en")))
        return

    membership = await get_guild_membership(pool, str(game_row["id"]))
    if not membership:
        await update.message.reply_text(get_text("chat_no_guild", player.get("language", "en")))
        return

    if membership.get("role") not in ("leader", "officer"):
        await update.message.reply_text(get_text("guild_not_officer", player.get("language", "en")))
        return

    username = args[0] if args else ""
    target_player = await _get_player_by_username(pool, username)
    if not target_player:
        await update.message.reply_text(get_text("guild_invite_not_found", player.get("language", "en")))
        return
    if target_player.get("is_npc"):
        await update.message.reply_text(get_text("guild_invite_npc", player.get("language", "en")))
        return

    target_game = await get_active_game(pool, str(target_player["id"]))
    if not target_game:
        await update.message.reply_text(get_text("guild_invite_no_game", player.get("language", "en")))
        return

    if not target_game.get("world_id") or str(target_game["world_id"]) != str(membership.get("world_id", game_row.get("world_id"))):
        await update.message.reply_text(get_text("guild_invite_wrong_world", player.get("language", "en")))
        return

    existing = await get_guild_membership(pool, str(target_game["id"]))
    if existing:
        await update.message.reply_text(get_text("guild_invite_already_in", player.get("language", "en")))
        return

    inv = await create_invite(
        pool,
        str(membership["guild_id"]),
        str(game_row["id"]),
        str(target_game["id"]),
    )
    inviter_name = get_display_name(game_row=game_row, player_row=player)
    msg = get_text("guild_invite_sent", player.get("language", "en"), name=inviter_name)

    if target_player.get("telegram_id", 0) > 0:
        try:
            lang = target_player.get("language", player.get("language", "en"))
            await context.bot.send_message(
                chat_id=target_player["telegram_id"],
                text=get_text("guild_invite_received", lang,
                    guild=membership.get("guild_name", ""), inviter=inviter_name),
            )
        except Exception as e:
            logger.warning("Guild invite notification failed: %s", e)

    await update.message.reply_text(msg)


async def _guild_accept(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, update.effective_user.id)
    if not player:
        await update.message.reply_text(get_text("free_text_no_game", "en"))
        return

    game_row = await get_active_game(pool, str(player["id"]))
    if not game_row:
        await update.message.reply_text(get_text("free_text_no_game", player.get("language", "en")))
        return

    invite = await get_pending_invite(pool, str(game_row["id"]))
    if not invite:
        await update.message.reply_text(get_text("guild_no_invite", player.get("language", "en")))
        return

    ok = await accept_invite(pool, str(invite["id"]), str(game_row["id"]))
    if ok:
        await update.message.reply_text(
            get_text("guild_joined", player.get("language", "en"), name=invite.get("guild_name", "")),
        )
    else:
        await update.message.reply_text(get_text("guild_invite_expired", player.get("language", "en")))


async def _guild_decline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, update.effective_user.id)
    if not player:
        await update.message.reply_text(get_text("free_text_no_game", "en"))
        return

    game_row = await get_active_game(pool, str(player["id"]))
    if not game_row:
        await update.message.reply_text(get_text("free_text_no_game", player.get("language", "en")))
        return

    invite = await get_pending_invite(pool, str(game_row["id"]))
    if not invite:
        await update.message.reply_text(get_text("guild_no_invite", player.get("language", "en")))
        return

    await decline_invite(pool, str(invite["id"]), str(game_row["id"]))
    await update.message.reply_text(get_text("guild_declined", player.get("language", "en")))


async def _guild_leave(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, update.effective_user.id)
    if not player:
        await update.message.reply_text(get_text("free_text_no_game", "en"))
        return

    game_row = await get_active_game(pool, str(player["id"]))
    if not game_row:
        await update.message.reply_text(get_text("free_text_no_game", player.get("language", "en")))
        return

    ok, msg = await leave_guild(pool, str(game_row["id"]))
    lang = player.get("language", "en")
    if ok:
        await update.message.reply_text(get_text("guild_left", lang))
    elif msg == "leader_must_transfer":
        await update.message.reply_text(get_text("guild_leader_transfer", lang))
    else:
        await update.message.reply_text(get_text("chat_no_guild", lang))


async def _guild_roster(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, update.effective_user.id)
    if not player:
        await update.message.reply_text(get_text("free_text_no_game", "en"))
        return

    game_row = await get_active_game(pool, str(player["id"]))
    if not game_row:
        await update.message.reply_text(get_text("free_text_no_game", player.get("language", "en")))
        return

    membership = await get_guild_membership(pool, str(game_row["id"]))
    if not membership:
        await update.message.reply_text(get_text("chat_no_guild", player.get("language", "en")))
        return

    members = await list_guild_members(pool, str(membership["guild_id"]))
    lines = [f"*{membership.get('guild_name', 'Guild')}* — Roster:\n"]
    for m in members:
        dn = get_display_name(game_row={"display_name": m.get("display_name")}, player_row=m)
        role_emoji = {"leader": "👑", "officer": "⭐", "member": "•"}.get(m.get("role", "member"), "•")
        lines.append(f"  {role_emoji} {dn} — {m.get('settlement_name', '?')}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def _guild_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, update.effective_user.id)
    if not player:
        await update.message.reply_text(get_text("free_text_no_game", "en"))
        return

    game_row = await get_active_game(pool, str(player["id"]))
    if not game_row:
        await update.message.reply_text(get_text("free_text_no_game", player.get("language", "en")))
        return

    membership = await get_guild_membership(pool, str(game_row["id"]))
    if not membership:
        await update.message.reply_text(get_text("chat_no_guild", player.get("language", "en")))
        return

    members = await list_guild_members(pool, str(membership["guild_id"]))
    leader_game = await get_settlement_by_id(pool, str(membership["leader_game_id"]))
    leader_name = get_display_name(game_row=leader_game, player_row=None) if leader_game else "?"

    await update.message.reply_text(
        get_text("guild_info", player.get("language", "en"),
            name=membership.get("guild_name", ""),
            leader=leader_name,
            count=len(members)),
        parse_mode="Markdown",
    )

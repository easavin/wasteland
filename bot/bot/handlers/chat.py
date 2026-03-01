"""Chat handlers — global, zone, guild chat and whisper."""

from __future__ import annotations

import logging
import re
import time

from telegram import Update
from telegram.ext import ContextTypes

from bot.db.queries.players import get_player_by_telegram_id
from bot.db.queries.game_states import get_active_game, get_settlements_in_world, get_settlements_in_zone
from bot.db.queries.chat import insert_chat_message, get_recent_chat
from bot.db.queries.guilds import get_guild_membership
from bot.db.queries.worlds import get_default_world
from bot.utils.display import get_display_name
from bot.i18n import get_text

logger = logging.getLogger(__name__)

CHAT_RATE_SECONDS = 5
CHAT_LOG_LIMIT = 20


async def _get_player_by_username(pool, username: str) -> dict | None:
    """Resolve @username to player (strip @)."""
    clean = username.lstrip("@").strip().lower()
    if not clean:
        return None
    row = await pool.fetchrow(
        "SELECT * FROM players WHERE LOWER(username) = $1",
        clean,
    )
    return dict(row) if row else None


async def handle_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /chat [message] — send to world global chat."""
    pool = context.bot_data["db_pool"]
    user = update.effective_user
    text = " ".join(context.args) if context.args else ""
    player = await get_player_by_telegram_id(pool, user.id)
    if not player:
        await update.message.reply_text(get_text("free_text_no_game", "en"))
        return

    game_row = await get_active_game(pool, str(player["id"]))
    if not game_row:
        await update.message.reply_text(get_text("free_text_no_game", player.get("language", "en")))
        return

    world_id = game_row.get("world_id")
    if not world_id:
        await update.message.reply_text(get_text("chat_no_world", player.get("language", "en")))
        return

    # Rate limit
    last = context.user_data.get("last_chat_at", 0)
    if time.time() - last < CHAT_RATE_SECONDS:
        await update.message.reply_text(get_text("chat_rate_limit", player.get("language", "en")))
        return

    if not text.strip():
        await update.message.reply_text(get_text("chat_empty", player.get("language", "en")))
        return

    lang = player.get("language", "en")
    await insert_chat_message(
        pool,
        world_id=str(world_id),
        sender_game_id=str(game_row["id"]),
        player_id=str(player["id"]),
        text=text.strip(),
        zone=None,
        guild_id=None,
    )
    context.user_data["last_chat_at"] = time.time()

    display = get_display_name(game_row=game_row, player_row=player)
    formatted = f"**{display}**: {text.strip()[:500]}"

    # Broadcast to all in world
    settlements = await get_settlements_in_world(pool, str(world_id))
    sent = 0
    for s in settlements:
        if str(s["player_id"]) == str(player["id"]):
            continue  # Don't send to self
        try:
            await context.bot.send_message(
                chat_id=s["telegram_id"],
                text=formatted,
                parse_mode="Markdown",
            )
            sent += 1
        except Exception as e:
            logger.debug("Chat broadcast failed to %s: %s", s.get("telegram_id"), e)

    await update.message.reply_text(get_text("chat_sent", lang, count=sent))


async def handle_zone_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /zone [message] — send to current zone only."""
    pool = context.bot_data["db_pool"]
    user = update.effective_user
    text = " ".join(context.args) if context.args else ""
    player = await get_player_by_telegram_id(pool, user.id)
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

    last = context.user_data.get("last_zone_chat_at", 0)
    if time.time() - last < CHAT_RATE_SECONDS:
        await update.message.reply_text(get_text("chat_rate_limit", player.get("language", "en")))
        return

    if not text.strip():
        await update.message.reply_text(get_text("chat_empty", player.get("language", "en")))
        return

    lang = player.get("language", "en")
    await insert_chat_message(
        pool,
        world_id=str(world_id),
        sender_game_id=str(game_row["id"]),
        player_id=str(player["id"]),
        text=text.strip(),
        zone=zone,
        guild_id=None,
    )
    context.user_data["last_zone_chat_at"] = time.time()

    display = get_display_name(game_row=game_row, player_row=player)
    formatted = f"**{display}** (Zone {zone}): {text.strip()[:500]}"

    settlements = await get_settlements_in_zone(pool, str(world_id), zone)
    sent = 0
    for s in settlements:
        if str(s["player_id"]) == str(player["id"]):
            continue
        try:
            await context.bot.send_message(
                chat_id=s["telegram_id"],
                text=formatted,
                parse_mode="Markdown",
            )
            sent += 1
        except Exception as e:
            logger.debug("Zone chat broadcast failed: %s", e)

    await update.message.reply_text(get_text("chat_sent", lang, count=sent))


async def handle_guild_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /guild [message] — send to guild members only."""
    pool = context.bot_data["db_pool"]
    user = update.effective_user
    text = " ".join(context.args) if context.args else ""
    player = await get_player_by_telegram_id(pool, user.id)
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

    guild_id = str(membership["guild_id"])
    guild_name = membership.get("guild_name", "Guild")
    world_id = game_row.get("world_id")
    if not world_id:
        await update.message.reply_text(get_text("chat_no_world", player.get("language", "en")))
        return

    last = context.user_data.get("last_guild_chat_at", 0)
    if time.time() - last < CHAT_RATE_SECONDS:
        await update.message.reply_text(get_text("chat_rate_limit", player.get("language", "en")))
        return

    if not text.strip():
        await update.message.reply_text(get_text("chat_empty", player.get("language", "en")))
        return

    lang = player.get("language", "en")
    await insert_chat_message(
        pool,
        world_id=str(world_id),
        sender_game_id=str(game_row["id"]),
        player_id=str(player["id"]),
        text=text.strip(),
        zone=None,
        guild_id=guild_id,
    )
    context.user_data["last_guild_chat_at"] = time.time()

    display = get_display_name(game_row=game_row, player_row=player)
    formatted = f"**{display}** [{guild_name}]: {text.strip()[:500]}"

    from bot.db.queries.guilds import get_guild_member_telegram_ids
    members = await get_guild_member_telegram_ids(pool, guild_id)
    sent = 0
    for tg_id in members:
        if tg_id == user.id:
            continue
        try:
            await context.bot.send_message(
                chat_id=tg_id,
                text=formatted,
                parse_mode="Markdown",
            )
            sent += 1
        except Exception as e:
            logger.debug("Guild chat broadcast failed: %s", e)

    await update.message.reply_text(get_text("chat_sent", lang, count=sent))




async def handle_whisper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /whisper @username message — direct message to another player."""
    pool = context.bot_data["db_pool"]
    user = update.effective_user
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text(
            get_text("whisper_usage", "en"),
        )
        return

    target_username = args[0]
    message = " ".join(args[1:])
    player = await get_player_by_telegram_id(pool, user.id)
    if not player:
        await update.message.reply_text(get_text("free_text_no_game", "en"))
        return

    game_row = await get_active_game(pool, str(player["id"]))
    if not game_row:
        await update.message.reply_text(get_text("free_text_no_game", player.get("language", "en")))
        return

    target_player = await _get_player_by_username(pool, target_username)
    if not target_player:
        await update.message.reply_text(get_text("whisper_not_found", player.get("language", "en")))
        return
    if target_player.get("is_npc"):
        await update.message.reply_text(get_text("whisper_npc", player.get("language", "en")))
        return

    target_game = await get_active_game(pool, str(target_player["id"]))
    if not target_game:
        await update.message.reply_text(get_text("whisper_no_game", player.get("language", "en")))
        return

    display = get_display_name(game_row=game_row, player_row=player)
    formatted = f"_Whisper from **{display}**_: {message[:500]}"

    try:
        await context.bot.send_message(
            chat_id=target_player["telegram_id"],
            text=formatted,
            parse_mode="Markdown",
        )
        await update.message.reply_text(get_text("whisper_sent", player.get("language", "en")))
    except Exception as e:
        logger.warning("Whisper failed: %s", e)
        await update.message.reply_text(get_text("whisper_failed", player.get("language", "en")))


async def handle_chatlog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /chatlog — show recent global chat messages."""
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
    if not world_id:
        await update.message.reply_text(get_text("chat_no_world", player.get("language", "en")))
        return

    messages = await get_recent_chat(
        pool,
        str(world_id),
        zone=None,
        guild_id=None,
        limit=CHAT_LOG_LIMIT,
    )
    if not messages:
        await update.message.reply_text(get_text("chat_log_empty", player.get("language", "en")))
        return

    lines = []
    for m in messages:
        dn = m.get("display_name") or m.get("first_name") or (f"@{m['username']}" if m.get("username") else "?")
        lines.append(f"**{dn}**: {m.get('text', '')[:100]}")

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
    )

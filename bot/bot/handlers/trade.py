"""Trade / marketplace handlers."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.db.queries.players import get_player_by_telegram_id
from bot.db.queries.game_states import get_active_game
from bot.db.queries.trade import (
    list_market_offers,
    create_offer,
    get_offer,
    execute_trade,
    cancel_offer,
    VALID_RESOURCES,
)
from bot.handlers.chat import _get_player_by_username
from bot.i18n import get_text

logger = logging.getLogger(__name__)


async def handle_market(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route /market to list, sell, buy, cancel."""
    args = context.args or []
    if args and args[0].lower() == "list":
        await handle_market_list(update, context)
        return
    if args and args[0].lower() == "sell":
        context.args = args[1:]
        await handle_market_sell(update, context)
        return
    if args and args[0].lower() == "buy":
        context.args = args[1:]
        await handle_market_buy(update, context)
        return
    if args and args[0].lower() == "cancel":
        context.args = args[1:]
        await handle_market_cancel(update, context)
        return
    await handle_market_list(update, context)


async def handle_market_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /market list."""
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

    offers = await list_market_offers(pool, str(world_id))
    lang = player.get("language", "en")
    if not offers:
        await update.message.reply_text(get_text("market_empty", lang))
        return

    lines = [get_text("market_list_header", lang) + "\n"]
    for o in offers[:15]:
        sid = str(o["id"])[:8]
        lines.append(
            f"`{sid}` {o.get('seller_name', '?')}: {o['amount']} {o['resource']} for {o['price_gold']} 💰"
        )
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def handle_market_sell(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /market sell <resource> <amount> <price>."""
    args = context.args or []  # May be set by handle_market
    if len(args) < 3:
        await update.message.reply_text(get_text("market_sell_usage", "en"))
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

    resource = args[0].lower()
    if resource not in ("food", "scrap"):
        await update.message.reply_text(get_text("market_invalid_resource", player.get("language", "en")))
        return

    try:
        amount = int(args[1])
        price = int(args[2])
    except ValueError:
        await update.message.reply_text(get_text("market_invalid_numbers", player.get("language", "en")))
        return

    if amount < 1 or price < 0:
        await update.message.reply_text(get_text("market_invalid_numbers", player.get("language", "en")))
        return

    current = int(game_row.get(resource, 0))
    if current < amount:
        await update.message.reply_text(
            get_text("market_insufficient", player.get("language", "en"), resource=resource, have=current),
        )
        return

    world_id = game_row.get("world_id")
    if not world_id:
        await update.message.reply_text(get_text("chat_no_world", player.get("language", "en")))
        return

    offer = await create_offer(
        pool, str(world_id), str(game_row["id"]),
        resource, amount, price,
        buyer_game_id=None,
    )

    await update.message.reply_text(
        get_text("market_sold", player.get("language", "en"),
            amount=amount, resource=resource, price=price, id=str(offer["id"])[:8]),
    )


async def handle_market_buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /market buy <offer_id>."""
    args = context.args or []
    if not args:
        await update.message.reply_text(get_text("market_buy_usage", "en"))
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

    offer_id = args[0]
    if len(offer_id) == 8:
        row = await pool.fetchrow(
            "SELECT id FROM trade_offers WHERE id::text LIKE $1 AND status = 'open' LIMIT 1",
            offer_id + "%",
        )
        if row:
            offer_id = str(row["id"])

    ok, err = await execute_trade(pool, offer_id, str(game_row["id"]))
    lang = player.get("language", "en")
    if ok:
        offer = await get_offer(pool, offer_id)
        await update.message.reply_text(
            get_text("market_bought", lang,
                amount=offer["amount"], resource=offer["resource"], price=offer["price_gold"]),
        )
    else:
        msg = {"offer_not_found": "market_offer_gone", "not_enough_gold": "market_no_gold",
               "seller_insufficient": "market_seller_empty", "offer_not_for_you": "market_not_yours"}
        await update.message.reply_text(get_text(msg.get(err, "market_error"), lang))


async def handle_market_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /market cancel <offer_id>."""
    args = context.args or []
    if not args:
        await update.message.reply_text(get_text("market_cancel_usage", "en"))
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

    offer_id = args[0]
    ok = await cancel_offer(pool, offer_id, str(game_row["id"]))
    if ok:
        await update.message.reply_text(get_text("market_cancelled", player.get("language", "en")))
    else:
        await update.message.reply_text(get_text("market_cancel_failed", player.get("language", "en")))


async def handle_trade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route /trade to direct offer or accept."""
    args = context.args or []
    if args and args[0].lower() == "accept":
        await handle_trade_accept(update, context)
        return
    await handle_trade_direct(update, context)


async def handle_trade_accept(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /trade accept <offer_id>."""
    args = (context.args or [])[1:]  # Skip "accept"
    if not args:
        await update.message.reply_text(get_text("trade_accept_usage", "en"))
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

    offer_id = args[0]
    if len(offer_id) == 8:
        row = await pool.fetchrow(
            "SELECT id FROM trade_offers WHERE id::text LIKE $1 AND status = 'open' LIMIT 1",
            offer_id + "%",
        )
        if row:
            offer_id = str(row["id"])

    ok, err = await execute_trade(pool, offer_id, str(game_row["id"]))
    lang = player.get("language", "en")
    if ok:
        offer = await get_offer(pool, offer_id)
        await update.message.reply_text(
            get_text("market_bought", lang,
                amount=offer["amount"], resource=offer["resource"], price=offer["price_gold"]),
        )
    else:
        msg = {"offer_not_found": "market_offer_gone", "not_enough_gold": "market_no_gold",
               "seller_insufficient": "market_seller_empty", "offer_not_for_you": "market_not_yours"}
        await update.message.reply_text(get_text(msg.get(err, "market_error"), lang))


async def handle_trade_direct(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /trade @username <resource> <amount> <price>."""
    args = context.args or []
    if len(args) < 4:
        await update.message.reply_text(get_text("trade_direct_usage", "en"))
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
        await update.message.reply_text(get_text("trade_target_not_found", player.get("language", "en")))
        return

    target_game = await get_active_game(pool, str(target_player["id"]))
    if not target_game:
        await update.message.reply_text(get_text("trade_target_no_game", player.get("language", "en")))
        return

    resource = args[1].lower()
    if resource not in ("food", "scrap"):
        await update.message.reply_text(get_text("market_invalid_resource", player.get("language", "en")))
        return

    try:
        amount = int(args[2])
        price = int(args[3])
    except ValueError:
        await update.message.reply_text(get_text("market_invalid_numbers", player.get("language", "en")))
        return

    if amount < 1 or price < 0:
        await update.message.reply_text(get_text("market_invalid_numbers", player.get("language", "en")))
        return

    current = int(game_row.get(resource, 0))
    if current < amount:
        await update.message.reply_text(
            get_text("market_insufficient", player.get("language", "en"), resource=resource, have=current),
        )
        return

    world_id = game_row.get("world_id")
    if not world_id or str(target_game.get("world_id")) != str(world_id):
        await update.message.reply_text(get_text("trade_same_world", player.get("language", "en")))
        return

    offer = await create_offer(
        pool, str(world_id), str(game_row["id"]),
        resource, amount, price,
        buyer_game_id=str(target_game["id"]),
    )

    seller_name = game_row.get("display_name") or player.get("first_name") or "?"
    try:
        await context.bot.send_message(
            chat_id=target_player["telegram_id"],
            text=get_text("trade_offer_received", target_player.get("language", "en"),
                seller=seller_name, amount=amount, resource=resource, price=price, id=str(offer["id"])[:8]),
        )
    except Exception as e:
        logger.warning("Trade notification failed: %s", e)

    await update.message.reply_text(
        get_text("trade_offer_sent", player.get("language", "en")),
    )

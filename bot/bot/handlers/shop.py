"""Handler for /shop command — spend gold on special purchases."""

from __future__ import annotations

import json
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from bot.db.queries.players import get_player_by_telegram_id
from bot.db.queries.game_states import get_active_game, update_game_state
from bot.engine.game_state import GameState
from bot.i18n import get_text

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shop catalog
# ---------------------------------------------------------------------------
# Each item: id, name (en/ru), description (en/ru), gold_cost, effect (callable)
# Effects mutate state in-place and return a short result message key.
# ---------------------------------------------------------------------------

SHOP_ITEMS: dict[str, dict] = {
    "emergency_food": {
        "name": {"en": "Emergency Rations", "ru": "Экстренный паёк"},
        "description": {
            "en": "Buy 40 food for your starving settlement.",
            "ru": "Купить 40 еды для голодающего поселения.",
        },
        "gold_cost": 20,
        "emoji": "🌾",
    },
    "hire_mercenaries": {
        "name": {"en": "Hire Mercenaries", "ru": "Нанять наёмников"},
        "description": {
            "en": "Hired guns boost defense by 25 and morale by 5.",
            "ru": "Наёмники усиливают оборону на 25 и мораль на 5.",
        },
        "gold_cost": 15,
        "emoji": "⚔️",
    },
    "faction_gift": {
        "name": {"en": "Faction Gift", "ru": "Подарок фракции"},
        "description": {
            "en": "Send gifts to all factions (+10 rep each).",
            "ru": "Отправить подарки всем фракциям (+10 репутации каждой).",
        },
        "gold_cost": 15,
        "emoji": "🎁",
    },
    "recruit_settlers": {
        "name": {"en": "Recruit Settlers", "ru": "Набрать поселенцев"},
        "description": {
            "en": "Word spreads of your gold. +8 population.",
            "ru": "Слухи о вашем золоте привлекают людей. +8 населения.",
        },
        "gold_cost": 12,
        "emoji": "👥",
    },
    "scrap_shipment": {
        "name": {"en": "Scrap Shipment", "ru": "Поставка хлама"},
        "description": {
            "en": "Buy a bulk shipment of building materials. +50 scrap.",
            "ru": "Закупка стройматериалов оптом. +50 хлама.",
        },
        "gold_cost": 18,
        "emoji": "🔩",
    },
    "skill_respec": {
        "name": {"en": "Skill Respec", "ru": "Сброс навыков"},
        "description": {
            "en": "Reset all skills and refund all spent skill points.",
            "ru": "Сбросить все навыки и вернуть все потраченные очки.",
        },
        "gold_cost": 25,
        "emoji": "🔄",
    },
}


def _apply_purchase(state: GameState, item_id: str) -> None:
    """Apply the effect of a shop purchase to game state (mutates in-place)."""
    if item_id == "emergency_food":
        state.food += 40
    elif item_id == "hire_mercenaries":
        state.defense = min(100, state.defense + 25)
        state.morale = min(100, state.morale + 5)
    elif item_id == "faction_gift":
        state.raiders_rep = min(100, state.raiders_rep + 10)
        state.traders_rep = min(100, state.traders_rep + 10)
        state.remnants_rep = min(100, state.remnants_rep + 10)
    elif item_id == "recruit_settlers":
        state.population += 8
    elif item_id == "scrap_shipment":
        state.scrap += 50
    elif item_id == "skill_respec":
        # Refund all spent points
        total_spent = sum(state.skills.values())
        state.skill_points += total_spent
        state.skills = {}


# ---------------------------------------------------------------------------
# Command handler
# ---------------------------------------------------------------------------

async def handle_shop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/shop — display the gold shop."""
    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, update.effective_user.id)
    if not player:
        await update.message.reply_text(get_text("free_text_no_game", "en"))
        return

    lang = player.get("language", "en")
    game_row = await get_active_game(pool, str(player["id"]))
    if not game_row:
        await update.message.reply_text(get_text("free_text_no_game", lang))
        return

    state = GameState.from_db_row(game_row)
    text = _format_shop(state, lang)
    keyboard = _shop_keyboard(state, lang)

    try:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")
    except BadRequest:
        await update.message.reply_text(text, reply_markup=keyboard)


async def handle_shop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard callback for shop purchases (shop:item_id)."""
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if not data.startswith("shop:"):
        return

    item_id = data[5:]  # e.g. "shop:emergency_food"
    if item_id not in SHOP_ITEMS:
        return

    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, query.from_user.id)
    if not player:
        return

    lang = player.get("language", "en")
    player_id = str(player["id"])

    game_row = await get_active_game(pool, player_id)
    if not game_row:
        return

    state = GameState.from_db_row(game_row)
    item = SHOP_ITEMS[item_id]
    cost = item["gold_cost"]

    # Check gold
    if state.gold < cost:
        error_text = get_text("shop_not_enough_gold", lang, cost=cost, gold=state.gold)
        await query.message.reply_text(error_text)
        return

    # Deduct gold and apply effect
    state.gold -= cost
    _apply_purchase(state, item_id)

    # Persist changes
    update_fields = {
        "gold": state.gold,
        "food": state.food,
        "scrap": state.scrap,
        "population": state.population,
        "morale": state.morale,
        "defense": state.defense,
        "raiders_rep": state.raiders_rep,
        "traders_rep": state.traders_rep,
        "remnants_rep": state.remnants_rep,
    }
    # Include skills if respec was used
    if item_id == "skill_respec":
        update_fields["skills"] = state.skills
        update_fields["skill_points"] = state.skill_points

    await update_game_state(pool, state.id, **update_fields)

    # Confirm purchase
    item_name = item["name"].get(lang, item["name"]["en"])
    confirm = get_text("shop_purchased", lang, item=item_name, cost=cost, gold=state.gold)
    await query.message.reply_text(confirm, parse_mode="Markdown")


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def _format_shop(state: GameState, lang: str) -> str:
    """Build the shop display text."""
    lines = [get_text("shop_header", lang, gold=state.gold)]
    lines.append("")

    for item_id, item in SHOP_ITEMS.items():
        name = item["name"].get(lang, item["name"]["en"])
        desc = item["description"].get(lang, item["description"]["en"])
        emoji = item["emoji"]
        cost = item["gold_cost"]
        affordable = "✅" if state.gold >= cost else "❌"

        lines.append(f"{emoji} *{name}* — {cost} 💰 {affordable}")
        lines.append(f"    _{desc}_")
        lines.append("")

    return "\n".join(lines)


def _shop_keyboard(state: GameState, lang: str) -> InlineKeyboardMarkup | None:
    """Build keyboard with buttons for affordable items."""
    buttons = []
    for item_id, item in SHOP_ITEMS.items():
        if state.gold < item["gold_cost"]:
            continue
        name = item["name"].get(lang, item["name"]["en"])
        emoji = item["emoji"]
        cost = item["gold_cost"]
        buttons.append([
            InlineKeyboardButton(
                f"{emoji} {name} ({cost} 💰)",
                callback_data=f"shop:{item_id}",
            ),
        ])

    if not buttons:
        return None
    return InlineKeyboardMarkup(buttons)

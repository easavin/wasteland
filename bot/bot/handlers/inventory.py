"""Handlers for /inventory and /use commands — item management."""

from __future__ import annotations

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from bot.db.queries.players import get_player_by_telegram_id
from bot.db.queries.game_states import get_active_game, update_game_state
from bot.engine.game_state import GameState
from bot.engine.items import (
    ITEMS,
    MAX_EQUIPPED,
    get_item,
    get_item_name,
    get_rarity_emoji,
    get_rarity_label,
    get_equipped_bonuses,
    add_item_to_inventory,
    remove_item_from_inventory,
    equip_item,
    get_inventory_display,
    format_effect_description,
)
from bot.i18n import get_text

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# /inventory command
# ---------------------------------------------------------------------------

async def handle_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/inventory — display all items with equip/use buttons."""
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
    text = _format_inventory_page(state, lang)
    keyboard = _inventory_keyboard(state.inventory, lang)

    try:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")
    except BadRequest:
        await update.message.reply_text(text, reply_markup=keyboard)


# ---------------------------------------------------------------------------
# /use <item_id> command
# ---------------------------------------------------------------------------

async def handle_use(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/use <item_id> — consume a consumable item and apply its effects."""
    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, update.effective_user.id)
    if not player:
        await update.message.reply_text(get_text("free_text_no_game", "en"))
        return

    lang = player.get("language", "en")

    # Parse item_id from command arguments.
    args = context.args
    if not args:
        await update.message.reply_text(get_text("use_usage", lang))
        return

    item_id = args[0].lower().strip()
    game_row = await get_active_game(pool, str(player["id"]))
    if not game_row:
        await update.message.reply_text(get_text("free_text_no_game", lang))
        return

    state = GameState.from_db_row(game_row)
    result_text = _apply_consumable(state, item_id, lang)

    if result_text is None:
        # Success — persist all changed fields.
        state.clamp_resources()
        await update_game_state(
            pool, state.id,
            food=state.food,
            scrap=state.scrap,
            gold=state.gold,
            population=state.population,
            morale=state.morale,
            defense=state.defense,
            xp=state.xp,
            inventory=state.inventory,
        )
        item_name = get_item_name(item_id, lang)
        effect_desc = format_effect_description(ITEMS[item_id]["effect"], lang)
        confirm = get_text(
            "use_success", lang,
            item=item_name,
            effect=effect_desc,
        )
        try:
            await update.message.reply_text(confirm, parse_mode="Markdown")
        except BadRequest:
            await update.message.reply_text(confirm)
    else:
        # Error message.
        await update.message.reply_text(result_text)


# ---------------------------------------------------------------------------
# Callback handler for inline buttons (inv:equip:<id> / inv:use:<id>)
# ---------------------------------------------------------------------------

async def handle_inventory_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle ``inv:equip:<item_id>`` and ``inv:use:<item_id>`` callbacks."""
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if not data.startswith("inv:"):
        return

    parts = data.split(":", 2)
    if len(parts) < 3:
        return

    action = parts[1]   # "equip" or "use"
    item_id = parts[2]

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

    if action == "equip":
        new_inv, success = equip_item(state.inventory, item_id)
        state.inventory = new_inv

        if not success:
            error = get_text("equip_failed", lang, max=MAX_EQUIPPED)
            await query.message.reply_text(error)
            return

        await update_game_state(pool, state.id, inventory=state.inventory)

        item_name = get_item_name(item_id, lang)
        # Determine whether we just equipped or unequipped.
        entry = next((e for e in state.inventory if e["id"] == item_id), None)
        if entry and entry.get("equipped"):
            msg = get_text("equip_on", lang, item=item_name)
        else:
            msg = get_text("equip_off", lang, item=item_name)
        await query.message.reply_text(msg, parse_mode="Markdown")

    elif action == "use":
        result_text = _apply_consumable(state, item_id, lang)
        if result_text is None:
            state.clamp_resources()
            await update_game_state(
                pool, state.id,
                food=state.food,
                scrap=state.scrap,
                gold=state.gold,
                population=state.population,
                morale=state.morale,
                defense=state.defense,
                xp=state.xp,
                inventory=state.inventory,
            )
            item_name = get_item_name(item_id, lang)
            effect_desc = format_effect_description(ITEMS[item_id]["effect"], lang)
            confirm = get_text("use_success", lang, item=item_name, effect=effect_desc)
            try:
                await query.message.reply_text(confirm, parse_mode="Markdown")
            except BadRequest:
                await query.message.reply_text(confirm)
        else:
            await query.message.reply_text(result_text)

    # Show updated inventory after action.
    game_row = await get_active_game(pool, player_id)
    if game_row:
        state = GameState.from_db_row(game_row)
        text = _format_inventory_page(state, lang)
        keyboard = _inventory_keyboard(state.inventory, lang)
        try:
            await query.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")
        except BadRequest:
            await query.message.reply_text(text, reply_markup=keyboard)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _apply_consumable(state: GameState, item_id: str, lang: str) -> str | None:
    """Use a consumable item, mutating *state* in-place.

    Returns ``None`` on success, or an error message string on failure.
    """
    spec = get_item(item_id)
    if spec is None:
        return get_text("use_unknown_item", lang)

    if spec["type"] != "consumable":
        return get_text("use_not_consumable", lang)

    # Check the player actually has the item.
    entry = next((e for e in state.inventory if e["id"] == item_id), None)
    if entry is None or entry.get("qty", 0) <= 0:
        return get_text("use_not_in_inventory", lang)

    # Apply effects to game state.
    effect = spec["effect"]
    for key, value in effect.items():
        if key == "food":
            state.food += value
        elif key == "scrap":
            state.scrap += value
        elif key == "gold":
            state.gold += value
        elif key == "population":
            state.population += value
        elif key == "morale":
            state.morale += value
        elif key == "defense":
            state.defense += value
        elif key == "xp":
            state.xp += value
        elif key == "building_cost_reduce_next":
            # Store as an active effect for the next build action.
            state.active_effects.append({
                "type": "building_cost_reduce_pct",
                "value": value,
                "turns_left": -1,  # consumed on next build
            })
        # Other passive-only keys are ignored for consumables.

    # Remove one from inventory.
    state.inventory = remove_item_from_inventory(state.inventory, item_id, 1)
    return None  # success


def _format_inventory_page(state: GameState, lang: str) -> str:
    """Build the inventory display text."""
    header = get_text("inventory_header", lang)
    body = get_inventory_display(state.inventory, lang)

    # Show equipped bonuses summary if any.
    bonuses = get_equipped_bonuses(state.inventory)
    bonus_line = ""
    if bonuses:
        parts = []
        for key, val in bonuses.items():
            parts.append(f"+{val} {key}")
        if lang == "ru":
            bonus_line = "\n🔧 *Бонусы снаряжения:* " + ", ".join(parts)
        else:
            bonus_line = "\n🔧 *Equipment bonuses:* " + ", ".join(parts)

    return f"{header}\n\n{body}{bonus_line}"


def _inventory_keyboard(
    inventory: list[dict],
    lang: str,
) -> InlineKeyboardMarkup | None:
    """Build inline keyboard with equip/unequip and use buttons."""
    if not inventory:
        return None

    buttons: list[list[InlineKeyboardButton]] = []

    for entry in inventory:
        item_id = entry["id"]
        spec = ITEMS.get(item_id)
        if spec is None:
            continue

        name = spec["name"].get(lang, spec["name"]["en"])
        emoji = get_rarity_emoji(spec["rarity"])

        if spec["type"] == "passive":
            if entry.get("equipped"):
                if lang == "ru":
                    label = f"{emoji} {name} — Снять"
                else:
                    label = f"{emoji} {name} — Unequip"
            else:
                if lang == "ru":
                    label = f"{emoji} {name} — Надеть"
                else:
                    label = f"{emoji} {name} — Equip"
            buttons.append([
                InlineKeyboardButton(label, callback_data=f"inv:equip:{item_id}"),
            ])
        else:
            qty = entry.get("qty", 1)
            if lang == "ru":
                label = f"{emoji} {name} x{qty} — Использовать"
            else:
                label = f"{emoji} {name} x{qty} — Use"
            buttons.append([
                InlineKeyboardButton(label, callback_data=f"inv:use:{item_id}"),
            ])

    if not buttons:
        return None
    return InlineKeyboardMarkup(buttons)

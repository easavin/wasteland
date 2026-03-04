"""Handler for /codex command — browse discovered lore entries."""

from __future__ import annotations

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from bot.db.queries.players import get_player_by_telegram_id
from bot.db.queries.game_states import get_active_game
from bot.engine.game_state import GameState
from bot.engine.codex import (
    CODEX_ENTRIES,
    CATEGORIES,
    CATEGORY_EMOJI,
    get_category_emoji,
)
from bot.i18n import get_text

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# /codex command — show categories overview
# ---------------------------------------------------------------------------

async def handle_codex(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/codex — show codex overview with category buttons."""
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
    text = _format_codex_overview(state.codex, lang)
    keyboard = _category_keyboard(lang)

    try:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")
    except BadRequest:
        await update.message.reply_text(text, reply_markup=keyboard)


# ---------------------------------------------------------------------------
# Callback handler for codex:<category> and codex:entry:<id>
# ---------------------------------------------------------------------------

async def handle_codex_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle codex: callbacks."""
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if not data.startswith("codex:"):
        return

    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, query.from_user.id)
    if not player:
        return

    lang = player.get("language", "en")
    game_row = await get_active_game(pool, str(player["id"]))
    if not game_row:
        return

    state = GameState.from_db_row(game_row)

    parts = data.split(":", 2)

    if len(parts) == 2:
        # codex:<category>
        category = parts[1]
        if category == "back":
            text = _format_codex_overview(state.codex, lang)
            keyboard = _category_keyboard(lang)
        elif category in CATEGORIES:
            text = _format_category_page(state.codex, category, lang)
            keyboard = _entry_keyboard(state.codex, category, lang)
        else:
            return
    elif len(parts) == 3 and parts[1] == "entry":
        # codex:entry:<entry_id>
        entry_id = parts[2]
        if entry_id not in CODEX_ENTRIES:
            return
        if entry_id not in state.codex:
            return  # not discovered
        text = _format_entry_detail(entry_id, lang)
        entry = CODEX_ENTRIES[entry_id]
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "< " + (_back_label(lang)),
                callback_data=f"codex:{entry['category']}",
            ),
        ]])
    else:
        return

    try:
        await query.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")
    except BadRequest:
        await query.message.reply_text(text, reply_markup=keyboard)


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def _format_codex_overview(discovered: list[str], lang: str) -> str:
    """Codex main page — categories with discovery counts."""
    if lang == "ru":
        header = "📖 *Кодекс Пустоши*"
        total_label = "Всего открыто"
    else:
        header = "📖 *Wasteland Codex*"
        total_label = "Total discovered"

    lines = [header, ""]

    total_discovered = len(discovered)
    total_entries = len(CODEX_ENTRIES)
    lines.append(f"{total_label}: {total_discovered}/{total_entries}")
    lines.append("")

    cat_names = {
        "creatures": {"en": "Creatures", "ru": "Существа"},
        "locations": {"en": "Locations", "ru": "Локации"},
        "tech": {"en": "Technology", "ru": "Технологии"},
        "history": {"en": "History", "ru": "История"},
        "factions": {"en": "Factions", "ru": "Фракции"},
    }

    for cat in CATEGORIES:
        emoji = get_category_emoji(cat)
        name = cat_names.get(cat, {}).get(lang, cat.title())
        cat_total = sum(1 for e in CODEX_ENTRIES.values() if e["category"] == cat)
        cat_found = sum(1 for eid in discovered if CODEX_ENTRIES.get(eid, {}).get("category") == cat)
        lines.append(f"{emoji} *{name}*: {cat_found}/{cat_total}")

    return "\n".join(lines)


def _format_category_page(discovered: list[str], category: str, lang: str) -> str:
    """List entries in a category — discovered ones are named, others are ???."""
    emoji = get_category_emoji(category)
    cat_names = {
        "creatures": {"en": "Creatures", "ru": "Существа"},
        "locations": {"en": "Locations", "ru": "Локации"},
        "tech": {"en": "Technology", "ru": "Технологии"},
        "history": {"en": "History", "ru": "История"},
        "factions": {"en": "Factions", "ru": "Фракции"},
    }
    cat_name = cat_names.get(category, {}).get(lang, category.title())
    header = f"{emoji} *{cat_name}*"

    lines = [header, ""]

    entries = [(eid, e) for eid, e in CODEX_ENTRIES.items() if e["category"] == category]
    for eid, entry in entries:
        if eid in discovered:
            name = entry["name"].get(lang, entry["name"]["en"])
            rarity = entry.get("rarity", "common")
            rarity_emoji = {"common": "⚪", "uncommon": "🟢", "rare": "🔵", "legendary": "🟡"}.get(rarity, "⚪")
            lines.append(f"{rarity_emoji} {name}")
        else:
            lines.append("❓ ???")

    return "\n".join(lines)


def _format_entry_detail(entry_id: str, lang: str) -> str:
    """Show a single codex entry with lore text."""
    entry = CODEX_ENTRIES[entry_id]
    emoji = get_category_emoji(entry["category"])
    name = entry["name"].get(lang, entry["name"]["en"])
    lore = entry["lore"].get(lang, entry["lore"]["en"])
    rarity = entry.get("rarity", "common")
    rarity_labels = {
        "common": {"en": "Common", "ru": "Обычная"},
        "uncommon": {"en": "Uncommon", "ru": "Необычная"},
        "rare": {"en": "Rare", "ru": "Редкая"},
        "legendary": {"en": "Legendary", "ru": "Легендарная"},
    }
    rarity_label = rarity_labels.get(rarity, {}).get(lang, rarity.title())

    return f"{emoji} *{name}* ({rarity_label})\n\n_{lore}_"


def _category_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Keyboard with one button per category."""
    cat_names = {
        "creatures": {"en": "Creatures", "ru": "Существа"},
        "locations": {"en": "Locations", "ru": "Локации"},
        "tech": {"en": "Technology", "ru": "Технологии"},
        "history": {"en": "History", "ru": "История"},
        "factions": {"en": "Factions", "ru": "Фракции"},
    }
    buttons = []
    for cat in CATEGORIES:
        emoji = get_category_emoji(cat)
        name = cat_names.get(cat, {}).get(lang, cat.title())
        buttons.append([InlineKeyboardButton(
            f"{emoji} {name}",
            callback_data=f"codex:{cat}",
        )])
    return InlineKeyboardMarkup(buttons)


def _entry_keyboard(discovered: list[str], category: str, lang: str) -> InlineKeyboardMarkup:
    """Keyboard with buttons for discovered entries in a category + back."""
    buttons = []
    entries = [(eid, e) for eid, e in CODEX_ENTRIES.items() if e["category"] == category]
    for eid, entry in entries:
        if eid in discovered:
            name = entry["name"].get(lang, entry["name"]["en"])
            buttons.append([InlineKeyboardButton(
                name,
                callback_data=f"codex:entry:{eid}",
            )])

    buttons.append([InlineKeyboardButton(
        "< " + _back_label(lang),
        callback_data="codex:back",
    )])
    return InlineKeyboardMarkup(buttons)


def _back_label(lang: str) -> str:
    return "Назад" if lang == "ru" else "Back"

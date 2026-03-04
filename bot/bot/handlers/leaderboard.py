"""Handler for /top command — weekly leaderboards by category."""

from __future__ import annotations

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import ContextTypes

import asyncpg

from bot.db.queries.players import get_player_by_telegram_id
from bot.db.queries.game_states import get_active_game

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Leaderboard categories
# ---------------------------------------------------------------------------

CATEGORIES: dict[str, dict] = {
    "strongest": {
        "emoji": "\U0001f3c6",  # trophy
        "label": {"en": "Strongest", "ru": "\u0421\u0438\u043b\u044c\u043d\u0435\u0439\u0448\u0438\u0435"},
        "order_by": "gs.level DESC, gs.xp DESC",
        "value_fmt": {"en": "Level {level} ({xp:,} XP)", "ru": "\u0423\u0440\u043e\u0432\u0435\u043d\u044c {level} ({xp:,} XP)"},
        "value_keys": ("level", "xp"),
    },
    "richest": {
        "emoji": "\U0001f4b0",  # money bag
        "label": {"en": "Richest", "ru": "\u0411\u043e\u0433\u0430\u0442\u0435\u0439\u0448\u0438\u0435"},
        "order_by": "gs.gold DESC",
        "value_fmt": {"en": "{gold:,} gold", "ru": "{gold:,} \u0437\u043e\u043b\u043e\u0442\u0430"},
        "value_keys": ("gold",),
    },
    "scholar": {
        "emoji": "\U0001f4d6",  # open book
        "label": {"en": "Scholar", "ru": "\u042d\u0440\u0443\u0434\u0438\u0442\u044b"},
        "order_by": "jsonb_array_length(gs.codex) DESC",
        "value_fmt": {"en": "{codex_count} entries", "ru": "{codex_count} \u0437\u0430\u043f\u0438\u0441\u0435\u0439"},
        "value_keys": ("codex_count",),
    },
}

DEFAULT_CATEGORY = "strongest"


# ---------------------------------------------------------------------------
# Database queries
# ---------------------------------------------------------------------------

async def get_leaderboard(
    pool: asyncpg.Pool,
    category: str,
    world_id: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """Return top players for a given category.

    Each entry has: rank, display_name, level, xp, gold, codex_count.
    """
    cat = CATEGORIES.get(category)
    if not cat:
        return []

    order_by = cat["order_by"]

    if world_id:
        query = f"""
            SELECT
                gs.display_name,
                gs.level,
                gs.xp,
                gs.gold,
                jsonb_array_length(gs.codex) AS codex_count,
                gs.player_id
            FROM game_states gs
            JOIN players p ON p.id = gs.player_id
            WHERE gs.status = 'active'
              AND gs.world_id = $1
              AND p.is_npc = FALSE
              AND p.is_banned = FALSE
            ORDER BY {order_by}
            LIMIT $2
        """
        rows = await pool.fetch(query, world_id, limit)
    else:
        query = f"""
            SELECT
                gs.display_name,
                gs.level,
                gs.xp,
                gs.gold,
                jsonb_array_length(gs.codex) AS codex_count,
                gs.player_id
            FROM game_states gs
            JOIN players p ON p.id = gs.player_id
            WHERE gs.status = 'active'
              AND p.is_npc = FALSE
              AND p.is_banned = FALSE
            ORDER BY {order_by}
            LIMIT $1
        """
        rows = await pool.fetch(query, limit)

    result = []
    for idx, row in enumerate(rows, start=1):
        result.append({
            "rank": idx,
            "display_name": row["display_name"] or "???",
            "level": row["level"],
            "xp": row["xp"],
            "gold": row["gold"],
            "codex_count": row["codex_count"],
            "player_id": str(row["player_id"]),
        })
    return result


async def get_player_rank(
    pool: asyncpg.Pool,
    player_id: str,
    category: str,
    world_id: str | None = None,
) -> dict | None:
    """Return the requesting player's rank + values for a category.

    Returns dict with rank, display_name, and value fields, or None.
    """
    cat = CATEGORIES.get(category)
    if not cat:
        return None

    order_by = cat["order_by"]

    if world_id:
        query = f"""
            WITH ranked AS (
                SELECT
                    gs.player_id,
                    gs.display_name,
                    gs.level,
                    gs.xp,
                    gs.gold,
                    jsonb_array_length(gs.codex) AS codex_count,
                    ROW_NUMBER() OVER (ORDER BY {order_by}) AS rank
                FROM game_states gs
                JOIN players p ON p.id = gs.player_id
                WHERE gs.status = 'active'
                  AND gs.world_id = $1
                  AND p.is_npc = FALSE
                  AND p.is_banned = FALSE
            )
            SELECT * FROM ranked WHERE player_id = $2
        """
        row = await pool.fetchrow(query, world_id, player_id)
    else:
        query = f"""
            WITH ranked AS (
                SELECT
                    gs.player_id,
                    gs.display_name,
                    gs.level,
                    gs.xp,
                    gs.gold,
                    jsonb_array_length(gs.codex) AS codex_count,
                    ROW_NUMBER() OVER (ORDER BY {order_by}) AS rank
                FROM game_states gs
                JOIN players p ON p.id = gs.player_id
                WHERE gs.status = 'active'
                  AND p.is_npc = FALSE
                  AND p.is_banned = FALSE
            )
            SELECT * FROM ranked WHERE player_id = $1
        """
        row = await pool.fetchrow(query, player_id)

    if not row:
        return None

    return {
        "rank": row["rank"],
        "display_name": row["display_name"] or "???",
        "level": row["level"],
        "xp": row["xp"],
        "gold": row["gold"],
        "codex_count": row["codex_count"],
    }


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def _format_value(category: str, entry: dict, lang: str) -> str:
    """Format the value string for a leaderboard entry."""
    cat = CATEGORIES[category]
    fmt = cat["value_fmt"].get(lang, cat["value_fmt"]["en"])
    return fmt.format(**entry)


def _format_leaderboard(
    entries: list[dict],
    category: str,
    player_rank: dict | None,
    player_id: str,
    lang: str,
) -> str:
    """Build the full leaderboard text."""
    cat = CATEGORIES[category]
    cat_label = cat["label"].get(lang, cat["label"]["en"])
    cat_emoji = cat["emoji"]

    header = LEADERBOARD_STRINGS["header"].get(lang, LEADERBOARD_STRINGS["header"]["en"])
    lines = [header.format(emoji=cat_emoji, category=cat_label)]
    lines.append("")

    if not entries:
        lines.append(LEADERBOARD_STRINGS["empty"].get(lang, LEADERBOARD_STRINGS["empty"]["en"]))
    else:
        rank_medals = {1: "\U0001f947", 2: "\U0001f948", 3: "\U0001f949"}  # gold, silver, bronze
        for entry in entries:
            medal = rank_medals.get(entry["rank"], f"#{entry['rank']}")
            value = _format_value(category, entry, lang)
            marker = " \u2b05" if entry["player_id"] == player_id else ""
            lines.append(f"{medal} *{entry['display_name']}* \u2014 {value}{marker}")

    # Player's own rank if not in top 10
    if player_rank:
        in_top = any(e["player_id"] == player_id for e in entries)
        if not in_top:
            lines.append("")
            sep = LEADERBOARD_STRINGS["your_rank"].get(lang, LEADERBOARD_STRINGS["your_rank"]["en"])
            value = _format_value(category, player_rank, lang)
            lines.append(f"{sep}")
            lines.append(f"#{player_rank['rank']} *{player_rank['display_name']}* \u2014 {value}")

    return "\n".join(lines)


def _category_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Build inline keyboard with category buttons."""
    buttons = []
    for cat_id, cat in CATEGORIES.items():
        label = cat["label"].get(lang, cat["label"]["en"])
        emoji = cat["emoji"]
        buttons.append(
            InlineKeyboardButton(
                f"{emoji} {label}",
                callback_data=f"top:{cat_id}",
            )
        )
    return InlineKeyboardMarkup([buttons])


# ---------------------------------------------------------------------------
# Command handler
# ---------------------------------------------------------------------------

async def handle_top(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/top - show leaderboard with default category (strongest)."""
    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, update.effective_user.id)
    if not player:
        await update.message.reply_text(
            LEADERBOARD_STRINGS["no_game"].get("en", "Start a game first with /start"),
        )
        return

    lang = player.get("language", "en")
    player_id = str(player["id"])

    game_row = await get_active_game(pool, player_id)
    world_id = str(game_row["world_id"]) if game_row and game_row.get("world_id") else None

    entries = await get_leaderboard(pool, DEFAULT_CATEGORY, world_id=world_id)
    player_rank = await get_player_rank(pool, player_id, DEFAULT_CATEGORY, world_id=world_id)

    text = _format_leaderboard(entries, DEFAULT_CATEGORY, player_rank, player_id, lang)

    try:
        await update.message.reply_text(
            text,
            reply_markup=_category_keyboard(lang),
            parse_mode="Markdown",
        )
    except BadRequest:
        await update.message.reply_text(
            text,
            reply_markup=_category_keyboard(lang),
        )


async def handle_top_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard callback for leaderboard category (top:<category>)."""
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if not data.startswith("top:"):
        return

    category = data[4:]
    if category not in CATEGORIES:
        return

    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, query.from_user.id)
    if not player:
        return

    lang = player.get("language", "en")
    player_id = str(player["id"])

    game_row = await get_active_game(pool, player_id)
    world_id = str(game_row["world_id"]) if game_row and game_row.get("world_id") else None

    entries = await get_leaderboard(pool, category, world_id=world_id)
    player_rank = await get_player_rank(pool, player_id, category, world_id=world_id)

    text = _format_leaderboard(entries, category, player_rank, player_id, lang)

    try:
        await query.message.reply_text(
            text,
            reply_markup=_category_keyboard(lang),
            parse_mode="Markdown",
        )
    except BadRequest:
        await query.message.reply_text(
            text,
            reply_markup=_category_keyboard(lang),
        )


# ---------------------------------------------------------------------------
# Strings (EN / RU)
# ---------------------------------------------------------------------------

LEADERBOARD_STRINGS: dict[str, dict[str, str]] = {
    "header": {
        "en": "{emoji} *Weekly Leaderboard \u2014 {category}*",
        "ru": "{emoji} *\u0422\u0430\u0431\u043b\u0438\u0446\u0430 \u043b\u0438\u0434\u0435\u0440\u043e\u0432 \u2014 {category}*",
    },
    "empty": {
        "en": "No active players yet. Be the first!",
        "ru": "\u041f\u043e\u043a\u0430 \u043d\u0435\u0442 \u0430\u043a\u0442\u0438\u0432\u043d\u044b\u0445 \u0438\u0433\u0440\u043e\u043a\u043e\u0432. \u0411\u0443\u0434\u044c \u043f\u0435\u0440\u0432\u044b\u043c!",
    },
    "your_rank": {
        "en": "\u2500\u2500\u2500 Your rank \u2500\u2500\u2500",
        "ru": "\u2500\u2500\u2500 \u0422\u0432\u043e\u0451 \u043c\u0435\u0441\u0442\u043e \u2500\u2500\u2500",
    },
    "no_game": {
        "en": "Start a game first with /start",
        "ru": "\u0421\u043d\u0430\u0447\u0430\u043b\u0430 \u043d\u0430\u0447\u043d\u0438 \u0438\u0433\u0440\u0443 \u043a\u043e\u043c\u0430\u043d\u0434\u043e\u0439 /start",
    },
}

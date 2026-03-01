"""Handler for /skills command — view and spend skill points."""

from __future__ import annotations

import json
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from bot.db.queries.players import get_player_by_telegram_id
from bot.db.queries.game_states import get_active_game, update_game_state
from bot.engine.game_state import GameState
from bot.engine.skills import (
    SKILLS,
    get_skill_rank,
    get_skill_effect,
    can_learn_skill,
    learn_skill,
    get_skills_by_category,
)
from bot.i18n import get_text

logger = logging.getLogger(__name__)

# Category labels
_CAT_LABELS = {
    "survival": {"en": "🏕 Survival", "ru": "🏕 Выживание"},
    "economy": {"en": "💰 Economy", "ru": "💰 Экономика"},
    "military": {"en": "⚔️ Military", "ru": "⚔️ Военное дело"},
    "social": {"en": "🤝 Social", "ru": "🤝 Социальное"},
}

_RANK_STARS = {0: "○○○", 1: "●○○", 2: "●●○", 3: "●●●"}


async def handle_skills(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/skills — show current skills and available upgrades."""
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
    text = _format_skills_page(state, lang)
    keyboard = _skills_keyboard(state, lang) if state.skill_points > 0 else None

    try:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")
    except BadRequest:
        await update.message.reply_text(text, reply_markup=keyboard)


async def handle_skill_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard callback for skill learning (skill:skill_id)."""
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if not data.startswith("skill:"):
        return

    skill_id = data[6:]  # e.g. "skill:iron_stomach"

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

    # Validate and learn
    ok, reason = can_learn_skill(state, skill_id)
    if not ok:
        error_text = get_text("skill_cannot_learn", lang, reason=reason)
        await query.message.reply_text(error_text)
        return

    learn_skill(state, skill_id)

    # Persist updated skills and skill_points
    await update_game_state(
        pool, state.id,
        skills=state.skills,
        skill_points=state.skill_points,
    )

    # Notify
    spec = SKILLS[skill_id]
    skill_name = spec["name"].get(lang, spec["name"]["en"])
    new_rank = state.skills[skill_id]
    effect_val = get_skill_effect(state, skill_id)

    confirm_text = get_text(
        "skill_learned", lang,
        skill=skill_name,
        rank=new_rank,
        effect=effect_val,
        remaining=state.skill_points,
    )
    await query.message.reply_text(confirm_text, parse_mode="Markdown")

    # Show updated skills page if they still have points
    if state.skill_points > 0:
        text = _format_skills_page(state, lang)
        keyboard = _skills_keyboard(state, lang)
        try:
            await query.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")
        except BadRequest:
            await query.message.reply_text(text, reply_markup=keyboard)


def _format_skills_page(state: GameState, lang: str) -> str:
    """Build the full skills display text."""
    lines = [get_text("skills_header", lang, points=state.skill_points)]
    lines.append("")

    cats = get_skills_by_category()
    cat_order = ["survival", "economy", "military", "social"]

    for cat in cat_order:
        skill_ids = cats.get(cat, [])
        if not skill_ids:
            continue

        cat_label = _CAT_LABELS.get(cat, {}).get(lang, cat.title())
        lines.append(f"*{cat_label}*")

        for sid in skill_ids:
            spec = SKILLS[sid]
            rank = get_skill_rank(state, sid)
            name = spec["name"].get(lang, spec["name"]["en"])
            stars = _RANK_STARS.get(rank, "○○○")
            effect = rank * spec["per_rank"] if rank > 0 else 0

            desc_template = spec["description"].get(lang, spec["description"]["en"])
            desc = desc_template.format(value=spec["per_rank"])

            line = f"  {stars} *{name}*"
            if rank > 0:
                line += f" (rank {rank}, +{effect})"
            lines.append(line)
            lines.append(f"      _{desc}_")

        lines.append("")

    return "\n".join(lines)


def _skills_keyboard(state: GameState, lang: str) -> InlineKeyboardMarkup:
    """Build keyboard with buttons for learnable skills."""
    buttons = []
    for sid, spec in SKILLS.items():
        ok, _ = can_learn_skill(state, sid)
        if not ok:
            continue
        name = spec["name"].get(lang, spec["name"]["en"])
        rank = state.skills.get(sid, 0)
        label = f"📖 {name} → Rank {rank + 1}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"skill:{sid}")])

    if not buttons:
        return None

    return InlineKeyboardMarkup(buttons)

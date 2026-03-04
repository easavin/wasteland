"""Handler for interactive multi-step exploration via inline keyboards.

When a player types 'explore', instead of the normal single-turn action,
they enter an interactive exploration scenario with branching choices.
The scenario state is stored in ``context.user_data`` for the duration.
"""

from __future__ import annotations

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from bot.db.queries.players import get_player_by_telegram_id
from bot.db.queries.game_states import get_active_game, update_game_state
from bot.engine.game_state import GameState
from bot.engine.exploration import (
    pick_scenario,
    resolve_exploration_choice,
    SCENARIOS,
    EXPLORATION_STRINGS,
)
from bot.engine.items import add_item_to_inventory, get_item_name
from bot.engine.codex import check_codex_discovery
from bot.i18n import get_text

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Entry point — called from messages.py when player types "explore"
# ---------------------------------------------------------------------------

async def start_exploration(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    player: dict,
    state: GameState,
) -> None:
    """Begin a new exploration scenario for the player."""
    lang = player.get("language", "en")

    # Pick a scenario based on zone
    try:
        scenario = pick_scenario(state.zone)
    except ValueError:
        await update.message.reply_text(get_text("explore_no_scenario", lang))
        return

    # Store exploration state in user_data
    context.user_data["exploration"] = {
        "scenario_id": scenario.id,
        "current_step": 0,
        "total_scrap": 0,
        "total_gold": 0,
        "total_pop_lost": 0,
        "total_morale_lost": 0,
        "items_found": [],
        "codex_found": [],
    }

    # Send the intro — use the intro_key for i18n lookup
    intro = EXPLORATION_STRINGS.get(scenario.intro_key, {}).get(lang)
    if not intro:
        # Fallback to a generic intro
        intro = "You set out into the wasteland..." if lang == "en" else "Ты отправляешься в пустошь..."

    scenario_name = _scenario_name(scenario, lang)
    text = f"🗺 *{scenario_name}*\n\n{intro}"
    keyboard = _step_keyboard(scenario, 0, lang)

    try:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")
    except BadRequest:
        await update.message.reply_text(text, reply_markup=keyboard)


# ---------------------------------------------------------------------------
# Callback handler for explore:<choice_id>
# ---------------------------------------------------------------------------

async def handle_explore_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle explore:<choice_id> callbacks during exploration."""
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if not data.startswith("explore:"):
        return

    choice_id = data[8:]  # after "explore:"

    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, query.from_user.id)
    if not player:
        return

    lang = player.get("language", "en")
    player_id = str(player["id"])

    # Check exploration state
    exp_state = context.user_data.get("exploration")
    if not exp_state:
        await query.message.reply_text(
            "No active exploration." if lang == "en" else "Нет активного исследования."
        )
        return

    scenario_id = exp_state["scenario_id"]
    scenario = next((s for s in SCENARIOS if s.id == scenario_id), None)
    if scenario is None:
        context.user_data.pop("exploration", None)
        return

    current_step_idx = exp_state["current_step"]
    if current_step_idx >= len(scenario.steps):
        context.user_data.pop("exploration", None)
        return

    step = scenario.steps[current_step_idx]

    # Find the chosen choice
    choice = next((c for c in step.choices if c.id == choice_id), None)
    if choice is None:
        return

    # Resolve the choice — returns a dict
    game_row = await get_active_game(pool, player_id)
    if not game_row:
        context.user_data.pop("exploration", None)
        return

    state = GameState.from_db_row(game_row)
    result = resolve_exploration_choice(choice, state.zone)

    # result is a dict: {"scrap", "gold", "item_id", "pop_loss", "morale_loss", "codex_entry"}
    scrap_gained = result.get("scrap", 0)
    gold_gained = result.get("gold", 0)
    pop_lost = result.get("pop_loss", 0)
    morale_lost = result.get("morale_loss", 0)
    item_id = result.get("item_id")
    codex_entry = result.get("codex_entry")

    # Accumulate results
    exp_state["total_scrap"] += scrap_gained
    exp_state["total_gold"] += gold_gained
    exp_state["total_pop_lost"] += pop_lost
    exp_state["total_morale_lost"] += morale_lost

    # Handle item from exploration engine
    item_found = None
    if item_id:
        state.inventory = add_item_to_inventory(state.inventory, item_id)
        exp_state["items_found"].append(item_id)
        item_found = item_id

    # Handle codex from exploration choice
    if codex_entry and codex_entry not in state.codex:
        state.codex.append(codex_entry)
        exp_state["codex_found"].append(codex_entry)
    elif not codex_entry:
        # Also try random codex discovery
        random_codex = check_codex_discovery(event_id=None, zone=state.zone, action="explore", discovered=state.codex)
        if random_codex:
            state.codex.append(random_codex)
            exp_state["codex_found"].append(random_codex)
            codex_entry = random_codex

    # Build response text for this step
    risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(choice.risk, "⚪")
    lines = [f"{risk_emoji} *{_choice_label(choice, lang)}*", ""]

    if scrap_gained > 0:
        lines.append(f"  🔩 +{scrap_gained} scrap")
    if gold_gained > 0:
        lines.append(f"  💰 +{gold_gained} gold")
    if pop_lost > 0:
        lines.append(f"  👥 -{pop_lost} population")
    if morale_lost > 0:
        lines.append(f"  😞 -{morale_lost} morale")
    if item_found:
        iname = get_item_name(item_found, lang)
        lines.append(f"  🎁 Found: {iname}")
    if codex_entry:
        from bot.engine.codex import CODEX_ENTRIES
        ce = CODEX_ENTRIES.get(codex_entry, {})
        ce_name = ce.get("name", {}).get(lang, codex_entry)
        lines.append(f"  📖 Codex: {ce_name}")

    # Check if scenario continues or resolves
    if choice.next_step is not None and choice.next_step < len(scenario.steps):
        # Continue to next step
        exp_state["current_step"] = choice.next_step
        next_step = scenario.steps[choice.next_step]

        # Use prompt_key for i18n lookup
        prompt = EXPLORATION_STRINGS.get(next_step.prompt_key, {}).get(lang)
        if not prompt:
            prompt = "What do you do next?" if lang == "en" else "Что дальше?"
        lines.append(f"\n{prompt}")

        text = "\n".join(lines)
        keyboard = _step_keyboard(scenario, choice.next_step, lang)
    else:
        # Exploration complete — apply all results
        state.scrap += exp_state["total_scrap"]
        state.gold += exp_state["total_gold"]
        state.population -= exp_state["total_pop_lost"]
        state.morale -= exp_state["total_morale_lost"]
        state.clamp_resources()

        await update_game_state(
            pool, state.id,
            scrap=state.scrap,
            gold=state.gold,
            population=state.population,
            morale=state.morale,
            inventory=state.inventory,
            codex=state.codex,
        )

        # Summary
        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━")
        if lang == "ru":
            lines.append("📊 *Итоги разведки:*")
        else:
            lines.append("📊 *Exploration Summary:*")

        total_scrap = exp_state["total_scrap"]
        total_gold = exp_state["total_gold"]
        total_pop = exp_state["total_pop_lost"]
        total_morale = exp_state["total_morale_lost"]

        if total_scrap > 0:
            lines.append(f"  🔩 +{total_scrap}")
        if total_gold > 0:
            lines.append(f"  💰 +{total_gold}")
        if total_pop > 0:
            lines.append(f"  👥 -{total_pop}")
        if total_morale > 0:
            lines.append(f"  😞 -{total_morale}")
        if exp_state["items_found"]:
            for iid in exp_state["items_found"]:
                iname = get_item_name(iid, lang)
                lines.append(f"  🎁 {iname}")
        if exp_state["codex_found"]:
            from bot.engine.codex import CODEX_ENTRIES as _CE
            for ceid in exp_state["codex_found"]:
                ce = _CE.get(ceid, {})
                lines.append(f"  📖 {ce.get('name', {}).get(lang, ceid)}")

        context.user_data.pop("exploration", None)
        keyboard = None
        text = "\n".join(lines)

    try:
        await query.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")
    except BadRequest:
        await query.message.reply_text(text, reply_markup=keyboard)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _scenario_name(scenario, lang: str) -> str:
    """Get a display name for the scenario from its id."""
    # Try i18n lookup first
    name = EXPLORATION_STRINGS.get(f"explore_sc_{scenario.id}_name", {}).get(lang)
    if name:
        return name
    # Fallback: prettify the ID
    return scenario.id.replace("_", " ").title()


def _choice_label(choice, lang: str) -> str:
    """Get a display label for a choice."""
    label = EXPLORATION_STRINGS.get(choice.label_key, {}).get(lang)
    if label:
        return label
    return choice.label_key.replace("_", " ").title()


def _step_keyboard(scenario, step_idx: int, lang: str) -> InlineKeyboardMarkup:
    """Build inline keyboard for a scenario step's choices."""
    step = scenario.steps[step_idx]
    buttons = []
    risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}
    for choice in step.choices:
        emoji = risk_emoji.get(choice.risk, "⚪")
        label = _choice_label(choice, lang)
        buttons.append([InlineKeyboardButton(
            f"{emoji} {label}",
            callback_data=f"explore:{choice.id}",
        )])
    return InlineKeyboardMarkup(buttons)


# EXPLORATION_STRINGS is imported from bot.engine.exploration

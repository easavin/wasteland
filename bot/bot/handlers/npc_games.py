"""NPC interactive minigame handlers.

Each NPC offers a unique minigame playable through inline keyboard buttons.
Game state is stored in context.user_data (ephemeral, per-user).
Rewards/penalties are applied to the player's game_states row on completion.

NPCs & their games:
  Old Trader  → Scrap Roulette (pick mystery crates)
  Doc         → Field Triage   (diagnose patients)
  Sentry      → Perimeter Breach (defend sectors)
"""

from __future__ import annotations

import logging
import random
from datetime import datetime, timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from bot.db.queries.players import get_player_by_telegram_id
from bot.db.queries.game_states import get_active_game, update_game_state
from bot.db.queries.npcs import list_npcs_in_zone
from bot.i18n import get_text

logger = logging.getLogger(__name__)

# Cooldown between minigame plays (seconds) — 1 game per NPC per 10 minutes
MINIGAME_COOLDOWN = 600

# ── NPC name → game type mapping ──────────────────────────────────────
_NPC_GAMES: dict[str, str] = {
    "old trader": "scrap_roulette",
    "doc": "field_triage",
    "sentry": "perimeter_breach",
}


# ══════════════════════════════════════════════════════════════════════
#  /npc command — list NPCs and start games
# ══════════════════════════════════════════════════════════════════════

async def handle_npc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /npc [name] — list NPCs or start a minigame with one."""
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

    world_id = game_row.get("world_id")
    zone = game_row.get("zone", 1)
    if not world_id:
        await update.message.reply_text(get_text("chat_no_world", lang))
        return

    args = context.args or []

    if not args:
        # List NPCs with "Play" buttons
        npcs = await list_npcs_in_zone(pool, str(world_id), zone)
        if not npcs:
            await update.message.reply_text(get_text("npc_no_npcs", lang))
            return

        buttons = []
        for n in npcs:
            name = n.get("display_name") or "?"
            game_type = _NPC_GAMES.get(name.lower())
            if game_type:
                game_label = get_text(f"npc_game_name_{game_type}", lang)
                buttons.append([InlineKeyboardButton(
                    f"{_npc_emoji(name)} {name} — {game_label}",
                    callback_data=f"npc:start:{name.lower().replace(' ', '_')}",
                )])

        if not buttons:
            await update.message.reply_text(get_text("npc_no_games", lang))
            return

        await update.message.reply_text(
            get_text("npc_games_header", lang),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown",
        )
        return

    # Start a game with a specific NPC
    npc_name = " ".join(args).strip().lower()
    await _start_npc_game(update.message, context, player, game_row, npc_name, lang)


# ══════════════════════════════════════════════════════════════════════
#  Callback handler — routes all npc: button presses
# ══════════════════════════════════════════════════════════════════════

async def handle_npc_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route npc:* callback queries."""
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, query.from_user.id)
    if not player:
        return

    lang = player.get("language", "en")
    game_row = await get_active_game(pool, str(player["id"]))
    if not game_row:
        return

    parts = data.split(":")
    # npc:start:<npc_key>
    if len(parts) >= 3 and parts[1] == "start":
        npc_key = parts[2]
        npc_name = npc_key.replace("_", " ")
        await _start_npc_game(query.message, context, player, game_row, npc_name, lang)
        return

    # npc:roulette:<choice>
    if len(parts) >= 3 and parts[1] == "roulette":
        await _handle_roulette_pick(query.message, context, player, game_row, parts[2], lang)
        return

    # npc:triage:<choice>
    if len(parts) >= 3 and parts[1] == "triage":
        await _handle_triage_pick(query.message, context, player, game_row, parts[2], lang)
        return

    # npc:breach:<choice>
    if len(parts) >= 3 and parts[1] == "breach":
        await _handle_breach_pick(query.message, context, player, game_row, parts[2], lang)
        return


# ══════════════════════════════════════════════════════════════════════
#  Start a minigame
# ══════════════════════════════════════════════════════════════════════

async def _start_npc_game(message, context, player, game_row, npc_name: str, lang: str) -> None:
    """Resolve NPC and launch the appropriate minigame."""
    game_type = _NPC_GAMES.get(npc_name)
    if not game_type:
        await _safe_reply(message, get_text("npc_not_found", lang))
        return

    # Cooldown check
    cooldown_key = f"npc_cooldown_{npc_name}"
    last_played = context.user_data.get(cooldown_key)
    now = datetime.now(timezone.utc)
    if last_played:
        elapsed = (now - last_played).total_seconds()
        if elapsed < MINIGAME_COOLDOWN:
            remaining = int(MINIGAME_COOLDOWN - elapsed)
            mins = remaining // 60
            secs = remaining % 60
            await _safe_reply(message, get_text("npc_cooldown", lang, mins=mins, secs=secs))
            return

    # Mark cooldown
    context.user_data[cooldown_key] = now

    if game_type == "scrap_roulette":
        await _start_roulette(message, context, player, game_row, lang)
    elif game_type == "field_triage":
        await _start_triage(message, context, player, game_row, lang)
    elif game_type == "perimeter_breach":
        await _start_breach(message, context, player, game_row, lang)


# ══════════════════════════════════════════════════════════════════════
#  GAME 1: Scrap Roulette (Old Trader)
# ══════════════════════════════════════════════════════════════════════

_CRATE_CONTENTS = [
    {"label_key": "roulette_crate_jackpot", "emoji": "💎", "gold": 15, "scrap": 25, "food": 0, "weight": 5},
    {"label_key": "roulette_crate_good", "emoji": "✨", "gold": 8, "scrap": 15, "food": 10, "weight": 15},
    {"label_key": "roulette_crate_decent", "emoji": "📦", "gold": 3, "scrap": 10, "food": 5, "weight": 25},
    {"label_key": "roulette_crate_junk", "emoji": "🗑", "gold": 0, "scrap": 3, "food": 0, "weight": 30},
    {"label_key": "roulette_crate_trap", "emoji": "💥", "gold": -5, "scrap": -10, "food": -5, "weight": 15},
    {"label_key": "roulette_crate_empty", "emoji": "💨", "gold": 0, "scrap": 0, "food": 0, "weight": 10},
]

ROULETTE_COST = 10  # scrap to play


async def _start_roulette(message, context, player, game_row, lang: str) -> None:
    """Old Trader's Scrap Roulette — pick one of three mystery crates."""
    # Check player has enough scrap
    current_scrap = game_row.get("scrap", 0)
    if current_scrap < ROULETTE_COST:
        await _safe_reply(message, get_text("roulette_no_scrap", lang, cost=ROULETTE_COST, have=current_scrap))
        return

    # Generate 3 random crates (weighted)
    weights = [c["weight"] for c in _CRATE_CONTENTS]
    crates = random.choices(_CRATE_CONTENTS, weights=weights, k=3)

    # Store in user_data for resolution
    context.user_data["roulette_crates"] = crates
    context.user_data["roulette_game_id"] = str(game_row["id"])

    intro = get_text("roulette_intro", lang, cost=ROULETTE_COST)
    buttons = [
        [
            InlineKeyboardButton("📦 A", callback_data="npc:roulette:0"),
            InlineKeyboardButton("📦 B", callback_data="npc:roulette:1"),
            InlineKeyboardButton("📦 C", callback_data="npc:roulette:2"),
        ],
    ]
    await _safe_reply(message, intro, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")


async def _handle_roulette_pick(message, context, player, game_row, choice: str, lang: str) -> None:
    """Resolve the player's crate pick."""
    crates = context.user_data.pop("roulette_crates", None)
    roulette_game_id = context.user_data.pop("roulette_game_id", None)
    if not crates or not roulette_game_id:
        await _safe_reply(message, get_text("npc_game_expired", lang))
        return

    try:
        idx = int(choice)
    except ValueError:
        return
    if idx < 0 or idx >= len(crates):
        return

    picked = crates[idx]
    pool = context.bot_data["db_pool"]

    # Deduct cost and apply rewards
    game_id = str(game_row["id"])
    current = await get_active_game(pool, str(player["id"]))
    if not current:
        return

    new_scrap = max(0, current["scrap"] - ROULETTE_COST + picked["scrap"])
    new_gold = max(0, current["gold"] + picked["gold"])
    new_food = max(0, current["food"] + picked["food"])

    await update_game_state(pool, game_id, scrap=new_scrap, gold=new_gold, food=new_food)

    # Build result message showing all 3 crates
    labels = ["A", "B", "C"]
    reveal_lines = []
    for i, c in enumerate(crates):
        content_name = get_text(c["label_key"], lang)
        marker = " 👈" if i == idx else ""
        reveal_lines.append(f"  {labels[i]}: {c['emoji']} {content_name}{marker}")

    delta_parts = []
    net_scrap = picked["scrap"] - ROULETTE_COST
    if net_scrap != 0:
        delta_parts.append(f"🔩 {'+' if net_scrap > 0 else ''}{net_scrap}")
    if picked["gold"] != 0:
        delta_parts.append(f"💰 {'+' if picked['gold'] > 0 else ''}{picked['gold']}")
    if picked["food"] != 0:
        delta_parts.append(f"🌾 {'+' if picked['food'] > 0 else ''}{picked['food']}")

    delta_str = " | ".join(delta_parts) if delta_parts else get_text("roulette_nothing", lang)

    text = get_text(
        "roulette_result", lang,
        picked=labels[idx],
        emoji=picked["emoji"],
        content=get_text(picked["label_key"], lang),
        reveal="\n".join(reveal_lines),
        deltas=delta_str,
    )
    await _safe_reply(message, text, parse_mode="Markdown")


# ══════════════════════════════════════════════════════════════════════
#  GAME 2: Field Triage (Doc)
# ══════════════════════════════════════════════════════════════════════

_TRIAGE_CASES = [
    {
        "symptom_key": "triage_case_radiation",
        "options": ["triage_opt_radaway", "triage_opt_bandage", "triage_opt_rest"],
        "correct": 0,
    },
    {
        "symptom_key": "triage_case_broken_leg",
        "options": ["triage_opt_splint", "triage_opt_herbs", "triage_opt_amputation"],
        "correct": 0,
    },
    {
        "symptom_key": "triage_case_fever",
        "options": ["triage_opt_antibiotics", "triage_opt_cold_water", "triage_opt_ignore"],
        "correct": 0,
    },
    {
        "symptom_key": "triage_case_wound",
        "options": ["triage_opt_stitch", "triage_opt_cauterize", "triage_opt_prayer"],
        "correct": 0,
    },
    {
        "symptom_key": "triage_case_toxin",
        "options": ["triage_opt_charcoal", "triage_opt_whiskey", "triage_opt_sleep"],
        "correct": 0,
    },
    {
        "symptom_key": "triage_case_dehydration",
        "options": ["triage_opt_clean_water", "triage_opt_stimpak", "triage_opt_food"],
        "correct": 0,
    },
]

TRIAGE_ROUNDS = 3
TRIAGE_REWARD_PER_CORRECT = {"population": 2, "morale": 3}
TRIAGE_PENALTY_PER_WRONG = {"morale": -2}


async def _start_triage(message, context, player, game_row, lang: str) -> None:
    """Doc's Field Triage — diagnose 3 patients."""
    cases = random.sample(_TRIAGE_CASES, min(TRIAGE_ROUNDS, len(_TRIAGE_CASES)))
    context.user_data["triage_cases"] = cases
    context.user_data["triage_round"] = 0
    context.user_data["triage_score"] = 0
    context.user_data["triage_game_id"] = str(game_row["id"])

    intro = get_text("triage_intro", lang, rounds=TRIAGE_ROUNDS)
    await _safe_reply(message, intro, parse_mode="Markdown")
    await _send_triage_round(message, context, lang)


async def _send_triage_round(message, context, lang: str) -> None:
    """Send the current triage case to the player."""
    cases = context.user_data.get("triage_cases", [])
    round_idx = context.user_data.get("triage_round", 0)

    if round_idx >= len(cases):
        return

    case = cases[round_idx]
    symptom = get_text(case["symptom_key"], lang)

    buttons = []
    for i, opt_key in enumerate(case["options"]):
        opt_text = get_text(opt_key, lang)
        buttons.append([InlineKeyboardButton(opt_text, callback_data=f"npc:triage:{i}")])

    text = get_text("triage_patient", lang, round=round_idx + 1, total=TRIAGE_ROUNDS, symptom=symptom)
    await _safe_reply(message, text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")


async def _handle_triage_pick(message, context, player, game_row, choice: str, lang: str) -> None:
    """Handle a treatment choice."""
    cases = context.user_data.get("triage_cases")
    round_idx = context.user_data.get("triage_round")
    if cases is None or round_idx is None:
        await _safe_reply(message, get_text("npc_game_expired", lang))
        return

    try:
        pick = int(choice)
    except ValueError:
        return

    if round_idx >= len(cases):
        return

    case = cases[round_idx]
    correct = case["correct"]
    is_correct = pick == correct

    if is_correct:
        context.user_data["triage_score"] = context.user_data.get("triage_score", 0) + 1
        feedback = get_text("triage_correct", lang)
    else:
        correct_text = get_text(case["options"][correct], lang)
        feedback = get_text("triage_wrong", lang, correct=correct_text)

    context.user_data["triage_round"] = round_idx + 1

    # Check if game is over
    if round_idx + 1 >= len(cases):
        score = context.user_data.pop("triage_score", 0)
        context.user_data.pop("triage_cases", None)
        context.user_data.pop("triage_round", None)
        game_id = context.user_data.pop("triage_game_id", None)

        # Apply rewards
        pool = context.bot_data["db_pool"]
        current = await get_active_game(pool, str(player["id"]))
        if current and game_id:
            pop_bonus = score * TRIAGE_REWARD_PER_CORRECT["population"]
            morale_bonus = score * TRIAGE_REWARD_PER_CORRECT["morale"]
            wrong = len(cases) - score
            morale_bonus += wrong * TRIAGE_PENALTY_PER_WRONG["morale"]

            new_pop = max(1, current["population"] + pop_bonus)
            new_morale = max(0, min(100, current["morale"] + morale_bonus))
            await update_game_state(pool, game_id, population=new_pop, morale=new_morale)

        result = get_text("triage_result", lang, score=score, total=len(cases), pop=score * 2, morale=morale_bonus)
        await _safe_reply(message, f"{feedback}\n\n{result}", parse_mode="Markdown")
        return

    # Send feedback + next round
    await _safe_reply(message, feedback, parse_mode="Markdown")
    await _send_triage_round(message, context, lang)


# ══════════════════════════════════════════════════════════════════════
#  GAME 3: Perimeter Breach (Sentry)
# ══════════════════════════════════════════════════════════════════════

_THREATS = [
    {
        "threat_key": "breach_threat_raiders",
        "correct": "shoot",
        "options": ["shoot", "negotiate", "hide"],
    },
    {
        "threat_key": "breach_threat_mutants",
        "correct": "shoot",
        "options": ["shoot", "trap", "run"],
    },
    {
        "threat_key": "breach_threat_traders",
        "correct": "negotiate",
        "options": ["shoot", "negotiate", "hide"],
    },
    {
        "threat_key": "breach_threat_refugees",
        "correct": "negotiate",
        "options": ["shoot", "negotiate", "hide"],
    },
    {
        "threat_key": "breach_threat_sandstorm",
        "correct": "hide",
        "options": ["shoot", "negotiate", "hide"],
    },
    {
        "threat_key": "breach_threat_drones",
        "correct": "shoot",
        "options": ["shoot", "trap", "run"],
    },
    {
        "threat_key": "breach_threat_scavengers",
        "correct": "negotiate",
        "options": ["shoot", "negotiate", "trap"],
    },
    {
        "threat_key": "breach_threat_radstorm",
        "correct": "hide",
        "options": ["shoot", "hide", "run"],
    },
]

_SECTOR_NAMES = ["North", "South", "East", "West"]

BREACH_ROUNDS = 4
BREACH_REWARD_PER_CORRECT = {"defense": 3, "morale": 2}
BREACH_PENALTY_PER_WRONG = {"defense": -2, "population": -1}


async def _start_breach(message, context, player, game_row, lang: str) -> None:
    """Sentry's Perimeter Breach — 4 rounds of threat response."""
    threats = random.sample(_THREATS, min(BREACH_ROUNDS, len(_THREATS)))
    sectors = random.sample(_SECTOR_NAMES, min(BREACH_ROUNDS, len(_SECTOR_NAMES)))

    context.user_data["breach_threats"] = threats
    context.user_data["breach_sectors"] = sectors
    context.user_data["breach_round"] = 0
    context.user_data["breach_score"] = 0
    context.user_data["breach_game_id"] = str(game_row["id"])

    intro = get_text("breach_intro", lang, rounds=BREACH_ROUNDS)
    await _safe_reply(message, intro, parse_mode="Markdown")
    await _send_breach_round(message, context, lang)


async def _send_breach_round(message, context, lang: str) -> None:
    """Send the current threat to the player."""
    threats = context.user_data.get("breach_threats", [])
    sectors = context.user_data.get("breach_sectors", [])
    round_idx = context.user_data.get("breach_round", 0)

    if round_idx >= len(threats):
        return

    threat = threats[round_idx]
    sector = sectors[round_idx] if round_idx < len(sectors) else "Unknown"
    threat_desc = get_text(threat["threat_key"], lang)

    buttons = []
    option_emojis = {"shoot": "🔫", "negotiate": "🤝", "hide": "🛡", "trap": "🪤", "run": "🏃"}
    for opt in threat["options"]:
        emoji = option_emojis.get(opt, "")
        opt_label = get_text(f"breach_opt_{opt}", lang)
        buttons.append(InlineKeyboardButton(f"{emoji} {opt_label}", callback_data=f"npc:breach:{opt}"))

    text = get_text(
        "breach_alert", lang,
        round=round_idx + 1, total=BREACH_ROUNDS,
        sector=sector, threat=threat_desc,
    )
    await _safe_reply(message, text, reply_markup=InlineKeyboardMarkup([buttons]), parse_mode="Markdown")


async def _handle_breach_pick(message, context, player, game_row, choice: str, lang: str) -> None:
    """Handle a defensive response choice."""
    threats = context.user_data.get("breach_threats")
    round_idx = context.user_data.get("breach_round")
    if threats is None or round_idx is None:
        await _safe_reply(message, get_text("npc_game_expired", lang))
        return

    if round_idx >= len(threats):
        return

    threat = threats[round_idx]
    is_correct = choice == threat["correct"]

    if is_correct:
        context.user_data["breach_score"] = context.user_data.get("breach_score", 0) + 1
        feedback = get_text("breach_correct", lang)
    else:
        correct_label = get_text(f"breach_opt_{threat['correct']}", lang)
        feedback = get_text("breach_wrong", lang, correct=correct_label)

    context.user_data["breach_round"] = round_idx + 1

    # Check if game is over
    if round_idx + 1 >= len(threats):
        score = context.user_data.pop("breach_score", 0)
        context.user_data.pop("breach_threats", None)
        context.user_data.pop("breach_sectors", None)
        context.user_data.pop("breach_round", None)
        game_id = context.user_data.pop("breach_game_id", None)

        # Apply rewards
        pool = context.bot_data["db_pool"]
        current = await get_active_game(pool, str(player["id"]))
        if current and game_id:
            wrong = BREACH_ROUNDS - score
            def_bonus = score * BREACH_REWARD_PER_CORRECT["defense"]
            morale_bonus = score * BREACH_REWARD_PER_CORRECT["morale"]
            def_penalty = wrong * BREACH_PENALTY_PER_WRONG["defense"]
            pop_penalty = wrong * BREACH_PENALTY_PER_WRONG["population"]

            new_defense = max(0, min(100, current["defense"] + def_bonus + def_penalty))
            new_morale = max(0, min(100, current["morale"] + morale_bonus))
            new_pop = max(1, current["population"] + pop_penalty)

            await update_game_state(pool, game_id, defense=new_defense, morale=new_morale, population=new_pop)

            total_def = def_bonus + def_penalty
            result = get_text(
                "breach_result", lang,
                score=score, total=BREACH_ROUNDS,
                defense=total_def, morale=morale_bonus, pop=pop_penalty,
            )
        else:
            result = get_text("breach_result_no_reward", lang)

        await _safe_reply(message, f"{feedback}\n\n{result}", parse_mode="Markdown")
        return

    # Send feedback + next round
    await _safe_reply(message, feedback, parse_mode="Markdown")
    await _send_breach_round(message, context, lang)


# ══════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════

def _npc_emoji(name: str) -> str:
    """Return an emoji for an NPC by name."""
    return {
        "old trader": "🏪",
        "doc": "💊",
        "sentry": "🎯",
    }.get(name.lower(), "👤")


async def _safe_reply(target, text: str, **kwargs) -> None:
    """Send a reply, retrying without parse_mode on Markdown errors."""
    try:
        await target.reply_text(text, **kwargs)
    except BadRequest as e:
        if "parse" in str(e).lower():
            kwargs.pop("parse_mode", None)
            await target.reply_text(text, **kwargs)
        else:
            raise

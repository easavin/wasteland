"""Daily mission catalog, generation, and progress tracking.

Missions are generated fresh each calendar day and stored as JSONB in the
``daily_missions`` table.  The turn processor calls :func:`check_mission_progress`
after every turn to update counters.
"""

from __future__ import annotations

import logging
import random
from copy import deepcopy

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mission template catalog
# ---------------------------------------------------------------------------
# Each template defines:
#   key             - unique identifier prefix (will be suffixed with target)
#   description_key - key into MISSION_STRINGS for the display text
#   target / target_range - fixed target value or [min, max] for randomisation
#   action          - (optional) the player action this tracks
#   check           - how progress is evaluated
#   stat            - (optional) for stat_threshold checks
#   reward_pool     - list of possible reward dicts (one is picked at random)
# ---------------------------------------------------------------------------

MISSION_TEMPLATES: list[dict] = [
    {
        "key": "explore_n",
        "description_key": "mission_explore_n",
        "target_range": [1, 3],
        "action": "explore",
        "check": "action_count",
        "reward_pool": [{"scrap": 20}, {"scrap": 30}],
    },
    {
        "key": "build_any",
        "description_key": "mission_build_any",
        "target": 1,
        "action": "build",
        "check": "action_count",
        "reward_pool": [{"gold": 5}],
    },
    {
        "key": "trade_n",
        "description_key": "mission_trade_n",
        "target_range": [1, 2],
        "action": "trade",
        "check": "action_count",
        "reward_pool": [{"food": 25}],
    },
    {
        "key": "defend_n",
        "description_key": "mission_defend_n",
        "target_range": [1, 2],
        "action": "defend",
        "check": "action_count",
        "reward_pool": [{"scrap": 25}],
    },
    {
        "key": "diplomacy_n",
        "description_key": "mission_diplomacy_n",
        "target_range": [1, 2],
        "action": "diplomacy",
        "check": "action_count",
        "reward_pool": [{"gold": 3}],
    },
    {
        "key": "rest_n",
        "description_key": "mission_rest_n",
        "target_range": [1, 2],
        "action": "rest",
        "check": "action_count",
        "reward_pool": [{"food": 15, "morale_bonus": 5}],
    },
    {
        "key": "earn_gold_n",
        "description_key": "mission_earn_gold",
        "target_range": [5, 15],
        "check": "gold_earned",
        "reward_pool": [{"scrap": 30}],
    },
    {
        "key": "play_npc_game",
        "description_key": "mission_play_npc",
        "target": 1,
        "check": "npc_game",
        "reward_pool": [{"gold": 5}],
    },
    {
        "key": "reach_morale",
        "description_key": "mission_reach_morale",
        "target_range": [70, 90],
        "check": "stat_threshold",
        "stat": "morale",
        "reward_pool": [{"food": 20}],
    },
    {
        "key": "reach_defense",
        "description_key": "mission_reach_defense",
        "target_range": [50, 80],
        "check": "stat_threshold",
        "stat": "defense",
        "reward_pool": [{"scrap": 25}],
    },
    {
        "key": "find_item",
        "description_key": "mission_find_item",
        "target": 1,
        "check": "item_found",
        "reward_pool": [{"gold": 8}],
    },
    {
        "key": "use_consumable",
        "description_key": "mission_use_consumable",
        "target": 1,
        "check": "consumable_used",
        "reward_pool": [{"scrap": 15}],
    },
    {
        "key": "earn_xp",
        "description_key": "mission_earn_xp",
        "target_range": [30, 60],
        "check": "xp_earned",
        "reward_pool": [{"gold": 5}],
    },
    {
        "key": "survive_event",
        "description_key": "mission_survive_event",
        "target": 1,
        "check": "event_survived",
        "reward_pool": [{"food": 20, "scrap": 20}],
    },
    {
        "key": "play_turns",
        "description_key": "mission_play_turns",
        "target_range": [3, 5],
        "check": "turns_played",
        "reward_pool": [{"gold": 8}],
    },
    {
        "key": "build_farm",
        "description_key": "mission_build_farm",
        "target": 1,
        "action": "build",
        "check": "build_specific",
        "building": "farm",
        "reward_pool": [{"food": 30}],
    },
    {
        "key": "build_watchtower",
        "description_key": "mission_build_watchtower",
        "target": 1,
        "action": "build",
        "check": "build_specific",
        "building": "watchtower",
        "reward_pool": [{"scrap": 20}],
    },
    {
        "key": "reach_population",
        "description_key": "mission_reach_population",
        "target_range": [55, 75],
        "check": "stat_threshold",
        "stat": "population",
        "reward_pool": [{"gold": 5}],
    },
    {
        "key": "earn_scrap_n",
        "description_key": "mission_earn_scrap",
        "target_range": [30, 60],
        "check": "scrap_earned",
        "reward_pool": [{"gold": 4}],
    },
    {
        "key": "collect_food_n",
        "description_key": "mission_collect_food",
        "target_range": [20, 50],
        "check": "food_earned",
        "reward_pool": [{"scrap": 20}],
    },
]


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def generate_daily_missions() -> list[dict]:
    """Pick 3 random missions from templates (no duplicates by key prefix).

    Randomises targets within ranges and picks a random reward from the pool.
    Returns a list of mission dicts ready for JSONB storage.
    """
    # Shuffle and pick unique templates by key prefix (first part before '_')
    shuffled = random.sample(MISSION_TEMPLATES, len(MISSION_TEMPLATES))
    selected: list[dict] = []
    used_prefixes: set[str] = set()

    for tmpl in shuffled:
        # Use the full key as prefix to avoid duplicates
        prefix = tmpl["key"]
        if prefix in used_prefixes:
            continue

        used_prefixes.add(prefix)
        mission = _instantiate_mission(tmpl)
        selected.append(mission)

        if len(selected) >= 3:
            break

    return selected


def _instantiate_mission(tmpl: dict) -> dict:
    """Create a concrete mission instance from a template."""
    # Determine target
    if "target_range" in tmpl:
        target = random.randint(tmpl["target_range"][0], tmpl["target_range"][1])
    else:
        target = tmpl["target"]

    # Pick reward
    reward = random.choice(tmpl["reward_pool"])

    # Build the mission key with target for uniqueness
    key = tmpl["key"]
    if "target_range" in tmpl:
        key = f"{tmpl['key']}_{target}"

    mission: dict = {
        "key": key,
        "description_key": tmpl["description_key"],
        "target": target,
        "progress": 0,
        "reward": deepcopy(reward),
        "completed": False,
        "check": tmpl["check"],
    }

    # Carry over optional fields used for progress checking
    if "action" in tmpl:
        mission["action"] = tmpl["action"]
    if "stat" in tmpl:
        mission["stat"] = tmpl["stat"]
    if "building" in tmpl:
        mission["building"] = tmpl["building"]

    return mission


# ---------------------------------------------------------------------------
# Progress checking
# ---------------------------------------------------------------------------

def check_mission_progress(
    missions: list[dict],
    action: str,
    turn_result_data: dict,
    game_state: dict,
) -> tuple[list[dict], list[dict]]:
    """Update mission progress based on what happened in a turn.

    Parameters
    ----------
    missions:
        Current list of mission dicts (mutated in place).
    action:
        The player action that was performed this turn.
    turn_result_data:
        Dict with turn outcome data::

            {
                "action": str,
                "gold_earned": int,
                "xp_earned": int,
                "item_found": bool,
                "event_survived": bool,
                "consumable_used": bool,
                "scrap_earned": int,
                "food_earned": int,
                "build_target": str | None,
                "npc_game_played": bool,
            }

    game_state:
        Dict of current game state values (post-turn) with keys like
        ``morale``, ``defense``, ``population``, etc.

    Returns
    -------
    tuple:
        (updated_missions, newly_completed_missions)
    """
    newly_completed: list[dict] = []

    for mission in missions:
        if mission["completed"]:
            continue

        check = mission["check"]
        progress_before = mission["progress"]

        if check == "action_count":
            # Count how many times the matching action was performed
            if action == mission.get("action"):
                mission["progress"] += 1

        elif check == "gold_earned":
            mission["progress"] += turn_result_data.get("gold_earned", 0)

        elif check == "xp_earned":
            mission["progress"] += turn_result_data.get("xp_earned", 0)

        elif check == "scrap_earned":
            mission["progress"] += max(0, turn_result_data.get("scrap_earned", 0))

        elif check == "food_earned":
            mission["progress"] += max(0, turn_result_data.get("food_earned", 0))

        elif check == "npc_game":
            if turn_result_data.get("npc_game_played", False):
                mission["progress"] += 1

        elif check == "stat_threshold":
            stat = mission.get("stat", "")
            current_value = game_state.get(stat, 0)
            # For threshold missions, progress is the current stat value
            mission["progress"] = current_value

        elif check == "item_found":
            if turn_result_data.get("item_found", False):
                mission["progress"] += 1

        elif check == "consumable_used":
            if turn_result_data.get("consumable_used", False):
                mission["progress"] += 1

        elif check == "event_survived":
            if turn_result_data.get("event_survived", False):
                mission["progress"] += 1

        elif check == "turns_played":
            # Every turn counts
            mission["progress"] += 1

        elif check == "build_specific":
            if action == "build" and turn_result_data.get("build_target") == mission.get("building"):
                mission["progress"] += 1

        # Check completion
        if not mission["completed"] and mission["progress"] >= mission["target"]:
            mission["completed"] = True
            newly_completed.append(mission)
            logger.info(
                "Mission completed: %s (target=%d)",
                mission["key"],
                mission["target"],
            )

    return missions, newly_completed


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def are_all_complete(missions: list[dict]) -> bool:
    """Return True if every mission in the list is completed."""
    return all(m["completed"] for m in missions) if missions else False


def format_missions_display(missions: list[dict], lang: str) -> str:
    """Format the mission list for display with progress bars.

    Parameters
    ----------
    missions:
        List of mission dicts.
    lang:
        Language code (``"en"`` or ``"ru"``).

    Returns
    -------
    str:
        Formatted multi-line text suitable for Telegram (Markdown).
    """
    lines: list[str] = []
    header = MISSION_STRINGS["dispatch_header"].get(lang, MISSION_STRINGS["dispatch_header"]["en"])
    lines.append(header)
    lines.append("")

    for i, mission in enumerate(missions, start=1):
        desc_key = mission["description_key"]
        desc_tmpl = MISSION_STRINGS.get(desc_key, {})
        desc = desc_tmpl.get(lang, desc_tmpl.get("en", desc_key))

        # Format description with target value
        try:
            desc = desc.format(n=mission["target"])
        except (KeyError, IndexError):
            pass

        progress = mission["progress"]
        target = mission["target"]
        completed = mission["completed"]

        # Progress bar
        if mission["check"] == "stat_threshold":
            bar = _stat_bar(progress, target)
        else:
            bar = _count_bar(progress, target)

        # Status emoji
        status = "\u2705" if completed else "\u2b1c"

        # Reward display
        reward_str = _format_reward(mission["reward"], lang)

        lines.append(f"{status} *{i}.* {desc}")
        lines.append(f"    {bar}  {progress}/{target}")
        lines.append(f"    {_reward_label(lang)}: {reward_str}")
        lines.append("")

    return "\n".join(lines)


def _count_bar(progress: int, target: int, length: int = 8) -> str:
    """Render a progress bar for count-based missions."""
    clamped = min(progress, target)
    filled = max(0, min(length, round(clamped / max(target, 1) * length)))
    return "\u2588" * filled + "\u2591" * (length - filled)


def _stat_bar(current: int, threshold: int, length: int = 8) -> str:
    """Render a progress bar for stat threshold missions."""
    clamped = min(current, threshold)
    filled = max(0, min(length, round(clamped / max(threshold, 1) * length)))
    return "\u2588" * filled + "\u2591" * (length - filled)


def _format_reward(reward: dict, lang: str) -> str:
    """Format a reward dict as a short string."""
    parts: list[str] = []
    emoji_map = {
        "scrap": "\U0001f529",
        "food": "\U0001f33e",
        "gold": "\U0001f4b0",
        "morale_bonus": "\U0001f60a",
    }
    for key, value in reward.items():
        emoji = emoji_map.get(key, "")
        parts.append(f"{emoji}+{value} {key}")
    return " ".join(parts)


def _reward_label(lang: str) -> str:
    """Return the localised 'Reward' label."""
    return MISSION_STRINGS["reward_label"].get(lang, MISSION_STRINGS["reward_label"]["en"])


# ---------------------------------------------------------------------------
# Localised strings
# ---------------------------------------------------------------------------

MISSION_STRINGS: dict[str, dict[str, str]] = {
    "dispatch_header": {
        "en": "\U0001f4cb *Daily Dispatch*",
        "ru": "\U0001f4cb *\u0415\u0436\u0435\u0434\u043d\u0435\u0432\u043d\u044b\u0435 \u0437\u0430\u0434\u0430\u043d\u0438\u044f*",
    },
    "reward_label": {
        "en": "Reward",
        "ru": "\u041d\u0430\u0433\u0440\u0430\u0434\u0430",
    },
    "dispatch_all_complete": {
        "en": "\U0001f389 *All missions complete!* Claim your dispatch bonus below.",
        "ru": "\U0001f389 *\u0412\u0441\u0435 \u0437\u0430\u0434\u0430\u043d\u0438\u044f \u0432\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u044b!* \u0417\u0430\u0431\u0435\u0440\u0438 \u0431\u043e\u043d\u0443\u0441 \u043d\u0438\u0436\u0435.",
    },
    "dispatch_bonus_claimed": {
        "en": "\u2705 Dispatch bonus already claimed! Come back tomorrow.",
        "ru": "\u2705 \u0411\u043e\u043d\u0443\u0441 \u0443\u0436\u0435 \u043f\u043e\u043b\u0443\u0447\u0435\u043d! \u0412\u043e\u0437\u0432\u0440\u0430\u0449\u0430\u0439\u0441\u044f \u0437\u0430\u0432\u0442\u0440\u0430.",
    },
    "dispatch_bonus_reward": {
        "en": (
            "\U0001f381 *Dispatch Bonus Claimed!*\n"
            "+50 XP | +10 \U0001f4b0 gold | +1 \U0001f7e2 uncommon item\n\n"
            "Come back tomorrow for new missions!"
        ),
        "ru": (
            "\U0001f381 *\u0411\u043e\u043d\u0443\u0441 \u043f\u043e\u043b\u0443\u0447\u0435\u043d!*\n"
            "+50 XP | +10 \U0001f4b0 \u0437\u043e\u043b\u043e\u0442\u0430 | +1 \U0001f7e2 \u043d\u0435\u043e\u0431\u044b\u0447\u043d\u044b\u0439 \u043f\u0440\u0435\u0434\u043c\u0435\u0442\n\n"
            "\u0412\u043e\u0437\u0432\u0440\u0430\u0449\u0430\u0439\u0441\u044f \u0437\u0430\u0432\u0442\u0440\u0430 \u0437\u0430 \u043d\u043e\u0432\u044b\u043c\u0438 \u0437\u0430\u0434\u0430\u043d\u0438\u044f\u043c\u0438!"
        ),
    },
    "dispatch_claim_button": {
        "en": "\U0001f381 Claim Dispatch Bonus",
        "ru": "\U0001f381 \u0417\u0430\u0431\u0440\u0430\u0442\u044c \u0431\u043e\u043d\u0443\u0441",
    },
    "dispatch_no_game": {
        "en": "You need an active game to view missions. Send /start first!",
        "ru": "\u0422\u0435\u0431\u0435 \u043d\u0443\u0436\u043d\u0430 \u0430\u043a\u0442\u0438\u0432\u043d\u0430\u044f \u0438\u0433\u0440\u0430. \u041e\u0442\u043f\u0440\u0430\u0432\u044c /start!",
    },
    "dispatch_mission_complete_inline": {
        "en": "\u2705 Mission complete: *{desc}* \u2014 {reward}",
        "ru": "\u2705 \u0417\u0430\u0434\u0430\u043d\u0438\u0435 \u0432\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u043e: *{desc}* \u2014 {reward}",
    },
    # --- Individual mission descriptions ---
    "mission_explore_n": {
        "en": "Explore the wasteland {n} time(s)",
        "ru": "\u0418\u0441\u0441\u043b\u0435\u0434\u043e\u0432\u0430\u0442\u044c \u043f\u0443\u0441\u0442\u043e\u0448\u044c {n} \u0440\u0430\u0437(\u0430)",
    },
    "mission_build_any": {
        "en": "Build any structure",
        "ru": "\u041f\u043e\u0441\u0442\u0440\u043e\u0438\u0442\u044c \u043b\u044e\u0431\u043e\u0435 \u0441\u0442\u0440\u043e\u0435\u043d\u0438\u0435",
    },
    "mission_trade_n": {
        "en": "Trade with outsiders {n} time(s)",
        "ru": "\u0422\u043e\u0440\u0433\u043e\u0432\u0430\u0442\u044c \u0441 \u0447\u0443\u0436\u0430\u043a\u0430\u043c\u0438 {n} \u0440\u0430\u0437(\u0430)",
    },
    "mission_defend_n": {
        "en": "Defend your settlement {n} time(s)",
        "ru": "\u0417\u0430\u0449\u0438\u0442\u0438\u0442\u044c \u043f\u043e\u0441\u0435\u043b\u0435\u043d\u0438\u0435 {n} \u0440\u0430\u0437(\u0430)",
    },
    "mission_diplomacy_n": {
        "en": "Engage in diplomacy {n} time(s)",
        "ru": "\u0417\u0430\u043d\u044f\u0442\u044c\u0441\u044f \u0434\u0438\u043f\u043b\u043e\u043c\u0430\u0442\u0438\u0435\u0439 {n} \u0440\u0430\u0437(\u0430)",
    },
    "mission_rest_n": {
        "en": "Rest and recover {n} time(s)",
        "ru": "\u041e\u0442\u0434\u043e\u0445\u043d\u0443\u0442\u044c {n} \u0440\u0430\u0437(\u0430)",
    },
    "mission_earn_gold": {
        "en": "Earn {n} gold",
        "ru": "\u0417\u0430\u0440\u0430\u0431\u043e\u0442\u0430\u0442\u044c {n} \u0437\u043e\u043b\u043e\u0442\u0430",
    },
    "mission_play_npc": {
        "en": "Play an NPC minigame",
        "ru": "\u0421\u044b\u0433\u0440\u0430\u0442\u044c \u0432 \u043c\u0438\u043d\u0438-\u0438\u0433\u0440\u0443 NPC",
    },
    "mission_reach_morale": {
        "en": "Reach {n} morale",
        "ru": "\u0414\u043e\u0441\u0442\u0438\u0447\u044c {n} \u043c\u043e\u0440\u0430\u043b\u0438",
    },
    "mission_reach_defense": {
        "en": "Reach {n} defense",
        "ru": "\u0414\u043e\u0441\u0442\u0438\u0447\u044c {n} \u043e\u0431\u043e\u0440\u043e\u043d\u044b",
    },
    "mission_find_item": {
        "en": "Find an item while exploring",
        "ru": "\u041d\u0430\u0439\u0442\u0438 \u043f\u0440\u0435\u0434\u043c\u0435\u0442 \u043f\u0440\u0438 \u0438\u0441\u0441\u043b\u0435\u0434\u043e\u0432\u0430\u043d\u0438\u0438",
    },
    "mission_use_consumable": {
        "en": "Use a consumable item",
        "ru": "\u0418\u0441\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u044c \u0440\u0430\u0441\u0445\u043e\u0434\u043d\u0438\u043a",
    },
    "mission_earn_xp": {
        "en": "Earn {n} XP",
        "ru": "\u041f\u043e\u043b\u0443\u0447\u0438\u0442\u044c {n} XP",
    },
    "mission_survive_event": {
        "en": "Survive a random event",
        "ru": "\u041f\u0435\u0440\u0435\u0436\u0438\u0442\u044c \u0441\u043b\u0443\u0447\u0430\u0439\u043d\u043e\u0435 \u0441\u043e\u0431\u044b\u0442\u0438\u0435",
    },
    "mission_play_turns": {
        "en": "Play {n} turns",
        "ru": "\u0421\u044b\u0433\u0440\u0430\u0442\u044c {n} \u0445\u043e\u0434\u043e\u0432",
    },
    "mission_build_farm": {
        "en": "Build a farm",
        "ru": "\u041f\u043e\u0441\u0442\u0440\u043e\u0438\u0442\u044c \u0444\u0435\u0440\u043c\u0443",
    },
    "mission_build_watchtower": {
        "en": "Build a watchtower",
        "ru": "\u041f\u043e\u0441\u0442\u0440\u043e\u0438\u0442\u044c \u0441\u0442\u043e\u0440\u043e\u0436\u0435\u0432\u0443\u044e \u0431\u0430\u0448\u043d\u044e",
    },
    "mission_reach_population": {
        "en": "Reach {n} population",
        "ru": "\u0414\u043e\u0441\u0442\u0438\u0447\u044c {n} \u043d\u0430\u0441\u0435\u043b\u0435\u043d\u0438\u044f",
    },
    "mission_earn_scrap": {
        "en": "Earn {n} scrap",
        "ru": "\u0417\u0430\u0440\u0430\u0431\u043e\u0442\u0430\u0442\u044c {n} \u0445\u043b\u0430\u043c\u0430",
    },
    "mission_collect_food": {
        "en": "Collect {n} food",
        "ru": "\u0421\u043e\u0431\u0440\u0430\u0442\u044c {n} \u0435\u0434\u044b",
    },
}

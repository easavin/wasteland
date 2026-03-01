"""Skill catalog and helpers for the RPG skill system.

Each skill has 3 ranks. Players earn 1 skill point every 5 levels and can
spend it to unlock or upgrade a skill. Each skill provides a flat, stackable
bonus per rank.

Skill effects are read by engine modules (resources, buildings, events) via
:func:`get_skill_rank` and :func:`get_skill_effect`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot.engine.game_state import GameState


# ---------------------------------------------------------------------------
# Skill catalog
# ---------------------------------------------------------------------------
# Each entry defines:
#   id          - unique slug (used as key in state.skills dict)
#   name        - dict with en/ru translations
#   description - dict with en/ru (uses {value} placeholder for rank-scaled)
#   max_rank    - always 3
#   per_rank    - numeric value per rank (interpretation depends on the skill)
#   category    - survival | economy | military | social
# ---------------------------------------------------------------------------

SKILLS: dict[str, dict] = {
    # === SURVIVAL ===
    "iron_stomach": {
        "name": {"en": "Iron Stomach", "ru": "Железный желудок"},
        "description": {
            "en": "Reduce food consumption by {value}% per rank.",
            "ru": "Снижает потребление еды на {value}% за ранг.",
        },
        "max_rank": 3,
        "per_rank": 8,  # 8%, 16%, 24% food consumption reduction
        "category": "survival",
    },
    "field_medic": {
        "name": {"en": "Field Medic", "ru": "Полевой медик"},
        "description": {
            "en": "Reduce population loss from events by {value} per rank.",
            "ru": "Снижает потери населения от событий на {value} за ранг.",
        },
        "max_rank": 3,
        "per_rank": 1,  # -1, -2, -3 pop loss from events
        "category": "survival",
    },
    "inspiring_leader": {
        "name": {"en": "Inspiring Leader", "ru": "Вдохновляющий лидер"},
        "description": {
            "en": "Boost morale gain from rest by +{value} per rank.",
            "ru": "Увеличивает прирост морали от отдыха на +{value} за ранг.",
        },
        "max_rank": 3,
        "per_rank": 3,  # +3, +6, +9 morale from rest
        "category": "survival",
    },
    # === ECONOMY ===
    "scrap_mastery": {
        "name": {"en": "Scrap Mastery", "ru": "Мастер утильсырья"},
        "description": {
            "en": "Reduce building scrap cost by {value}% per rank.",
            "ru": "Снижает стоимость строительства на {value}% за ранг.",
        },
        "max_rank": 3,
        "per_rank": 10,  # 10%, 20%, 30% cost reduction
        "category": "economy",
    },
    "haggler": {
        "name": {"en": "Haggler", "ru": "Торгаш"},
        "description": {
            "en": "Earn +{value} extra food when trading per rank.",
            "ru": "Получаете +{value} дополнительной еды при торговле за ранг.",
        },
        "max_rank": 3,
        "per_rank": 5,  # +5, +10, +15 food from trade
        "category": "economy",
    },
    "black_market": {
        "name": {"en": "Black Market", "ru": "Чёрный рынок"},
        "description": {
            "en": "Earn +{value} extra gold from trade and explore per rank.",
            "ru": "Получаете +{value} золота за торговлю и разведку за ранг.",
        },
        "max_rank": 3,
        "per_rank": 2,  # +2, +4, +6 gold from trade/explore
        "category": "economy",
    },
    "salvage_expert": {
        "name": {"en": "Salvage Expert", "ru": "Эксперт по утилю"},
        "description": {
            "en": "Find +{value} extra scrap when exploring per rank.",
            "ru": "Находите +{value} дополнительного хлама при разведке за ранг.",
        },
        "max_rank": 3,
        "per_rank": 5,  # +5, +10, +15 scrap from explore
        "category": "economy",
    },
    # === MILITARY ===
    "thick_skin": {
        "name": {"en": "Thick Skin", "ru": "Толстая кожа"},
        "description": {
            "en": "Reduce defense loss from events by {value}% per rank.",
            "ru": "Снижает потери обороны от событий на {value}% за ранг.",
        },
        "max_rank": 3,
        "per_rank": 10,  # 10%, 20%, 30% defense loss reduction
        "category": "military",
    },
    "fortification_expert": {
        "name": {"en": "Fortification Expert", "ru": "Эксперт фортификации"},
        "description": {
            "en": "Defense buildings produce +{value} extra per rank.",
            "ru": "Оборонительные здания дают +{value} дополнительно за ранг.",
        },
        "max_rank": 3,
        "per_rank": 1,  # +1, +2, +3 per defense building per turn
        "category": "military",
    },
    "patrol_routes": {
        "name": {"en": "Patrol Routes", "ru": "Патрульные маршруты"},
        "description": {
            "en": "Gain +{value} extra defense when defending per rank.",
            "ru": "Получаете +{value} дополнительной обороны при защите за ранг.",
        },
        "max_rank": 3,
        "per_rank": 3,  # +3, +6, +9 defense from defend action
        "category": "military",
    },
    "raiders_instinct": {
        "name": {"en": "Raider's Instinct", "ru": "Инстинкт рейдера"},
        "description": {
            "en": "Reduce population loss from combat events by {value} per rank.",
            "ru": "Снижает потери населения от боёв на {value} за ранг.",
        },
        "max_rank": 3,
        "per_rank": 1,  # -1, -2, -3 pop loss from combat events
        "category": "military",
    },
    # === SOCIAL ===
    "caravan_network": {
        "name": {"en": "Caravan Network", "ru": "Караванная сеть"},
        "description": {
            "en": "Trade events yield +{value}% more positive deltas per rank.",
            "ru": "Торговые события дают +{value}% больше бонусов за ранг.",
        },
        "max_rank": 3,
        "per_rank": 15,  # 15%, 30%, 45% boost to positive trade event deltas
        "category": "social",
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_skill_rank(state: GameState, skill_id: str) -> int:
    """Return the current rank (0-3) of *skill_id* for this game state."""
    return state.skills.get(skill_id, 0)


def get_skill_effect(state: GameState, skill_id: str) -> int | float:
    """Return the total numeric effect of *skill_id* at its current rank.

    This is ``rank * per_rank``.  Returns 0 if the skill is not learned.
    """
    rank = get_skill_rank(state, skill_id)
    if rank <= 0:
        return 0
    spec = SKILLS.get(skill_id)
    if spec is None:
        return 0
    return rank * spec["per_rank"]


def can_learn_skill(state: GameState, skill_id: str) -> tuple[bool, str]:
    """Check whether the player can spend a point on *skill_id*.

    Returns (True, "") or (False, reason).
    """
    if skill_id not in SKILLS:
        return False, "Unknown skill."

    if state.skill_points <= 0:
        return False, "No skill points available."

    spec = SKILLS[skill_id]
    current_rank = state.skills.get(skill_id, 0)
    if current_rank >= spec["max_rank"]:
        return False, f"{spec['name']['en']} is already at max rank."

    return True, ""


def learn_skill(state: GameState, skill_id: str) -> bool:
    """Spend a skill point to learn or upgrade *skill_id*.

    Mutates ``state.skills`` and ``state.skill_points`` in-place.
    Returns True on success, False if preconditions fail.
    """
    ok, _ = can_learn_skill(state, skill_id)
    if not ok:
        return False

    state.skills[skill_id] = state.skills.get(skill_id, 0) + 1
    state.skill_points -= 1
    return True


def get_skills_by_category() -> dict[str, list[str]]:
    """Group skill IDs by category for display."""
    cats: dict[str, list[str]] = {}
    for sid, spec in SKILLS.items():
        cat = spec["category"]
        cats.setdefault(cat, []).append(sid)
    return cats

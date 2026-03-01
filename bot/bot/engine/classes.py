"""Player class definitions for the RPG system.

Each class provides starting resource overrides, a passive ability,
and an affinity action that receives enhanced bonuses.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Class catalog
# ---------------------------------------------------------------------------

PLAYER_CLASSES: dict[str, dict] = {
    "scavenger": {
        "name": {"en": "Scavenger", "ru": "Старатель"},
        "description": {
            "en": "Wasteland salvage expert. Finds more when exploring the ruins.",
            "ru": "Мастер поиска в пустошах. Находит больше при исследовании руин.",
        },
        "emoji": "🔍",
        "starting_overrides": {"scrap": 110, "food": 90},
        "starting_rep_overrides": {},
        "passive_id": "resourceful",  # +20% scrap from explore
        "affinity_action": "explore",
    },
    "warden": {
        "name": {"en": "Warden", "ru": "Страж"},
        "description": {
            "en": "Military discipline leader. Walls hold longer under your command.",
            "ru": "Военный лидер. Стены дольше стоят под вашим командованием.",
        },
        "emoji": "🛡",
        "starting_overrides": {"defense": 50, "morale": 75},
        "starting_rep_overrides": {},
        "passive_id": "fortified",  # defense decay -1 instead of -3
        "affinity_action": "defend",
    },
    "trader": {
        "name": {"en": "Trader", "ru": "Торговец"},
        "description": {
            "en": "Caravan boss who knows the value of everything. Better trade deals.",
            "ru": "Глава каравана. Знает цену всему. Лучшие сделки.",
        },
        "emoji": "💰",
        "starting_overrides": {"food": 120, "scrap": 90},
        "starting_rep_overrides": {"traders_rep": 15},
        "passive_id": "connected",  # +10 food on trade, reduced scrap cost
        "affinity_action": "trade",
    },
    "diplomat": {
        "name": {"en": "Diplomat", "ru": "Дипломат"},
        "description": {
            "en": "Smooth talker who can defuse any crisis. Faction relations grow faster.",
            "ru": "Мастер переговоров. Отношения с фракциями растут быстрее.",
        },
        "emoji": "🕊",
        "starting_overrides": {"morale": 80, "population": 55},
        "starting_rep_overrides": {},
        "passive_id": "silver_tongue",  # diplomacy costs 5 food, +50% rep gains
        "affinity_action": "diplomacy",
    },
    "medic": {
        "name": {"en": "Medic", "ru": "Медик"},
        "description": {
            "en": "Former field surgeon. Keeps people alive against all odds.",
            "ru": "Бывший полевой хирург. Спасает людей вопреки всему.",
        },
        "emoji": "💊",
        "starting_overrides": {"population": 60, "food": 110},
        "starting_rep_overrides": {},
        "passive_id": "triage",  # starvation threshold 3, -1 pop loss from events
        "affinity_action": "rest",
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_starting_resources(class_id: str) -> dict[str, int]:
    """Return the starting resource dict for *class_id*.

    Merges class-specific overrides on top of the game defaults.
    """
    defaults = {
        "population": 50,
        "food": 100,
        "scrap": 80,
        "morale": 70,
        "defense": 30,
    }
    cls = PLAYER_CLASSES.get(class_id)
    if cls:
        defaults.update(cls["starting_overrides"])
    return defaults


def get_starting_rep_overrides(class_id: str) -> dict[str, int]:
    """Return faction reputation overrides for *class_id*."""
    cls = PLAYER_CLASSES.get(class_id)
    if cls:
        return dict(cls.get("starting_rep_overrides", {}))
    return {}


def get_passive(class_id: str) -> str:
    """Return the passive ability ID for *class_id*."""
    cls = PLAYER_CLASSES.get(class_id)
    return cls["passive_id"] if cls else ""


def get_starvation_threshold(class_id: str) -> int:
    """Medic class survives 3 starvation turns instead of 2."""
    return 3 if class_id == "medic" else 2

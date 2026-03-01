"""Random event catalog and per-turn event roller.

Each event has:
    id            - unique slug
    name          - dict with en/ru translations
    category      - environmental | population | combat | trade | lore | exploration
    min_turn      - earliest turn this event can fire
    min_zone      - minimum zone required (default 1)
    weight        - base selection weight (higher = more likely)
    conditions    - optional callable(state) -> bool; event is eligible only when True
    outcomes      - list of possible outcomes, each with:
                        weight, deltas (dict), narration_hint (str)
"""

from __future__ import annotations

import random
from math import ceil
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from bot.engine.game_state import GameState


# ---------------------------------------------------------------------------
# Helper type for readability
# ---------------------------------------------------------------------------
_Condition = Callable[["GameState"], bool]


def _always(_state: "GameState") -> bool:  # noqa: D401
    return True


# ---------------------------------------------------------------------------
# Event catalog
# ---------------------------------------------------------------------------

EVENT_CATALOG: list[dict] = [
    # ==== ZONE 1 EVENTS (original) ====

    # ---- ENVIRONMENTAL ----
    {
        "id": "dust_storm",
        "name": {"en": "Dust Storm", "ru": "Пылевая буря"},
        "category": "environmental",
        "min_turn": 1,
        "min_zone": 1,
        "weight": 12,
        "conditions": _always,
        "outcomes": [
            {
                "weight": 60,
                "deltas": {"food": -8, "morale": -5},
                "narration_hint": "A choking dust storm sweeps through, damaging crops and spirits.",
            },
            {
                "weight": 40,
                "deltas": {"food": -4, "scrap": 5},
                "narration_hint": "Strong winds tear at the settlement, but uncover buried scrap.",
            },
        ],
    },
    {
        "id": "water_source",
        "name": {"en": "Water Source Found", "ru": "Найден источник воды"},
        "category": "environmental",
        "min_turn": 5,
        "min_zone": 1,
        "weight": 8,
        "conditions": _always,
        "outcomes": [
            {
                "weight": 70,
                "deltas": {"food": 15, "morale": 5},
                "narration_hint": "Scouts discover a clean underground spring - a rare blessing.",
            },
            {
                "weight": 30,
                "deltas": {"food": 8, "population": 3},
                "narration_hint": "A water source attracts new settlers from the wastes.",
            },
        ],
    },
    {
        "id": "green_zone_discovery",
        "name": {"en": "Green Zone Discovery", "ru": "Найдена зелёная зона"},
        "category": "environmental",
        "min_turn": 10,
        "min_zone": 1,
        "weight": 6,
        "conditions": lambda s: s.population >= 30,
        "outcomes": [
            {
                "weight": 50,
                "deltas": {"food": 25, "morale": 8},
                "narration_hint": "An impossibly fertile patch of land is found - the earth is healing.",
            },
            {
                "weight": 30,
                "deltas": {"food": 15, "population": 5, "morale": 5},
                "narration_hint": "The green zone attracts families seeking safety.",
            },
            {
                "weight": 20,
                "deltas": {"food": 10, "scrap": -10, "morale": 3},
                "narration_hint": "Clearing the green zone for farming is costly but worthwhile.",
            },
        ],
    },
    {
        "id": "harvest_bounty",
        "name": {"en": "Harvest Bounty", "ru": "Богатый урожай"},
        "category": "environmental",
        "min_turn": 3,
        "min_zone": 1,
        "weight": 10,
        "conditions": lambda s: s.buildings.get("farm", 0) >= 1,
        "outcomes": [
            {
                "weight": 100,
                "deltas": {"food": 20, "morale": 5},
                "narration_hint": "The farms yield a bumper crop this turn.",
            },
        ],
    },
    # ---- POPULATION ----
    {
        "id": "wanderers",
        "name": {"en": "Wanderers Arrive", "ru": "Прибыли скитальцы"},
        "category": "population",
        "min_turn": 2,
        "min_zone": 1,
        "weight": 12,
        "conditions": _always,
        "outcomes": [
            {
                "weight": 60,
                "deltas": {"population": 5, "food": -5},
                "narration_hint": "A band of wanderers asks to join the settlement.",
            },
            {
                "weight": 25,
                "deltas": {"population": 3, "scrap": 10},
                "narration_hint": "Wanderers arrive bearing gifts of salvaged scrap.",
            },
            {
                "weight": 15,
                "deltas": {"population": 8, "food": -12, "morale": -3},
                "narration_hint": "A large group of desperate wanderers overwhelms resources.",
            },
        ],
    },
    {
        "id": "plague_outbreak",
        "name": {"en": "Plague Outbreak", "ru": "Вспышка чумы"},
        "category": "population",
        "min_turn": 8,
        "min_zone": 1,
        "weight": 7,
        "conditions": lambda s: s.population >= 40,
        "outcomes": [
            {
                "weight": 50,
                "deltas": {"population": -8, "morale": -10},
                "narration_hint": "A mysterious illness tears through the settlement.",
            },
            {
                "weight": 30,
                "deltas": {"population": -4, "morale": -5, "food": -5},
                "narration_hint": "Sickness spreads; quarantine measures strain food stores.",
            },
            {
                "weight": 20,
                "deltas": {"population": -2, "morale": -3},
                "narration_hint": "The clinic helps contain the outbreak, but not without losses.",
            },
        ],
    },
    {
        "id": "accord_refugees",
        "name": {"en": "Accord Refugees", "ru": "Беженцы Аккорда"},
        "category": "population",
        "min_turn": 12,
        "min_zone": 1,
        "weight": 7,
        "conditions": lambda s: s.traders_rep >= -10,
        "outcomes": [
            {
                "weight": 50,
                "deltas": {"population": 10, "food": -15, "morale": 3},
                "narration_hint": "Refugees from a collapsed trade zone seek shelter. They bring skills but need food.",
            },
            {
                "weight": 30,
                "deltas": {"population": 6, "scrap": 15, "food": -8},
                "narration_hint": "Displaced traders arrive with salvaged goods from ruined markets.",
            },
            {
                "weight": 20,
                "deltas": {"population": 4, "morale": -5, "defense": -5},
                "narration_hint": "The refugees carry tensions from their fallen settlements.",
            },
        ],
    },
    {
        "id": "morale_crisis",
        "name": {"en": "Morale Crisis", "ru": "Кризис морали"},
        "category": "population",
        "min_turn": 6,
        "min_zone": 1,
        "weight": 8,
        "conditions": lambda s: s.morale < 45,
        "outcomes": [
            {
                "weight": 60,
                "deltas": {"morale": -10, "population": -3},
                "narration_hint": "Discontent boils over - some settlers leave in the night.",
            },
            {
                "weight": 40,
                "deltas": {"morale": -7, "defense": -5},
                "narration_hint": "Guard shifts go unmanned as settlers lose hope.",
            },
        ],
    },
    # ---- COMBAT ----
    {
        "id": "raider_skirmish",
        "name": {"en": "Raider Skirmish", "ru": "Стычка с рейдерами"},
        "category": "combat",
        "min_turn": 3,
        "min_zone": 1,
        "weight": 14,
        "conditions": _always,
        "outcomes": [
            {
                "weight": 40,
                "deltas": {"defense": -8, "population": -2, "scrap": -5},
                "narration_hint": "Raiders probe your defenses. Losses on both sides.",
            },
            {
                "weight": 35,
                "deltas": {"food": -10, "defense": -3},
                "narration_hint": "A quick raid on the food stores before guards can react.",
            },
            {
                "weight": 25,
                "deltas": {"scrap": 10, "defense": -5, "morale": 5},
                "narration_hint": "The settlement repels raiders and salvages their gear.",
            },
        ],
    },
    {
        "id": "mutant_herd",
        "name": {"en": "Mutant Herd", "ru": "Стадо мутантов"},
        "category": "combat",
        "min_turn": 7,
        "min_zone": 1,
        "weight": 8,
        "conditions": _always,
        "outcomes": [
            {
                "weight": 50,
                "deltas": {"population": -3, "defense": -5, "food": 10},
                "narration_hint": "Mutant beasts stampede through. Some are killed for meat.",
            },
            {
                "weight": 30,
                "deltas": {"defense": -10, "morale": -5},
                "narration_hint": "Twisted creatures batter the walls. The damage is severe.",
            },
            {
                "weight": 20,
                "deltas": {"food": 15, "scrap": 5, "morale": 3},
                "narration_hint": "Hunters bring down the mutant herd. Feast tonight!",
            },
        ],
    },
    {
        "id": "hegemony_scouts",
        "name": {"en": "Hegemony Scouts", "ru": "Разведчики Гегемонии"},
        "category": "combat",
        "min_turn": 15,
        "min_zone": 1,
        "weight": 7,
        "conditions": lambda s: s.population >= 50,
        "outcomes": [
            {
                "weight": 40,
                "deltas": {"scrap": -20, "defense": -5, "morale": -5},
                "narration_hint": "Ex-military enforcers demand tribute in scrap. Resistance seems futile.",
            },
            {
                "weight": 35,
                "deltas": {"scrap": -10, "defense": 5},
                "narration_hint": "You negotiate a smaller tribute. They leave, for now.",
            },
            {
                "weight": 25,
                "deltas": {"defense": -10, "morale": 8, "scrap": 5},
                "narration_hint": "The settlement stands firm. The Hegemony scouts retreat empty-handed.",
            },
        ],
    },
    # ---- TRADE ----
    {
        "id": "trade_caravan",
        "name": {"en": "Trade Caravan", "ru": "Торговый караван"},
        "category": "trade",
        "min_turn": 4,
        "min_zone": 1,
        "weight": 12,
        "conditions": _always,
        "outcomes": [
            {
                "weight": 50,
                "deltas": {"food": 15, "scrap": -10, "morale": 3, "gold": 3},
                "narration_hint": "A merchant caravan offers food for scrap at fair prices. They pay in gold too.",
            },
            {
                "weight": 30,
                "deltas": {"scrap": 12, "food": -8, "gold": 5},
                "narration_hint": "Traders want food - they offer quality salvage and gold in return.",
            },
            {
                "weight": 20,
                "deltas": {"food": 10, "scrap": 10, "morale": 5, "gold": 8},
                "narration_hint": "A generous caravan shares supplies freely and leaves a pouch of gold.",
            },
        ],
    },
    {
        "id": "faction_civil_war",
        "name": {"en": "Faction Civil War", "ru": "Гражданская война фракции"},
        "category": "trade",
        "min_turn": 20,
        "min_zone": 1,
        "weight": 5,
        "conditions": lambda s: (
            s.raiders_rep > 20 or s.traders_rep > 20 or s.remnants_rep > 20
        ),
        "outcomes": [
            {
                "weight": 50,
                "deltas": {"scrap": 20, "morale": -5},
                "narration_hint": "A nearby faction splinters. Refugees bring scrap but also fear.",
            },
            {
                "weight": 50,
                "deltas": {"population": 5, "defense": -5, "food": -10},
                "narration_hint": "Faction infighting spills over. Displaced fighters seek refuge.",
            },
        ],
    },
    # ---- LORE ----
    {
        "id": "network_broadcast",
        "name": {"en": "The Network's Broadcast", "ru": "Трансляция Сети"},
        "category": "lore",
        "min_turn": 8,
        "min_zone": 1,
        "weight": 7,
        "conditions": _always,
        "outcomes": [
            {
                "weight": 40,
                "deltas": {"morale": -8, "population": -2},
                "narration_hint": (
                    "A crackling broadcast fills the airwaves with propaganda. "
                    "Some settlers believe the lies and slip away in the night."
                ),
            },
            {
                "weight": 35,
                "deltas": {"morale": 5, "defense": -3},
                "narration_hint": (
                    "The Network promises safety in exchange for loyalty. "
                    "Your people rally against the manipulation, but guards are distracted."
                ),
            },
            {
                "weight": 25,
                "deltas": {"morale": -3, "scrap": 8},
                "narration_hint": (
                    "You jam the signal and scavenge the relay equipment for parts."
                ),
            },
        ],
    },
    {
        "id": "thinking_machine_signal",
        "name": {"en": "Thinking Machine Signal", "ru": "Сигнал Мыслящей Машины"},
        "category": "lore",
        "min_turn": 18,
        "min_zone": 1,
        "weight": 5,
        "conditions": lambda s: s.remnants_rep >= 0,
        "outcomes": [
            {
                "weight": 35,
                "deltas": {"scrap": 25, "morale": -5},
                "narration_hint": (
                    "A rogue AI offers blueprints through encoded transmissions. "
                    "The tech is invaluable, but its motives are unsettling."
                ),
            },
            {
                "weight": 35,
                "deltas": {"defense": 10, "morale": -8},
                "narration_hint": (
                    "The machine offers to automate your defenses. "
                    "Effective, but your people fear what they cannot understand."
                ),
            },
            {
                "weight": 30,
                "deltas": {"population": -3, "scrap": 15, "defense": 5},
                "narration_hint": (
                    "A few settlers vanish near the signal source. "
                    "Those who return bring advanced components."
                ),
            },
        ],
    },
    {
        "id": "digital_cache",
        "name": {"en": "Digital Cache", "ru": "Цифровой тайник"},
        "category": "lore",
        "min_turn": 10,
        "min_zone": 1,
        "weight": 6,
        "conditions": _always,
        "outcomes": [
            {
                "weight": 50,
                "deltas": {"scrap": 20, "morale": 5},
                "narration_hint": (
                    "Explorers uncover a pre-Collapse data archive. "
                    "The technical knowledge within is priceless."
                ),
            },
            {
                "weight": 30,
                "deltas": {"morale": 10, "defense": 3},
                "narration_hint": (
                    "Old-world records reveal defensive strategies that still work."
                ),
            },
            {
                "weight": 20,
                "deltas": {"morale": -5, "scrap": 10},
                "narration_hint": (
                    "The archive contains disturbing truths about the Collapse. "
                    "Some wish it had stayed buried."
                ),
            },
        ],
    },
    # ---- EXPLORATION ----
    {
        "id": "tech_salvage",
        "name": {"en": "Tech Salvage", "ru": "Технологическая находка"},
        "category": "exploration",
        "min_turn": 5,
        "min_zone": 1,
        "weight": 10,
        "conditions": _always,
        "outcomes": [
            {
                "weight": 60,
                "deltas": {"scrap": 20, "morale": 3},
                "narration_hint": "A collapsed building yields a trove of usable technology.",
            },
            {
                "weight": 40,
                "deltas": {"scrap": 12, "defense": 5},
                "narration_hint": "Military-grade equipment is salvaged from an old depot.",
            },
        ],
    },

    # ==== ZONE 2+ EVENTS ====
    {
        "id": "hegemony_patrol",
        "name": {"en": "Hegemony Patrol", "ru": "Патруль Гегемонии"},
        "category": "combat",
        "min_turn": 1,
        "min_zone": 2,
        "weight": 10,
        "conditions": _always,
        "outcomes": [
            {
                "weight": 50,
                "deltas": {"defense": -12, "population": -4, "scrap": -10},
                "narration_hint": "A heavily armed Hegemony patrol attacks without warning.",
            },
            {
                "weight": 30,
                "deltas": {"gold": -8, "defense": -5},
                "narration_hint": "The patrol demands gold tribute. You pay to avoid bloodshed.",
            },
            {
                "weight": 20,
                "deltas": {"defense": -8, "morale": 10, "scrap": 15},
                "narration_hint": "Your defenders ambush the patrol and seize their supplies.",
            },
        ],
    },
    {
        "id": "toxic_rain",
        "name": {"en": "Toxic Rain", "ru": "Токсичный дождь"},
        "category": "environmental",
        "min_turn": 1,
        "min_zone": 2,
        "weight": 8,
        "conditions": _always,
        "outcomes": [
            {
                "weight": 60,
                "deltas": {"food": -15, "morale": -8, "population": -2},
                "narration_hint": "Acid rain falls for hours, poisoning crops and sickening settlers.",
            },
            {
                "weight": 40,
                "deltas": {"food": -10, "scrap": 8},
                "narration_hint": "The toxic rain corrodes structures but exposes metal beneath.",
            },
        ],
    },
    {
        "id": "rare_mineral_vein",
        "name": {"en": "Rare Mineral Vein", "ru": "Жила редких минералов"},
        "category": "exploration",
        "min_turn": 1,
        "min_zone": 2,
        "weight": 7,
        "conditions": _always,
        "outcomes": [
            {
                "weight": 50,
                "deltas": {"scrap": 30, "gold": 10},
                "narration_hint": "Miners discover a vein of pre-Collapse alloy. Worth a fortune.",
            },
            {
                "weight": 50,
                "deltas": {"scrap": 15, "gold": 5, "population": -2},
                "narration_hint": "The mine yields riches but a cave-in claims lives.",
            },
        ],
    },

    # ==== ZONE 3+ EVENTS ====
    {
        "id": "machine_uprising",
        "name": {"en": "Machine Uprising", "ru": "Восстание машин"},
        "category": "combat",
        "min_turn": 1,
        "min_zone": 3,
        "weight": 8,
        "conditions": _always,
        "outcomes": [
            {
                "weight": 40,
                "deltas": {"defense": -15, "population": -5, "scrap": -15},
                "narration_hint": "Automated defense systems turn hostile. Your own machines attack.",
            },
            {
                "weight": 30,
                "deltas": {"defense": -10, "morale": -10},
                "narration_hint": "Rogue drones patrol the perimeter, firing at anything that moves.",
            },
            {
                "weight": 30,
                "deltas": {"scrap": 25, "defense": 5, "population": -3},
                "narration_hint": "After heavy losses, you reprogram the machines. They serve you now.",
            },
        ],
    },
    {
        "id": "great_storm",
        "name": {"en": "The Great Storm", "ru": "Великая буря"},
        "category": "environmental",
        "min_turn": 1,
        "min_zone": 3,
        "weight": 7,
        "conditions": _always,
        "outcomes": [
            {
                "weight": 60,
                "deltas": {"food": -20, "defense": -15, "morale": -10},
                "narration_hint": "A cataclysmic storm batters the settlement for days. Everything suffers.",
            },
            {
                "weight": 40,
                "deltas": {"food": -10, "defense": -8, "scrap": 15},
                "narration_hint": "The storm is devastating but washes up debris from distant ruins.",
            },
        ],
    },

    # ==== ZONE 4+ EVENTS ====
    {
        "id": "network_siege",
        "name": {"en": "The Network Siege", "ru": "Осада Сети"},
        "category": "combat",
        "min_turn": 1,
        "min_zone": 4,
        "weight": 8,
        "conditions": _always,
        "outcomes": [
            {
                "weight": 50,
                "deltas": {"defense": -20, "population": -8, "food": -15, "morale": -10},
                "narration_hint": "The Network launches a full assault on the settlement. A desperate battle.",
            },
            {
                "weight": 30,
                "deltas": {"defense": -15, "scrap": -20, "gold": -10},
                "narration_hint": "Network agents sabotage infrastructure and loot the treasury.",
            },
            {
                "weight": 20,
                "deltas": {"defense": -10, "morale": 15, "gold": 20, "scrap": 20},
                "narration_hint": "Against all odds, you break the siege and capture their war chest.",
            },
        ],
    },
    {
        "id": "ancient_bunker",
        "name": {"en": "Ancient Bunker", "ru": "Древний бункер"},
        "category": "exploration",
        "min_turn": 1,
        "min_zone": 4,
        "weight": 6,
        "conditions": _always,
        "outcomes": [
            {
                "weight": 40,
                "deltas": {"scrap": 40, "gold": 15, "morale": 8},
                "narration_hint": "A pre-Collapse military bunker is cracked open. Treasure beyond measure.",
            },
            {
                "weight": 30,
                "deltas": {"scrap": 25, "defense": 10, "population": -3},
                "narration_hint": "The bunker's automated defenses activate before you secure it.",
            },
            {
                "weight": 30,
                "deltas": {"gold": 10, "morale": -8},
                "narration_hint": "Inside the bunker: records of atrocities committed before the Collapse.",
            },
        ],
    },

    # ==== ADDITIONAL ZONE 2 EVENTS ====
    {
        "id": "wasting_resurgence",
        "name": {"en": "Wasting Resurgence", "ru": "Возрождение Чумы"},
        "category": "population",
        "min_turn": 1,
        "min_zone": 2,
        "weight": 7,
        "conditions": lambda s: s.population >= 40,
        "outcomes": [
            {
                "weight": 50,
                "deltas": {"population": -6, "morale": -8, "food": -5},
                "narration_hint": "The Wasting flares up in your settlement. Quarantine empties the streets.",
            },
            {
                "weight": 30,
                "deltas": {"population": -3, "morale": -5},
                "narration_hint": "A milder strain of The Wasting passes through. Survivors develop immunity.",
            },
            {
                "weight": 20,
                "deltas": {"population": -2, "morale": 5, "scrap": 10},
                "narration_hint": "Your medics contain the outbreak quickly. Abandoned quarantine zones yield supplies.",
            },
        ],
    },
    {
        "id": "smuggler_contact",
        "name": {"en": "Smuggler Contact", "ru": "Контрабандист"},
        "category": "trade",
        "min_turn": 1,
        "min_zone": 2,
        "weight": 8,
        "conditions": _always,
        "outcomes": [
            {
                "weight": 40,
                "deltas": {"gold": 8, "scrap": 15, "morale": -3},
                "narration_hint": "A shady smuggler offers rare goods. The deal feels wrong but the price is right.",
            },
            {
                "weight": 35,
                "deltas": {"gold": 5, "food": 12},
                "narration_hint": "A smuggler trades contraband food supplies for gold. No questions asked.",
            },
            {
                "weight": 25,
                "deltas": {"gold": -5, "morale": -5},
                "narration_hint": "The smuggler's goods turn out to be worthless. You've been had.",
            },
        ],
    },

    # ==== ADDITIONAL ZONE 3 EVENTS ====
    {
        "id": "drone_swarm",
        "name": {"en": "Drone Swarm", "ru": "Рой дронов"},
        "category": "combat",
        "min_turn": 1,
        "min_zone": 3,
        "weight": 7,
        "conditions": _always,
        "outcomes": [
            {
                "weight": 45,
                "deltas": {"defense": -12, "population": -4, "morale": -8},
                "narration_hint": "Autonomous combat drones swarm the settlement in formation. Cold, precise, lethal.",
            },
            {
                "weight": 30,
                "deltas": {"defense": -8, "scrap": 20},
                "narration_hint": "After repelling the drone swarm, your engineers salvage their components.",
            },
            {
                "weight": 25,
                "deltas": {"defense": -5, "scrap": 30, "gold": 5},
                "narration_hint": "Your Radio Tower jams the swarm's coordination. Easy pickings after that.",
            },
        ],
    },
    {
        "id": "underground_market",
        "name": {"en": "Underground Market", "ru": "Подпольный рынок"},
        "category": "trade",
        "min_turn": 1,
        "min_zone": 3,
        "weight": 6,
        "conditions": lambda s: s.gold >= 5,
        "outcomes": [
            {
                "weight": 40,
                "deltas": {"gold": -5, "scrap": 35, "food": 15},
                "narration_hint": "An underground market appears in the ruins. Prices are steep but selection is unmatched.",
            },
            {
                "weight": 35,
                "deltas": {"gold": 12, "morale": -3},
                "narration_hint": "You sell scavenged pre-Collapse tech at the black market for a hefty profit.",
            },
            {
                "weight": 25,
                "deltas": {"gold": -3, "defense": 8, "scrap": 10},
                "narration_hint": "Military hardware at the underground market. Expensive but worth every coin.",
            },
        ],
    },
    {
        "id": "remnant_expedition",
        "name": {"en": "Remnant Expedition", "ru": "Экспедиция Осколков"},
        "category": "exploration",
        "min_turn": 1,
        "min_zone": 3,
        "weight": 6,
        "conditions": lambda s: s.remnants_rep >= 10,
        "outcomes": [
            {
                "weight": 40,
                "deltas": {"scrap": 25, "morale": 5, "gold": 5},
                "narration_hint": "Remnant scholars invite you on an expedition to a pre-Collapse research facility.",
            },
            {
                "weight": 35,
                "deltas": {"scrap": 15, "defense": 5, "population": -2},
                "narration_hint": "The expedition finds valuable tech but the facility's traps claim two settlers.",
            },
            {
                "weight": 25,
                "deltas": {"morale": 10, "food": 10},
                "narration_hint": "The Remnants share their hydroponics knowledge. Your farms will never be the same.",
            },
        ],
    },

    # ==== ADDITIONAL ZONE 4 EVENTS ====
    {
        "id": "data_heist",
        "name": {"en": "Network Data Heist", "ru": "Кража данных Сети"},
        "category": "lore",
        "min_turn": 1,
        "min_zone": 4,
        "weight": 6,
        "conditions": _always,
        "outcomes": [
            {
                "weight": 35,
                "deltas": {"gold": 20, "defense": -10, "morale": 5},
                "narration_hint": "Your hackers breach a Network data vault. The information is worth a fortune.",
            },
            {
                "weight": 35,
                "deltas": {"gold": 10, "scrap": 20, "population": -3},
                "narration_hint": "The data heist succeeds but Network countermeasures take their toll.",
            },
            {
                "weight": 30,
                "deltas": {"defense": -15, "morale": -10, "gold": -5},
                "narration_hint": "The heist fails. The Network retaliates with a targeted strike on your settlement.",
            },
        ],
    },
    {
        "id": "warlord_alliance",
        "name": {"en": "Warlord Alliance", "ru": "Альянс полевых командиров"},
        "category": "combat",
        "min_turn": 1,
        "min_zone": 4,
        "weight": 7,
        "conditions": lambda s: s.raiders_rep >= 20,
        "outcomes": [
            {
                "weight": 40,
                "deltas": {"defense": 15, "morale": 8, "food": -15},
                "narration_hint": "Raider warlords offer a temporary alliance. Their fighters bolster your walls.",
            },
            {
                "weight": 35,
                "deltas": {"scrap": 20, "gold": 8, "morale": -5},
                "narration_hint": "The warlords bring tribute. Your people are uneasy about these new allies.",
            },
            {
                "weight": 25,
                "deltas": {"defense": -10, "food": -10, "population": -3},
                "narration_hint": "The alliance was a trap. Raiders attack from inside while their allies hit the walls.",
            },
        ],
    },

    # ==== ZONE 5 EVENTS ====
    {
        "id": "the_reckoning",
        "name": {"en": "The Reckoning", "ru": "Расплата"},
        "category": "combat",
        "min_turn": 1,
        "min_zone": 5,
        "weight": 7,
        "conditions": _always,
        "outcomes": [
            {
                "weight": 50,
                "deltas": {"defense": -25, "population": -10, "food": -20, "morale": -15},
                "narration_hint": "Every faction unites against you. The wasteland itself seems to fight back.",
            },
            {
                "weight": 30,
                "deltas": {"defense": -15, "population": -5, "gold": -15},
                "narration_hint": "Mercenary armies demand everything you have. Surrender or die.",
            },
            {
                "weight": 20,
                "deltas": {"morale": 20, "defense": 10, "gold": 30, "scrap": 30},
                "narration_hint": "You emerge victorious from the greatest battle the wasteland has seen.",
            },
        ],
    },
    {
        "id": "paradise_found",
        "name": {"en": "Paradise Found", "ru": "Найденный рай"},
        "category": "exploration",
        "min_turn": 1,
        "min_zone": 5,
        "weight": 5,
        "conditions": lambda s: s.level >= 25,
        "outcomes": [
            {
                "weight": 40,
                "deltas": {"food": 40, "morale": 15, "population": 10, "gold": 15},
                "narration_hint": "An untouched valley, hidden from the world since the Collapse. A true paradise.",
            },
            {
                "weight": 35,
                "deltas": {"food": 25, "scrap": 30, "gold": 10},
                "narration_hint": "The valley has been picked over by someone before you. Still, remarkable finds.",
            },
            {
                "weight": 25,
                "deltas": {"food": 15, "population": -5, "morale": -10, "scrap": 40, "gold": 20},
                "narration_hint": "Paradise was guarded. Automated defenses exact a heavy price for entry.",
            },
        ],
    },
    {
        "id": "machine_god",
        "name": {"en": "The Machine God", "ru": "Машинный бог"},
        "category": "lore",
        "min_turn": 1,
        "min_zone": 5,
        "weight": 5,
        "conditions": _always,
        "outcomes": [
            {
                "weight": 35,
                "deltas": {"defense": 20, "scrap": 40, "morale": -15},
                "narration_hint": "A Thinking Machine of immense power offers allegiance. Your people are terrified.",
            },
            {
                "weight": 35,
                "deltas": {"gold": 25, "morale": 10, "defense": 5},
                "narration_hint": "You negotiate with the Machine God. It provides resources in exchange for data about human settlement patterns.",
            },
            {
                "weight": 30,
                "deltas": {"defense": -20, "population": -8, "scrap": -20},
                "narration_hint": "The Machine God's offer was deception. Your systems are compromised, your people scattered.",
            },
        ],
    },
]


# ---------------------------------------------------------------------------
# Event roller
# ---------------------------------------------------------------------------


def _event_probability(turn_number: int, zone: int) -> float:
    """Return the probability [0.0, 1.0] that an event fires this turn."""
    base = 0.25 + turn_number * 0.005  # slow ramp
    base = min(base, 0.40 + zone * 0.05)  # zone bonus
    return min(base, 0.75)  # hard cap


def roll_random_event(
    state: GameState,
    turn_number: int,
) -> dict | None:
    """Attempt to fire a random event for this turn.

    Returns ``None`` if no event fires (probability miss) or no eligible
    events exist.  Otherwise returns a dict with::

        {"id": str, "name": str, "deltas": dict, "narration_hint": str}
    """
    zone = state.zone

    # Step 1: probability gate
    if random.random() > _event_probability(turn_number, zone):
        return None

    # Step 2: filter eligible events (turn gate + zone gate + conditions)
    eligible: list[dict] = []
    for event in EVENT_CATALOG:
        if turn_number < event["min_turn"]:
            continue
        if zone < event.get("min_zone", 1):
            continue
        condition_fn = event.get("conditions", _always)
        try:
            if not condition_fn(state):
                continue
        except Exception:
            # Malformed condition -- skip the event.
            continue
        eligible.append(event)

    if not eligible:
        return None

    # Step 3: weighted random selection of event
    weights = [e["weight"] for e in eligible]
    chosen_event = random.choices(eligible, weights=weights, k=1)[0]

    # Step 4: weighted outcome within the chosen event
    outcomes = chosen_event["outcomes"]
    outcome_weights = [o["weight"] for o in outcomes]
    chosen_outcome = random.choices(outcomes, weights=outcome_weights, k=1)[0]

    # Step 5: apply zone difficulty multiplier to negative deltas
    from bot.engine.progression import get_zone_difficulty_multiplier

    multiplier = get_zone_difficulty_multiplier(zone)
    final_deltas: dict[str, int] = {}
    for k, v in chosen_outcome["deltas"].items():
        if v < 0 and multiplier != 1.0:
            final_deltas[k] = ceil(v * multiplier)  # ceil preserves negative direction
        else:
            final_deltas[k] = v

    # Step 6: apply skill modifiers to event deltas
    from bot.engine.skills import get_skill_effect

    category = chosen_event.get("category", "")

    # Skill: Thick Skin — reduce defense losses from events by X%
    thick_skin_pct = get_skill_effect(state, "thick_skin")
    if thick_skin_pct > 0 and "defense" in final_deltas and final_deltas["defense"] < 0:
        reduced = ceil(final_deltas["defense"] * (1.0 - thick_skin_pct / 100.0))
        final_deltas["defense"] = min(reduced, -1) if final_deltas["defense"] < 0 else reduced

    # Skill: Raider's Instinct — reduce pop loss from combat events
    if category == "combat":
        ri_reduction = int(get_skill_effect(state, "raiders_instinct"))
        if ri_reduction > 0 and "population" in final_deltas and final_deltas["population"] < 0:
            final_deltas["population"] = min(0, final_deltas["population"] + ri_reduction)

    # Skill: Field Medic — reduce pop loss from any event
    fm_reduction = int(get_skill_effect(state, "field_medic"))
    if fm_reduction > 0 and "population" in final_deltas and final_deltas["population"] < 0:
        final_deltas["population"] = min(0, final_deltas["population"] + fm_reduction)

    # Skill: Caravan Network — boost positive deltas from trade events
    if category == "trade":
        cn_pct = get_skill_effect(state, "caravan_network")
        if cn_pct > 0:
            for k, v in final_deltas.items():
                if v > 0:
                    final_deltas[k] = ceil(v * (1.0 + cn_pct / 100.0))

    return {
        "id": chosen_event["id"],
        "name": chosen_event["name"].get("en", chosen_event["id"]),
        "deltas": final_deltas,
        "narration_hint": chosen_outcome["narration_hint"],
    }

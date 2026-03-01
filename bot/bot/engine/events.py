"""Random event catalog and per-turn event roller.

Each event has:
    id            - unique slug
    name          - dict with en/ru translations
    category      - environmental | population | combat | trade | lore | exploration
    min_turn      - earliest turn this event can fire
    weight        - base selection weight (higher = more likely)
    conditions    - optional callable(state) -> bool; event is eligible only when True
    outcomes      - list of possible outcomes, each with:
                        weight, deltas (dict), narration_hint (str)
"""

from __future__ import annotations

import random
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
    # ---- ENVIRONMENTAL ----
    {
        "id": "dust_storm",
        "name": {"en": "Dust Storm", "ru": "\u041f\u044b\u043b\u0435\u0432\u0430\u044f \u0431\u0443\u0440\u044f"},
        "category": "environmental",
        "min_turn": 1,
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
        "name": {"en": "Water Source Found", "ru": "\u041d\u0430\u0439\u0434\u0435\u043d \u0438\u0441\u0442\u043e\u0447\u043d\u0438\u043a \u0432\u043e\u0434\u044b"},
        "category": "environmental",
        "min_turn": 5,
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
        "name": {"en": "Green Zone Discovery", "ru": "\u041d\u0430\u0439\u0434\u0435\u043d\u0430 \u0437\u0435\u043b\u0451\u043d\u0430\u044f \u0437\u043e\u043d\u0430"},
        "category": "environmental",
        "min_turn": 10,
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
        "name": {"en": "Harvest Bounty", "ru": "\u0411\u043e\u0433\u0430\u0442\u044b\u0439 \u0443\u0440\u043e\u0436\u0430\u0439"},
        "category": "environmental",
        "min_turn": 3,
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
        "name": {"en": "Wanderers Arrive", "ru": "\u041f\u0440\u0438\u0431\u044b\u043b\u0438 \u0441\u043a\u0438\u0442\u0430\u043b\u044c\u0446\u044b"},
        "category": "population",
        "min_turn": 2,
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
        "name": {"en": "Plague Outbreak", "ru": "\u0412\u0441\u043f\u044b\u0448\u043a\u0430 \u0447\u0443\u043c\u044b"},
        "category": "population",
        "min_turn": 8,
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
        "name": {"en": "Accord Refugees", "ru": "\u0411\u0435\u0436\u0435\u043d\u0446\u044b \u0410\u043a\u043a\u043e\u0440\u0434\u0430"},
        "category": "population",
        "min_turn": 12,
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
        "name": {"en": "Morale Crisis", "ru": "\u041a\u0440\u0438\u0437\u0438\u0441 \u043c\u043e\u0440\u0430\u043b\u0438"},
        "category": "population",
        "min_turn": 6,
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
        "name": {"en": "Raider Skirmish", "ru": "\u0421\u0442\u044b\u0447\u043a\u0430 \u0441 \u0440\u0435\u0439\u0434\u0435\u0440\u0430\u043c\u0438"},
        "category": "combat",
        "min_turn": 3,
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
        "name": {"en": "Mutant Herd", "ru": "\u0421\u0442\u0430\u0434\u043e \u043c\u0443\u0442\u0430\u043d\u0442\u043e\u0432"},
        "category": "combat",
        "min_turn": 7,
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
        "name": {"en": "Hegemony Scouts", "ru": "\u0420\u0430\u0437\u0432\u0435\u0434\u0447\u0438\u043a\u0438 \u0413\u0435\u0433\u0435\u043c\u043e\u043d\u0438\u0438"},
        "category": "combat",
        "min_turn": 15,
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
        "name": {"en": "Trade Caravan", "ru": "\u0422\u043e\u0440\u0433\u043e\u0432\u044b\u0439 \u043a\u0430\u0440\u0430\u0432\u0430\u043d"},
        "category": "trade",
        "min_turn": 4,
        "weight": 12,
        "conditions": _always,
        "outcomes": [
            {
                "weight": 50,
                "deltas": {"food": 15, "scrap": -10, "morale": 3},
                "narration_hint": "A merchant caravan offers food for scrap at fair prices.",
            },
            {
                "weight": 30,
                "deltas": {"scrap": 12, "food": -8},
                "narration_hint": "Traders want food - they offer quality salvage in return.",
            },
            {
                "weight": 20,
                "deltas": {"food": 10, "scrap": 10, "morale": 5},
                "narration_hint": "A generous caravan shares supplies freely - is it a trap?",
            },
        ],
    },
    {
        "id": "faction_civil_war",
        "name": {"en": "Faction Civil War", "ru": "\u0413\u0440\u0430\u0436\u0434\u0430\u043d\u0441\u043a\u0430\u044f \u0432\u043e\u0439\u043d\u0430 \u0444\u0440\u0430\u043a\u0446\u0438\u0438"},
        "category": "trade",
        "min_turn": 20,
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
        "name": {"en": "The Network's Broadcast", "ru": "\u0422\u0440\u0430\u043d\u0441\u043b\u044f\u0446\u0438\u044f \u0421\u0435\u0442\u0438"},
        "category": "lore",
        "min_turn": 8,
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
        "name": {"en": "Thinking Machine Signal", "ru": "\u0421\u0438\u0433\u043d\u0430\u043b \u041c\u044b\u0441\u043b\u044f\u0449\u0435\u0439 \u041c\u0430\u0448\u0438\u043d\u044b"},
        "category": "lore",
        "min_turn": 18,
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
        "name": {"en": "Digital Cache", "ru": "\u0426\u0438\u0444\u0440\u043e\u0432\u043e\u0439 \u0442\u0430\u0439\u043d\u0438\u043a"},
        "category": "lore",
        "min_turn": 10,
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
        "name": {"en": "Tech Salvage", "ru": "\u0422\u0435\u0445\u043d\u043e\u043b\u043e\u0433\u0438\u0447\u0435\u0441\u043a\u0430\u044f \u043d\u0430\u0445\u043e\u0434\u043a\u0430"},
        "category": "exploration",
        "min_turn": 5,
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
]


# ---------------------------------------------------------------------------
# Event roller
# ---------------------------------------------------------------------------


def _event_probability(turn_number: int) -> float:
    """Return the probability [0.0, 1.0] that an event fires this turn."""
    if turn_number <= 5:
        return 0.20
    if turn_number <= 20:
        return 0.35
    if turn_number <= 40:
        return 0.50
    return 0.65


def roll_random_event(
    state: GameState,
    turn_number: int,
) -> dict | None:
    """Attempt to fire a random event for this turn.

    Returns ``None`` if no event fires (probability miss) or no eligible
    events exist.  Otherwise returns a dict with::

        {"id": str, "name": str, "deltas": dict, "narration_hint": str}
    """
    # Step 1: probability gate
    if random.random() > _event_probability(turn_number):
        return None

    # Step 2: filter eligible events
    eligible: list[dict] = []
    for event in EVENT_CATALOG:
        if turn_number < event["min_turn"]:
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

    return {
        "id": chosen_event["id"],
        "name": chosen_event["name"].get("en", chosen_event["id"]),
        "deltas": dict(chosen_outcome["deltas"]),
        "narration_hint": chosen_outcome["narration_hint"],
    }

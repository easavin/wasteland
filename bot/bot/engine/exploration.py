"""Interactive multi-step exploration system.

Each exploration scenario is a small state machine: the player picks a
location, then navigates 1-3 branching steps via inline-keyboard choices.
Each choice carries risk/reward parameters that are resolved into concrete
resource deltas by :func:`resolve_exploration_choice`.

Scenarios are selected with :func:`pick_scenario` using a zone-gated
weighted random.

Terminology
-----------
scenario  - a location with an intro prompt and a list of steps.
step      - a decision point inside a scenario (prompt + choices).
choice    - a single option at a step (button), with risk/reward spec.

i18n keys follow the pattern::

    explore_sc_{scenario_id}_intro
    explore_sc_{scenario_id}_s{step_index}
    explore_sc_{scenario_id}_c_{choice_id}
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from math import ceil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot.engine.game_state import GameState


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExplorationChoice:
    """A single selectable option within an exploration step."""

    id: str
    label_key: str
    risk: str  # "low" | "medium" | "high"
    scrap_range: tuple[int, int] = (0, 0)
    item_chance: float = 0.0
    gold_range: tuple[int, int] = (0, 0)
    pop_risk: int = 0
    morale_risk: int = 0
    next_step: int | None = None  # index into scenario steps, or None = resolve
    codex_entry: str | None = None


@dataclass(frozen=True)
class ExplorationStep:
    """A single decision point inside a scenario."""

    prompt_key: str
    choices: list[ExplorationChoice]


@dataclass(frozen=True)
class ExplorationScenario:
    """A complete multi-step exploration location."""

    id: str
    zone_min: int
    weight: int
    intro_key: str
    steps: list[ExplorationStep]


# ---------------------------------------------------------------------------
# Risk multipliers
# ---------------------------------------------------------------------------

_RISK_PENALTY_CHANCE: dict[str, float] = {
    "low": 0.10,
    "medium": 0.30,
    "high": 0.55,
}


# ---------------------------------------------------------------------------
# Scenario catalog
# ---------------------------------------------------------------------------

SCENARIOS: list[ExplorationScenario] = [
    # ======================================================================
    # ZONE 1
    # ======================================================================

    # 1. Abandoned Gas Station
    ExplorationScenario(
        id="gasstation",
        zone_min=1,
        weight=12,
        intro_key="explore_sc_gasstation_intro",
        steps=[
            ExplorationStep(
                prompt_key="explore_sc_gasstation_s0",
                choices=[
                    ExplorationChoice(
                        id="main",
                        label_key="explore_sc_gasstation_c_main",
                        risk="low",
                        scrap_range=(8, 15),
                        gold_range=(1, 3),
                        item_chance=0.15,
                    ),
                    ExplorationChoice(
                        id="storage",
                        label_key="explore_sc_gasstation_c_storage",
                        risk="medium",
                        scrap_range=(12, 22),
                        gold_range=(2, 5),
                        item_chance=0.25,
                        pop_risk=1,
                    ),
                    ExplorationChoice(
                        id="cellar",
                        label_key="explore_sc_gasstation_c_cellar",
                        risk="high",
                        scrap_range=(18, 30),
                        gold_range=(3, 8),
                        item_chance=0.40,
                        pop_risk=2,
                        morale_risk=3,
                        codex_entry="codex_old_fuel_ledger",
                    ),
                ],
            ),
        ],
    ),

    # 2. Collapsed Apartment Block
    ExplorationScenario(
        id="apartment",
        zone_min=1,
        weight=11,
        intro_key="explore_sc_apartment_intro",
        steps=[
            ExplorationStep(
                prompt_key="explore_sc_apartment_s0",
                choices=[
                    ExplorationChoice(
                        id="lobby",
                        label_key="explore_sc_apartment_c_lobby",
                        risk="low",
                        scrap_range=(6, 12),
                        gold_range=(0, 2),
                        item_chance=0.10,
                    ),
                    ExplorationChoice(
                        id="stairwell",
                        label_key="explore_sc_apartment_c_stairwell",
                        risk="medium",
                        scrap_range=(10, 20),
                        gold_range=(1, 4),
                        item_chance=0.20,
                        pop_risk=1,
                    ),
                    ExplorationChoice(
                        id="roof",
                        label_key="explore_sc_apartment_c_roof",
                        risk="high",
                        scrap_range=(15, 28),
                        gold_range=(2, 6),
                        item_chance=0.35,
                        pop_risk=2,
                        morale_risk=2,
                        codex_entry="codex_rooftop_signal",
                    ),
                ],
            ),
        ],
    ),

    # 3. Overgrown Market
    ExplorationScenario(
        id="market",
        zone_min=1,
        weight=10,
        intro_key="explore_sc_market_intro",
        steps=[
            ExplorationStep(
                prompt_key="explore_sc_market_s0",
                choices=[
                    ExplorationChoice(
                        id="stalls",
                        label_key="explore_sc_market_c_stalls",
                        risk="low",
                        scrap_range=(5, 10),
                        gold_range=(1, 3),
                        item_chance=0.10,
                    ),
                    ExplorationChoice(
                        id="pharmacy",
                        label_key="explore_sc_market_c_pharmacy",
                        risk="medium",
                        scrap_range=(8, 18),
                        gold_range=(2, 5),
                        item_chance=0.30,
                        pop_risk=1,
                        codex_entry="codex_pharmacy_notes",
                    ),
                    ExplorationChoice(
                        id="alley",
                        label_key="explore_sc_market_c_alley",
                        risk="high",
                        scrap_range=(14, 25),
                        gold_range=(3, 7),
                        item_chance=0.25,
                        pop_risk=2,
                        morale_risk=3,
                    ),
                ],
            ),
        ],
    ),

    # 4. Roadside Camp (two steps)
    ExplorationScenario(
        id="camp",
        zone_min=1,
        weight=10,
        intro_key="explore_sc_camp_intro",
        steps=[
            # Step 0: initial approach
            ExplorationStep(
                prompt_key="explore_sc_camp_s0",
                choices=[
                    ExplorationChoice(
                        id="tents",
                        label_key="explore_sc_camp_c_tents",
                        risk="low",
                        scrap_range=(6, 14),
                        gold_range=(1, 3),
                        item_chance=0.15,
                    ),
                    ExplorationChoice(
                        id="vehicle",
                        label_key="explore_sc_camp_c_vehicle",
                        risk="medium",
                        scrap_range=(10, 20),
                        gold_range=(2, 4),
                        item_chance=0.20,
                        pop_risk=1,
                    ),
                    ExplorationChoice(
                        id="tracks",
                        label_key="explore_sc_camp_c_tracks",
                        risk="low",
                        scrap_range=(0, 0),
                        next_step=1,
                    ),
                ],
            ),
            # Step 1: follow the tracks
            ExplorationStep(
                prompt_key="explore_sc_camp_s1",
                choices=[
                    ExplorationChoice(
                        id="cave",
                        label_key="explore_sc_camp_c_cave",
                        risk="high",
                        scrap_range=(16, 30),
                        gold_range=(4, 8),
                        item_chance=0.40,
                        pop_risk=2,
                        morale_risk=3,
                        codex_entry="codex_camp_cave_drawings",
                    ),
                    ExplorationChoice(
                        id="clearing",
                        label_key="explore_sc_camp_c_clearing",
                        risk="medium",
                        scrap_range=(10, 18),
                        gold_range=(2, 5),
                        item_chance=0.20,
                        pop_risk=1,
                    ),
                ],
            ),
        ],
    ),

    # 5. Old School Building (two steps)
    ExplorationScenario(
        id="school",
        zone_min=1,
        weight=9,
        intro_key="explore_sc_school_intro",
        steps=[
            # Step 0: ground floor
            ExplorationStep(
                prompt_key="explore_sc_school_s0",
                choices=[
                    ExplorationChoice(
                        id="classrooms",
                        label_key="explore_sc_school_c_classrooms",
                        risk="low",
                        scrap_range=(5, 12),
                        gold_range=(0, 2),
                        item_chance=0.10,
                    ),
                    ExplorationChoice(
                        id="cafeteria",
                        label_key="explore_sc_school_c_cafeteria",
                        risk="low",
                        scrap_range=(4, 10),
                        gold_range=(1, 3),
                        item_chance=0.15,
                    ),
                    ExplorationChoice(
                        id="office",
                        label_key="explore_sc_school_c_office",
                        risk="medium",
                        scrap_range=(8, 16),
                        gold_range=(2, 4),
                        item_chance=0.20,
                        next_step=1,
                    ),
                ],
            ),
            # Step 1: principal's office leads to hidden basement
            ExplorationStep(
                prompt_key="explore_sc_school_s1",
                choices=[
                    ExplorationChoice(
                        id="basement",
                        label_key="explore_sc_school_c_basement",
                        risk="high",
                        scrap_range=(18, 32),
                        gold_range=(4, 9),
                        item_chance=0.45,
                        pop_risk=2,
                        morale_risk=4,
                        codex_entry="codex_school_records",
                    ),
                    ExplorationChoice(
                        id="leave",
                        label_key="explore_sc_school_c_leave",
                        risk="low",
                        scrap_range=(4, 8),
                        gold_range=(1, 2),
                    ),
                ],
            ),
        ],
    ),

    # ======================================================================
    # ZONE 2
    # ======================================================================

    # 6. Ruined Factory Complex (two steps)
    ExplorationScenario(
        id="factory",
        zone_min=2,
        weight=10,
        intro_key="explore_sc_factory_intro",
        steps=[
            ExplorationStep(
                prompt_key="explore_sc_factory_s0",
                choices=[
                    ExplorationChoice(
                        id="hall",
                        label_key="explore_sc_factory_c_hall",
                        risk="medium",
                        scrap_range=(14, 25),
                        gold_range=(2, 5),
                        item_chance=0.20,
                        pop_risk=1,
                    ),
                    ExplorationChoice(
                        id="basement",
                        label_key="explore_sc_factory_c_basement",
                        risk="medium",
                        scrap_range=(10, 18),
                        gold_range=(1, 4),
                        item_chance=0.15,
                        next_step=1,
                    ),
                    ExplorationChoice(
                        id="perimeter",
                        label_key="explore_sc_factory_c_perimeter",
                        risk="low",
                        scrap_range=(8, 16),
                        gold_range=(1, 3),
                        item_chance=0.10,
                    ),
                ],
            ),
            ExplorationStep(
                prompt_key="explore_sc_factory_s1",
                choices=[
                    ExplorationChoice(
                        id="locked_door",
                        label_key="explore_sc_factory_c_locked",
                        risk="high",
                        scrap_range=(22, 38),
                        gold_range=(5, 10),
                        item_chance=0.45,
                        pop_risk=2,
                        morale_risk=3,
                        codex_entry="codex_factory_schematics",
                    ),
                    ExplorationChoice(
                        id="vent",
                        label_key="explore_sc_factory_c_vent",
                        risk="medium",
                        scrap_range=(14, 24),
                        gold_range=(3, 6),
                        item_chance=0.30,
                        pop_risk=1,
                    ),
                ],
            ),
        ],
    ),

    # 7. Military Checkpoint
    ExplorationScenario(
        id="checkpoint",
        zone_min=2,
        weight=9,
        intro_key="explore_sc_checkpoint_intro",
        steps=[
            ExplorationStep(
                prompt_key="explore_sc_checkpoint_s0",
                choices=[
                    ExplorationChoice(
                        id="barracks",
                        label_key="explore_sc_checkpoint_c_barracks",
                        risk="medium",
                        scrap_range=(12, 22),
                        gold_range=(2, 5),
                        item_chance=0.25,
                        pop_risk=1,
                    ),
                    ExplorationChoice(
                        id="armory",
                        label_key="explore_sc_checkpoint_c_armory",
                        risk="high",
                        scrap_range=(20, 35),
                        gold_range=(5, 10),
                        item_chance=0.50,
                        pop_risk=3,
                        morale_risk=4,
                        codex_entry="codex_military_orders",
                    ),
                    ExplorationChoice(
                        id="radio",
                        label_key="explore_sc_checkpoint_c_radio",
                        risk="low",
                        scrap_range=(8, 15),
                        gold_range=(1, 3),
                        item_chance=0.15,
                        codex_entry="codex_last_broadcast",
                    ),
                ],
            ),
        ],
    ),

    # 8. Hospital Ruins (two steps)
    ExplorationScenario(
        id="hospital",
        zone_min=2,
        weight=9,
        intro_key="explore_sc_hospital_intro",
        steps=[
            ExplorationStep(
                prompt_key="explore_sc_hospital_s0",
                choices=[
                    ExplorationChoice(
                        id="pharmacy",
                        label_key="explore_sc_hospital_c_pharmacy",
                        risk="low",
                        scrap_range=(10, 18),
                        gold_range=(2, 5),
                        item_chance=0.30,
                    ),
                    ExplorationChoice(
                        id="operating",
                        label_key="explore_sc_hospital_c_operating",
                        risk="medium",
                        scrap_range=(14, 24),
                        gold_range=(3, 6),
                        item_chance=0.25,
                        pop_risk=1,
                        morale_risk=2,
                    ),
                    ExplorationChoice(
                        id="morgue",
                        label_key="explore_sc_hospital_c_morgue",
                        risk="high",
                        scrap_range=(12, 20),
                        gold_range=(2, 5),
                        item_chance=0.20,
                        morale_risk=5,
                        next_step=1,
                    ),
                ],
            ),
            ExplorationStep(
                prompt_key="explore_sc_hospital_s1",
                choices=[
                    ExplorationChoice(
                        id="secret_lab",
                        label_key="explore_sc_hospital_c_lab",
                        risk="high",
                        scrap_range=(25, 42),
                        gold_range=(6, 12),
                        item_chance=0.55,
                        pop_risk=3,
                        morale_risk=5,
                        codex_entry="codex_wasting_research",
                    ),
                    ExplorationChoice(
                        id="retreat",
                        label_key="explore_sc_hospital_c_retreat",
                        risk="low",
                        scrap_range=(5, 10),
                        gold_range=(1, 2),
                    ),
                ],
            ),
        ],
    ),

    # 9. Train Yard
    ExplorationScenario(
        id="trainyard",
        zone_min=2,
        weight=8,
        intro_key="explore_sc_trainyard_intro",
        steps=[
            ExplorationStep(
                prompt_key="explore_sc_trainyard_s0",
                choices=[
                    ExplorationChoice(
                        id="cargo",
                        label_key="explore_sc_trainyard_c_cargo",
                        risk="medium",
                        scrap_range=(14, 26),
                        gold_range=(2, 6),
                        item_chance=0.25,
                        pop_risk=1,
                    ),
                    ExplorationChoice(
                        id="engine",
                        label_key="explore_sc_trainyard_c_engine",
                        risk="medium",
                        scrap_range=(16, 28),
                        gold_range=(3, 7),
                        item_chance=0.20,
                        pop_risk=1,
                        codex_entry="codex_train_manifest",
                    ),
                    ExplorationChoice(
                        id="tunnel",
                        label_key="explore_sc_trainyard_c_tunnel",
                        risk="high",
                        scrap_range=(20, 35),
                        gold_range=(5, 10),
                        item_chance=0.40,
                        pop_risk=2,
                        morale_risk=4,
                    ),
                ],
            ),
        ],
    ),

    # 10. Collapsed Bridge (two steps)
    ExplorationScenario(
        id="bridge",
        zone_min=2,
        weight=8,
        intro_key="explore_sc_bridge_intro",
        steps=[
            ExplorationStep(
                prompt_key="explore_sc_bridge_s0",
                choices=[
                    ExplorationChoice(
                        id="riverbank",
                        label_key="explore_sc_bridge_c_riverbank",
                        risk="low",
                        scrap_range=(8, 16),
                        gold_range=(1, 3),
                        item_chance=0.15,
                    ),
                    ExplorationChoice(
                        id="supports",
                        label_key="explore_sc_bridge_c_supports",
                        risk="medium",
                        scrap_range=(12, 22),
                        gold_range=(2, 5),
                        item_chance=0.20,
                        pop_risk=1,
                        next_step=1,
                    ),
                ],
            ),
            ExplorationStep(
                prompt_key="explore_sc_bridge_s1",
                choices=[
                    ExplorationChoice(
                        id="air_pocket",
                        label_key="explore_sc_bridge_c_air_pocket",
                        risk="medium",
                        scrap_range=(16, 28),
                        gold_range=(4, 8),
                        item_chance=0.35,
                        pop_risk=1,
                        codex_entry="codex_bridge_builders",
                    ),
                    ExplorationChoice(
                        id="deep_dive",
                        label_key="explore_sc_bridge_c_deep_dive",
                        risk="high",
                        scrap_range=(24, 40),
                        gold_range=(6, 12),
                        item_chance=0.50,
                        pop_risk=3,
                        morale_risk=4,
                    ),
                ],
            ),
        ],
    ),

    # ======================================================================
    # ZONE 3+
    # ======================================================================

    # 11. Underground Bunker (two steps)
    ExplorationScenario(
        id="bunker",
        zone_min=3,
        weight=9,
        intro_key="explore_sc_bunker_intro",
        steps=[
            ExplorationStep(
                prompt_key="explore_sc_bunker_s0",
                choices=[
                    ExplorationChoice(
                        id="corridor",
                        label_key="explore_sc_bunker_c_corridor",
                        risk="medium",
                        scrap_range=(16, 28),
                        gold_range=(3, 7),
                        item_chance=0.25,
                        pop_risk=1,
                    ),
                    ExplorationChoice(
                        id="server",
                        label_key="explore_sc_bunker_c_server",
                        risk="medium",
                        scrap_range=(14, 24),
                        gold_range=(4, 8),
                        item_chance=0.30,
                        pop_risk=1,
                        next_step=1,
                    ),
                    ExplorationChoice(
                        id="quarters",
                        label_key="explore_sc_bunker_c_quarters",
                        risk="low",
                        scrap_range=(10, 20),
                        gold_range=(2, 5),
                        item_chance=0.20,
                        codex_entry="codex_bunker_diary",
                    ),
                ],
            ),
            ExplorationStep(
                prompt_key="explore_sc_bunker_s1",
                choices=[
                    ExplorationChoice(
                        id="mainframe",
                        label_key="explore_sc_bunker_c_mainframe",
                        risk="high",
                        scrap_range=(28, 45),
                        gold_range=(8, 15),
                        item_chance=0.55,
                        pop_risk=2,
                        morale_risk=4,
                        codex_entry="codex_bunker_ai_logs",
                    ),
                    ExplorationChoice(
                        id="armory",
                        label_key="explore_sc_bunker_c_armory",
                        risk="high",
                        scrap_range=(24, 40),
                        gold_range=(6, 12),
                        item_chance=0.50,
                        pop_risk=3,
                        morale_risk=3,
                    ),
                ],
            ),
        ],
    ),

    # 12. Research Facility
    ExplorationScenario(
        id="research",
        zone_min=3,
        weight=8,
        intro_key="explore_sc_research_intro",
        steps=[
            ExplorationStep(
                prompt_key="explore_sc_research_s0",
                choices=[
                    ExplorationChoice(
                        id="labs",
                        label_key="explore_sc_research_c_labs",
                        risk="medium",
                        scrap_range=(18, 30),
                        gold_range=(4, 8),
                        item_chance=0.30,
                        pop_risk=1,
                        codex_entry="codex_research_notes",
                    ),
                    ExplorationChoice(
                        id="specimens",
                        label_key="explore_sc_research_c_specimens",
                        risk="high",
                        scrap_range=(22, 38),
                        gold_range=(5, 12),
                        item_chance=0.50,
                        pop_risk=3,
                        morale_risk=6,
                        codex_entry="codex_specimen_theta",
                    ),
                    ExplorationChoice(
                        id="admin",
                        label_key="explore_sc_research_c_admin",
                        risk="low",
                        scrap_range=(12, 22),
                        gold_range=(3, 6),
                        item_chance=0.20,
                    ),
                ],
            ),
        ],
    ),

    # 13. Power Plant (two steps)
    ExplorationScenario(
        id="powerplant",
        zone_min=3,
        weight=7,
        intro_key="explore_sc_powerplant_intro",
        steps=[
            ExplorationStep(
                prompt_key="explore_sc_powerplant_s0",
                choices=[
                    ExplorationChoice(
                        id="control",
                        label_key="explore_sc_powerplant_c_control",
                        risk="medium",
                        scrap_range=(16, 28),
                        gold_range=(3, 7),
                        item_chance=0.25,
                        pop_risk=1,
                        codex_entry="codex_power_logs",
                    ),
                    ExplorationChoice(
                        id="reactor",
                        label_key="explore_sc_powerplant_c_reactor",
                        risk="high",
                        scrap_range=(30, 50),
                        gold_range=(8, 16),
                        item_chance=0.55,
                        pop_risk=4,
                        morale_risk=6,
                    ),
                    ExplorationChoice(
                        id="tunnels",
                        label_key="explore_sc_powerplant_c_tunnels",
                        risk="medium",
                        scrap_range=(14, 26),
                        gold_range=(3, 6),
                        item_chance=0.20,
                        pop_risk=1,
                        next_step=1,
                    ),
                ],
            ),
            ExplorationStep(
                prompt_key="explore_sc_powerplant_s1",
                choices=[
                    ExplorationChoice(
                        id="generator",
                        label_key="explore_sc_powerplant_c_generator",
                        risk="high",
                        scrap_range=(26, 44),
                        gold_range=(7, 14),
                        item_chance=0.50,
                        pop_risk=2,
                        morale_risk=4,
                        codex_entry="codex_fusion_core",
                    ),
                    ExplorationChoice(
                        id="exit",
                        label_key="explore_sc_powerplant_c_exit",
                        risk="low",
                        scrap_range=(8, 14),
                        gold_range=(2, 4),
                        item_chance=0.10,
                    ),
                ],
            ),
        ],
    ),

    # 14. Communication Tower (two steps)
    ExplorationScenario(
        id="comtower",
        zone_min=3,
        weight=7,
        intro_key="explore_sc_comtower_intro",
        steps=[
            ExplorationStep(
                prompt_key="explore_sc_comtower_s0",
                choices=[
                    ExplorationChoice(
                        id="base",
                        label_key="explore_sc_comtower_c_base",
                        risk="low",
                        scrap_range=(12, 22),
                        gold_range=(2, 5),
                        item_chance=0.15,
                    ),
                    ExplorationChoice(
                        id="antenna",
                        label_key="explore_sc_comtower_c_antenna",
                        risk="medium",
                        scrap_range=(18, 30),
                        gold_range=(4, 8),
                        item_chance=0.30,
                        pop_risk=2,
                        morale_risk=2,
                        codex_entry="codex_network_freq",
                    ),
                    ExplorationChoice(
                        id="cables",
                        label_key="explore_sc_comtower_c_cables",
                        risk="medium",
                        scrap_range=(10, 18),
                        gold_range=(2, 4),
                        item_chance=0.15,
                        next_step=1,
                    ),
                ],
            ),
            ExplorationStep(
                prompt_key="explore_sc_comtower_s1",
                choices=[
                    ExplorationChoice(
                        id="data_vault",
                        label_key="explore_sc_comtower_c_vault",
                        risk="high",
                        scrap_range=(26, 44),
                        gold_range=(8, 15),
                        item_chance=0.55,
                        pop_risk=2,
                        morale_risk=5,
                        codex_entry="codex_encrypted_archive",
                    ),
                    ExplorationChoice(
                        id="surface",
                        label_key="explore_sc_comtower_c_surface",
                        risk="low",
                        scrap_range=(6, 12),
                        gold_range=(1, 3),
                        item_chance=0.10,
                    ),
                ],
            ),
        ],
    ),

    # 15. The Dead Mall (two steps)
    ExplorationScenario(
        id="deadmall",
        zone_min=3,
        weight=8,
        intro_key="explore_sc_deadmall_intro",
        steps=[
            ExplorationStep(
                prompt_key="explore_sc_deadmall_s0",
                choices=[
                    ExplorationChoice(
                        id="stores",
                        label_key="explore_sc_deadmall_c_stores",
                        risk="medium",
                        scrap_range=(14, 26),
                        gold_range=(3, 7),
                        item_chance=0.25,
                        pop_risk=1,
                    ),
                    ExplorationChoice(
                        id="foodcourt",
                        label_key="explore_sc_deadmall_c_foodcourt",
                        risk="low",
                        scrap_range=(10, 18),
                        gold_range=(2, 5),
                        item_chance=0.15,
                    ),
                    ExplorationChoice(
                        id="security",
                        label_key="explore_sc_deadmall_c_security",
                        risk="medium",
                        scrap_range=(12, 22),
                        gold_range=(3, 6),
                        item_chance=0.20,
                        pop_risk=1,
                        next_step=1,
                    ),
                ],
            ),
            ExplorationStep(
                prompt_key="explore_sc_deadmall_s1",
                choices=[
                    ExplorationChoice(
                        id="vault",
                        label_key="explore_sc_deadmall_c_vault",
                        risk="high",
                        scrap_range=(28, 48),
                        gold_range=(10, 18),
                        item_chance=0.60,
                        pop_risk=3,
                        morale_risk=5,
                        codex_entry="codex_mall_safe",
                    ),
                    ExplorationChoice(
                        id="back_exit",
                        label_key="explore_sc_deadmall_c_exit",
                        risk="low",
                        scrap_range=(6, 12),
                        gold_range=(1, 3),
                        item_chance=0.10,
                    ),
                ],
            ),
        ],
    ),
]

# Index for quick lookup by id
_SCENARIO_MAP: dict[str, ExplorationScenario] = {s.id: s for s in SCENARIOS}


# ---------------------------------------------------------------------------
# Selection / resolution helpers
# ---------------------------------------------------------------------------

def pick_scenario(zone: int) -> ExplorationScenario:
    """Weighted random selection of a scenario available for *zone*.

    Raises ``ValueError`` if no scenarios are eligible (should not happen in
    production since zone 1 always has entries).
    """
    eligible = [s for s in SCENARIOS if zone >= s.zone_min]
    if not eligible:
        raise ValueError(f"No exploration scenarios for zone {zone}")

    weights = [s.weight for s in eligible]
    return random.choices(eligible, weights=weights, k=1)[0]


def get_scenario(scenario_id: str) -> ExplorationScenario | None:
    """Look up a scenario by its id."""
    return _SCENARIO_MAP.get(scenario_id)


def resolve_exploration_choice(
    choice: ExplorationChoice,
    zone: int,
) -> dict:
    """Calculate concrete rewards/penalties for *choice*.

    Returns a dict with::

        {
            "scrap": int,
            "gold": int,
            "item_id": str | None,
            "pop_loss": int,
            "morale_loss": int,
            "codex_entry": str | None,
        }

    Zone multiplier is applied to rewards (higher zones give more loot).
    Risk penalties fire probabilistically.
    """
    # Zone reward multiplier: 1.0 / 1.15 / 1.3 / 1.5 / 1.75
    zone_mult: float = {1: 1.0, 2: 1.15, 3: 1.3, 4: 1.5, 5: 1.75}.get(zone, 1.0)

    # Scrap reward
    lo, hi = choice.scrap_range
    raw_scrap = random.randint(lo, hi) if hi > lo else lo
    scrap = ceil(raw_scrap * zone_mult)

    # Gold reward
    glo, ghi = choice.gold_range
    gold = random.randint(glo, ghi) if ghi > glo else glo
    gold = ceil(gold * zone_mult)

    # Item drop
    item_id: str | None = None
    if choice.item_chance > 0 and random.random() < choice.item_chance:
        item_id = _roll_exploration_item(zone)

    # Risk penalties (probabilistic)
    pop_loss = 0
    morale_loss = 0
    penalty_chance = _RISK_PENALTY_CHANCE.get(choice.risk, 0.10)
    if choice.pop_risk > 0 and random.random() < penalty_chance:
        pop_loss = choice.pop_risk
    if choice.morale_risk > 0 and random.random() < penalty_chance:
        morale_loss = choice.morale_risk

    return {
        "scrap": scrap,
        "gold": gold,
        "item_id": item_id,
        "pop_loss": pop_loss,
        "morale_loss": morale_loss,
        "codex_entry": choice.codex_entry,
    }


def _roll_exploration_item(zone: int) -> str:
    """Roll a random item id appropriate for the zone.

    Returns a generic item slug.  The item catalog is defined elsewhere;
    here we just pick a tier-appropriate id.
    """
    # Tier pools by zone (item ids are resolved by the item system)
    tier_1 = ["item_scrap_armor", "item_rusty_blade", "item_first_aid", "item_rations"]
    tier_2 = ["item_combat_knife", "item_kevlar_vest", "item_med_kit", "item_binoculars"]
    tier_3 = ["item_assault_rifle", "item_hazmat_suit", "item_advanced_med", "item_night_vision"]
    tier_rare = ["item_power_cell", "item_ai_chip", "item_ancient_map", "item_fusion_core"]

    if zone <= 1:
        pool = tier_1
    elif zone == 2:
        pool = tier_1 + tier_2
    elif zone == 3:
        pool = tier_2 + tier_3
    elif zone == 4:
        pool = tier_3 + tier_rare
    else:
        pool = tier_3 + tier_rare + tier_rare  # double-weight rares at zone 5

    return random.choice(pool)


# ---------------------------------------------------------------------------
# i18n strings
# ---------------------------------------------------------------------------

EXPLORATION_STRINGS: dict[str, dict[str, str]] = {
    # ==================================================================
    # Scenario display names (used by explore handler)
    # ==================================================================
    "explore_sc_gasstation_name": {"en": "Abandoned Gas Station", "ru": "Заброшенная заправка"},
    "explore_sc_apartment_name": {"en": "Crumbling Apartment Block", "ru": "Разрушенный жилой дом"},
    "explore_sc_market_name": {"en": "Ransacked Market", "ru": "Разграбленный рынок"},
    "explore_sc_camp_name": {"en": "Abandoned Camp", "ru": "Заброшенный лагерь"},
    "explore_sc_school_name": {"en": "Old School Building", "ru": "Старое школьное здание"},
    "explore_sc_factory_name": {"en": "Ruined Factory Complex", "ru": "Разрушенный заводской комплекс"},
    "explore_sc_checkpoint_name": {"en": "Military Checkpoint", "ru": "Военный блокпост"},
    "explore_sc_hospital_name": {"en": "Ruined Hospital", "ru": "Разрушенная больница"},
    "explore_sc_trainyard_name": {"en": "Abandoned Trainyard", "ru": "Заброшенное депо"},
    "explore_sc_bridge_name": {"en": "Collapsed Bridge", "ru": "Обрушенный мост"},
    "explore_sc_bunker_name": {"en": "Underground Bunker", "ru": "Подземный бункер"},
    "explore_sc_research_name": {"en": "Research Lab", "ru": "Исследовательская лаборатория"},
    "explore_sc_powerplant_name": {"en": "Wrecked Power Plant", "ru": "Разрушенная электростанция"},
    "explore_sc_comtower_name": {"en": "Communications Tower", "ru": "Телекоммуникационная вышка"},
    "explore_sc_deadmall_name": {"en": "Dead Mall", "ru": "Мёртвый торговый центр"},

    # ==================================================================
    # 1. Abandoned Gas Station
    # ==================================================================
    "explore_sc_gasstation_intro": {
        "en": (
            "You spot an old gas station half-buried in sand. "
            "The rusted pumps stand like skeletal sentinels. "
            "There might still be something worth salvaging inside."
        ),
        "ru": (
            "Ты замечаешь старую заправку, наполовину засыпанную песком. "
            "Ржавые колонки стоят как скелеты часовых. "
            "Внутри ещё может быть что-то ценное."
        ),
    },
    "explore_sc_gasstation_s0": {
        "en": "The station has three areas you could search. Where do you go?",
        "ru": "На станции три зоны для обыска. Куда идёшь?",
    },
    "explore_sc_gasstation_c_main": {
        "en": "Main Building",
        "ru": "Главное здание",
    },
    "explore_sc_gasstation_c_storage": {
        "en": "Storage Shed",
        "ru": "Складской сарай",
    },
    "explore_sc_gasstation_c_cellar": {
        "en": "Underground Cellar",
        "ru": "Подземный погреб",
    },

    # ==================================================================
    # 2. Collapsed Apartment Block
    # ==================================================================
    "explore_sc_apartment_intro": {
        "en": (
            "A collapsed apartment block looms ahead. Concrete slabs hang "
            "at impossible angles. The building groans in the wind, but "
            "scavengers say the upper floors were never picked clean."
        ),
        "ru": (
            "Впереди высится обрушившийся жилой дом. Бетонные плиты висят "
            "под немыслимыми углами. Здание стонет на ветру, но говорят, "
            "что верхние этажи так и не обыскали до конца."
        ),
    },
    "explore_sc_apartment_s0": {
        "en": "You can try to enter from different points. Choose your approach:",
        "ru": "Войти можно с разных сторон. Выбери подход:",
    },
    "explore_sc_apartment_c_lobby": {
        "en": "Lobby Rubble",
        "ru": "Завалы вестибюля",
    },
    "explore_sc_apartment_c_stairwell": {
        "en": "Stairwell Climb",
        "ru": "Подъём по лестнице",
    },
    "explore_sc_apartment_c_roof": {
        "en": "Roof Access",
        "ru": "Выход на крышу",
    },

    # ==================================================================
    # 3. Overgrown Market
    # ==================================================================
    "explore_sc_market_intro": {
        "en": (
            "An old marketplace sprawls before you, choked with vines and "
            "twisted metal. Faded signs advertise goods that no longer exist. "
            "Somewhere beneath the overgrowth, there could be useful supplies."
        ),
        "ru": (
            "Перед тобой раскинулся старый рынок, заросший лианами и "
            "скрученным металлом. Выцветшие вывески рекламируют товары, "
            "которых давно нет. Под зарослями могут скрываться припасы."
        ),
    },
    "explore_sc_market_s0": {
        "en": "The market has several sections still standing. Where do you look?",
        "ru": "Несколько секций рынка ещё стоят. Где будешь искать?",
    },
    "explore_sc_market_c_stalls": {
        "en": "Vegetable Stalls",
        "ru": "Овощные прилавки",
    },
    "explore_sc_market_c_pharmacy": {
        "en": "Pharmacy Counter",
        "ru": "Прилавок аптеки",
    },
    "explore_sc_market_c_alley": {
        "en": "Back Alley",
        "ru": "Задний переулок",
    },

    # ==================================================================
    # 4. Roadside Camp
    # ==================================================================
    "explore_sc_camp_intro": {
        "en": (
            "A roadside camp appears around the bend - abandoned tents, "
            "a burnt-out vehicle, and fresh tracks leading into the hills. "
            "Someone was here recently."
        ),
        "ru": (
            "За поворотом виднеется придорожный лагерь - брошенные палатки, "
            "выгоревший автомобиль и свежие следы, ведущие в холмы. "
            "Кто-то был здесь совсем недавно."
        ),
    },
    "explore_sc_camp_s0": {
        "en": "The camp looks recently abandoned. What catches your eye?",
        "ru": "Лагерь покинули недавно. Что привлекает твоё внимание?",
    },
    "explore_sc_camp_c_tents": {
        "en": "Search Tents",
        "ru": "Обыскать палатки",
    },
    "explore_sc_camp_c_vehicle": {
        "en": "Check Vehicle",
        "ru": "Осмотреть машину",
    },
    "explore_sc_camp_c_tracks": {
        "en": "Follow Tracks",
        "ru": "Пойти по следам",
    },
    "explore_sc_camp_s1": {
        "en": (
            "The tracks lead through dense brush to a fork in the path. "
            "One trail descends into a dark cave mouth. "
            "The other opens into a sunlit clearing."
        ),
        "ru": (
            "Следы ведут сквозь густой кустарник к развилке. "
            "Одна тропа спускается в тёмную пещеру. "
            "Другая выходит на залитую солнцем поляну."
        ),
    },
    "explore_sc_camp_c_cave": {
        "en": "Enter the Cave",
        "ru": "Войти в пещеру",
    },
    "explore_sc_camp_c_clearing": {
        "en": "Check the Clearing",
        "ru": "Осмотреть поляну",
    },

    # ==================================================================
    # 5. Old School Building
    # ==================================================================
    "explore_sc_school_intro": {
        "en": (
            "An old school building stands mostly intact, its windows like "
            "hollow eyes. Children's drawings still cling to the walls inside. "
            "This place holds memories - and maybe supplies."
        ),
        "ru": (
            "Старое школьное здание стоит почти целым, окна - как пустые "
            "глазницы. Внутри на стенах ещё висят детские рисунки. "
            "Здесь хранятся воспоминания - и, возможно, припасы."
        ),
    },
    "explore_sc_school_s0": {
        "en": "The ground floor seems safe enough. Which area do you explore first?",
        "ru": "Первый этаж выглядит безопасно. Какую зону обыщешь первой?",
    },
    "explore_sc_school_c_classrooms": {
        "en": "Classrooms",
        "ru": "Классные комнаты",
    },
    "explore_sc_school_c_cafeteria": {
        "en": "Cafeteria",
        "ru": "Столовая",
    },
    "explore_sc_school_c_office": {
        "en": "Principal's Office",
        "ru": "Кабинет директора",
    },
    "explore_sc_school_s1": {
        "en": (
            "Behind the principal's desk, you find a hidden trapdoor. "
            "The darkness below smells of dust and old paper. "
            "Do you risk going down?"
        ),
        "ru": (
            "За столом директора ты находишь скрытый люк. "
            "Снизу пахнет пылью и старой бумагой. "
            "Рискнёшь спуститься?"
        ),
    },
    "explore_sc_school_c_basement": {
        "en": "Descend to Basement",
        "ru": "Спуститься в подвал",
    },
    "explore_sc_school_c_leave": {
        "en": "Take What You Have and Leave",
        "ru": "Забрать найденное и уйти",
    },

    # ==================================================================
    # 6. Ruined Factory Complex
    # ==================================================================
    "explore_sc_factory_intro": {
        "en": (
            "A sprawling factory complex rises from the wasteland, its "
            "smokestacks like broken fingers against the sky. "
            "Machinery still hums faintly deep inside."
        ),
        "ru": (
            "Из пустоши поднимается огромный заводской комплекс, его "
            "трубы торчат как сломанные пальцы на фоне неба. "
            "Глубоко внутри всё ещё слышно слабое гудение машин."
        ),
    },
    "explore_sc_factory_s0": {
        "en": "The factory has multiple entry points. Where do you start?",
        "ru": "На завод можно попасть несколькими путями. Откуда начнёшь?",
    },
    "explore_sc_factory_c_hall": {
        "en": "Main Production Hall",
        "ru": "Главный цех",
    },
    "explore_sc_factory_c_basement": {
        "en": "Basement Level",
        "ru": "Подвальный уровень",
    },
    "explore_sc_factory_c_perimeter": {
        "en": "Perimeter Sheds",
        "ru": "Периметр и склады",
    },
    "explore_sc_factory_s1": {
        "en": (
            "The basement leads to a sealed section. "
            "A heavy door blocks one passage, and a narrow ventilation "
            "shaft offers an alternative route."
        ),
        "ru": (
            "Подвал ведёт к запечатанной секции. "
            "Массивная дверь преграждает один проход, а узкая "
            "вентиляционная шахта предлагает альтернативный путь."
        ),
    },
    "explore_sc_factory_c_locked": {
        "en": "Force the Locked Door",
        "ru": "Взломать дверь",
    },
    "explore_sc_factory_c_vent": {
        "en": "Crawl Through Vent",
        "ru": "Пролезть через вентиляцию",
    },

    # ==================================================================
    # 7. Military Checkpoint
    # ==================================================================
    "explore_sc_checkpoint_intro": {
        "en": (
            "A pre-Collapse military checkpoint still guards the road. "
            "Sandbags and razor wire form a perimeter around concrete "
            "structures. The Hegemony flag hangs in tatters."
        ),
        "ru": (
            "Военный блокпост довоенных времён всё ещё стоит на дороге. "
            "Мешки с песком и колючая проволока окружают бетонные "
            "строения. Флаг Гегемонии висит лохмотьями."
        ),
    },
    "explore_sc_checkpoint_s0": {
        "en": "Three structures remain relatively intact. Which do you enter?",
        "ru": "Три строения относительно целы. В какое войдёшь?",
    },
    "explore_sc_checkpoint_c_barracks": {
        "en": "Barracks",
        "ru": "Казармы",
    },
    "explore_sc_checkpoint_c_armory": {
        "en": "Armory (Dangerous!)",
        "ru": "Арсенал (Опасно!)",
    },
    "explore_sc_checkpoint_c_radio": {
        "en": "Radio Tower",
        "ru": "Радиовышка",
    },

    # ==================================================================
    # 8. Hospital Ruins
    # ==================================================================
    "explore_sc_hospital_intro": {
        "en": (
            "The ruins of a hospital loom before you. "
            "Its white walls are now grey with ash and time. "
            "Medical supplies would be invaluable - if anything survived."
        ),
        "ru": (
            "Перед тобой высятся руины больницы. "
            "Её белые стены теперь серые от пепла и времени. "
            "Медикаменты были бы бесценны - если что-то уцелело."
        ),
    },
    "explore_sc_hospital_s0": {
        "en": "The hospital's wings stretch in different directions. Choose one:",
        "ru": "Крылья больницы расходятся в разных направлениях. Выбери одно:",
    },
    "explore_sc_hospital_c_pharmacy": {
        "en": "Pharmacy Wing",
        "ru": "Аптечное крыло",
    },
    "explore_sc_hospital_c_operating": {
        "en": "Operating Rooms",
        "ru": "Операционные",
    },
    "explore_sc_hospital_c_morgue": {
        "en": "Morgue",
        "ru": "Морг",
    },
    "explore_sc_hospital_s1": {
        "en": (
            "Beyond the morgue, you discover a concealed stairway leading "
            "down. The sign reads 'Authorized Personnel Only'. "
            "The air smells of chemicals."
        ),
        "ru": (
            "За моргом ты обнаруживаешь скрытую лестницу вниз. "
            "Табличка гласит: 'Только для авторизованного персонала'. "
            "В воздухе пахнет химикатами."
        ),
    },
    "explore_sc_hospital_c_lab": {
        "en": "Enter the Secret Lab",
        "ru": "Войти в секретную лабораторию",
    },
    "explore_sc_hospital_c_retreat": {
        "en": "Too Risky, Retreat",
        "ru": "Слишком опасно, отступить",
    },

    # ==================================================================
    # 9. Train Yard
    # ==================================================================
    "explore_sc_trainyard_intro": {
        "en": (
            "Rows of derailed freight cars stretch into the distance. "
            "The train yard is a maze of rusted steel and forgotten cargo. "
            "Something metallic clangs in the wind."
        ),
        "ru": (
            "Ряды сошедших с рельсов товарных вагонов тянутся вдаль. "
            "Железнодорожная станция - лабиринт ржавой стали и "
            "забытых грузов. Что-то металлическое звенит на ветру."
        ),
    },
    "explore_sc_trainyard_s0": {
        "en": "The yard offers several areas of interest. Where do you search?",
        "ru": "На станции несколько интересных зон. Где будешь искать?",
    },
    "explore_sc_trainyard_c_cargo": {
        "en": "Cargo Cars",
        "ru": "Грузовые вагоны",
    },
    "explore_sc_trainyard_c_engine": {
        "en": "Engine Room",
        "ru": "Машинное отделение",
    },
    "explore_sc_trainyard_c_tunnel": {
        "en": "Underground Tunnel",
        "ru": "Подземный тоннель",
    },

    # ==================================================================
    # 10. Collapsed Bridge
    # ==================================================================
    "explore_sc_bridge_intro": {
        "en": (
            "A massive bridge has collapsed into the river below. "
            "Its twisted supports jut from the water like the ribs of "
            "some great beast. Debris is scattered along both banks."
        ),
        "ru": (
            "Огромный мост обрушился в реку. "
            "Его скрученные опоры торчат из воды, как рёбра "
            "какого-то великого зверя. Обломки разбросаны по обоим берегам."
        ),
    },
    "explore_sc_bridge_s0": {
        "en": "You can search the riverbank or climb down to the bridge supports.",
        "ru": "Можно обыскать берег или спуститься к опорам моста.",
    },
    "explore_sc_bridge_c_riverbank": {
        "en": "Search the Riverbank",
        "ru": "Обыскать берег",
    },
    "explore_sc_bridge_c_supports": {
        "en": "Climb to Bridge Supports",
        "ru": "Спуститься к опорам",
    },
    "explore_sc_bridge_s1": {
        "en": (
            "Beneath the collapsed span, you find an air pocket in the "
            "wreckage. Deeper still, the river swirls into a flooded "
            "compartment that might hold sealed containers."
        ),
        "ru": (
            "Под обрушившимся пролётом ты находишь воздушный карман "
            "в обломках. Ещё глубже река закручивается в затопленный "
            "отсек, где могут быть герметичные контейнеры."
        ),
    },
    "explore_sc_bridge_c_air_pocket": {
        "en": "Explore the Air Pocket",
        "ru": "Исследовать воздушный карман",
    },
    "explore_sc_bridge_c_deep_dive": {
        "en": "Deep Dive into Flooded Section",
        "ru": "Нырнуть в затопленную секцию",
    },

    # ==================================================================
    # 11. Underground Bunker
    # ==================================================================
    "explore_sc_bunker_intro": {
        "en": (
            "A blast door yawns open in the hillside, revealing a "
            "pre-Collapse bunker. Emergency lights flicker in the "
            "corridor beyond. The air is stale but breathable."
        ),
        "ru": (
            "Бронированная дверь зияет в склоне холма, открывая "
            "довоенный бункер. Аварийное освещение мерцает в "
            "коридоре. Воздух затхлый, но дышать можно."
        ),
    },
    "explore_sc_bunker_s0": {
        "en": "The bunker branches into three sections. Choose your path:",
        "ru": "Бункер разветвляется на три секции. Выбери путь:",
    },
    "explore_sc_bunker_c_corridor": {
        "en": "Main Corridor",
        "ru": "Главный коридор",
    },
    "explore_sc_bunker_c_server": {
        "en": "Server Room",
        "ru": "Серверная",
    },
    "explore_sc_bunker_c_quarters": {
        "en": "Living Quarters",
        "ru": "Жилые помещения",
    },
    "explore_sc_bunker_s1": {
        "en": (
            "The server room's backup power still trickles. "
            "A mainframe terminal blinks invitingly, and a sealed "
            "armory door has a keypad that might still work."
        ),
        "ru": (
            "В серверной ещё теплится резервное питание. "
            "Терминал мейнфрейма мигает приглашающе, а запечатанная "
            "дверь арсенала имеет клавиатуру, которая может работать."
        ),
    },
    "explore_sc_bunker_c_mainframe": {
        "en": "Access the Mainframe",
        "ru": "Подключиться к мейнфрейму",
    },
    "explore_sc_bunker_c_armory": {
        "en": "Break into the Armory",
        "ru": "Взломать арсенал",
    },

    # ==================================================================
    # 12. Research Facility
    # ==================================================================
    "explore_sc_research_intro": {
        "en": (
            "A research facility rises from the scorched earth, its "
            "reinforced walls still mostly intact. Biohazard symbols "
            "are painted on every entrance. Proceed with caution."
        ),
        "ru": (
            "Исследовательский комплекс поднимается из выжженной земли, "
            "его укреплённые стены в основном целы. Знаки биологической "
            "опасности нарисованы на каждом входе. Действуй осторожно."
        ),
    },
    "explore_sc_research_s0": {
        "en": "The facility has three accessible wings. Which do you explore?",
        "ru": "В комплексе три доступных крыла. Какое исследуешь?",
    },
    "explore_sc_research_c_labs": {
        "en": "Research Labs",
        "ru": "Лаборатории",
    },
    "explore_sc_research_c_specimens": {
        "en": "Specimen Storage (Very Dangerous!)",
        "ru": "Хранилище образцов (Очень опасно!)",
    },
    "explore_sc_research_c_admin": {
        "en": "Admin Offices",
        "ru": "Административные офисы",
    },

    # ==================================================================
    # 13. Power Plant
    # ==================================================================
    "explore_sc_powerplant_intro": {
        "en": (
            "The cooling towers of a nuclear power plant dominate the "
            "horizon. Radiation readings are elevated but not lethal "
            "near the outer buildings. The real danger lies within."
        ),
        "ru": (
            "Градирни атомной электростанции доминируют на горизонте. "
            "Уровень радиации повышен, но не смертелен у внешних зданий. "
            "Настоящая опасность - внутри."
        ),
    },
    "explore_sc_powerplant_s0": {
        "en": "Three areas of the plant are accessible. Choose carefully:",
        "ru": "Три зоны станции доступны. Выбирай осторожно:",
    },
    "explore_sc_powerplant_c_control": {
        "en": "Control Room",
        "ru": "Пульт управления",
    },
    "explore_sc_powerplant_c_reactor": {
        "en": "Reactor Core (Extreme Risk!)",
        "ru": "Ядро реактора (Крайне опасно!)",
    },
    "explore_sc_powerplant_c_tunnels": {
        "en": "Maintenance Tunnels",
        "ru": "Технические тоннели",
    },
    "explore_sc_powerplant_s1": {
        "en": (
            "The tunnels lead to a backup generator room. "
            "The generator looks salvageable, but the ceiling "
            "is crumbling. You could also take the safe exit."
        ),
        "ru": (
            "Тоннели ведут к помещению резервного генератора. "
            "Генератор выглядит пригодным для разборки, но потолок "
            "осыпается. Можно также выйти безопасным путём."
        ),
    },
    "explore_sc_powerplant_c_generator": {
        "en": "Salvage the Generator",
        "ru": "Разобрать генератор",
    },
    "explore_sc_powerplant_c_exit": {
        "en": "Take the Safe Exit",
        "ru": "Выйти безопасным путём",
    },

    # ==================================================================
    # 14. Communication Tower
    # ==================================================================
    "explore_sc_comtower_intro": {
        "en": (
            "A communication tower stands tall against the ashen sky, "
            "its dish still pointed at the heavens. Cables snake down "
            "into the earth. Someone maintained this recently."
        ),
        "ru": (
            "Коммуникационная вышка возвышается на фоне пепельного неба, "
            "её тарелка всё ещё направлена в небо. Кабели змеями "
            "уходят в землю. Кто-то обслуживал это недавно."
        ),
    },
    "explore_sc_comtower_s0": {
        "en": "The tower complex has three points of interest. Where do you start?",
        "ru": "У вышки три интересных точки. С чего начнёшь?",
    },
    "explore_sc_comtower_c_base": {
        "en": "Base Level",
        "ru": "Основание вышки",
    },
    "explore_sc_comtower_c_antenna": {
        "en": "Antenna Array",
        "ru": "Антенная решётка",
    },
    "explore_sc_comtower_c_cables": {
        "en": "Follow Underground Cables",
        "ru": "Пойти по подземным кабелям",
    },
    "explore_sc_comtower_s1": {
        "en": (
            "The cables lead to a reinforced hatch. Below it, "
            "a data vault hums with residual power. The security "
            "system looks partially active."
        ),
        "ru": (
            "Кабели ведут к укреплённому люку. Под ним "
            "дата-хранилище гудит от остаточного питания. "
            "Система безопасности частично активна."
        ),
    },
    "explore_sc_comtower_c_vault": {
        "en": "Breach the Data Vault",
        "ru": "Взломать хранилище данных",
    },
    "explore_sc_comtower_c_surface": {
        "en": "Return to Surface",
        "ru": "Вернуться на поверхность",
    },

    # ==================================================================
    # 15. The Dead Mall
    # ==================================================================
    "explore_sc_deadmall_intro": {
        "en": (
            "A massive shopping mall lies gutted and dark. "
            "Escalators frozen mid-step, shop fronts gaping open. "
            "Somewhere inside, a generator still chugs. "
            "This place has secrets."
        ),
        "ru": (
            "Огромный торговый центр стоит выпотрошенный и тёмный. "
            "Эскалаторы застыли на полушаге, витрины зияют пустотой. "
            "Где-то внутри ещё тарахтит генератор. "
            "У этого места есть секреты."
        ),
    },
    "explore_sc_deadmall_s0": {
        "en": "The mall stretches in several directions. Where do you head?",
        "ru": "Молл тянется в нескольких направлениях. Куда пойдёшь?",
    },
    "explore_sc_deadmall_c_stores": {
        "en": "Department Stores",
        "ru": "Универмаги",
    },
    "explore_sc_deadmall_c_foodcourt": {
        "en": "Food Court",
        "ru": "Фуд-корт",
    },
    "explore_sc_deadmall_c_security": {
        "en": "Security Office",
        "ru": "Офис охраны",
    },
    "explore_sc_deadmall_s1": {
        "en": (
            "In the security office, monitors show a feed from a hidden "
            "basement level. A heavy vault door is visible on the screen. "
            "You find the access keycard on the desk."
        ),
        "ru": (
            "В офисе охраны мониторы показывают скрытый подвальный "
            "уровень. На экране видна массивная дверь хранилища. "
            "Ты находишь ключ-карту доступа на столе."
        ),
    },
    "explore_sc_deadmall_c_vault": {
        "en": "Open the Hidden Vault",
        "ru": "Открыть скрытое хранилище",
    },
    "explore_sc_deadmall_c_exit": {
        "en": "Leave with What You Have",
        "ru": "Уйти с тем, что есть",
    },
}

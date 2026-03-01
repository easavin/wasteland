"""Core game state and turn result data structures."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GameState:
    """Mutable snapshot of a single game.

    Field names mirror the ``game_states`` table columns so that
    ``GameState.from_db_row(dict(row))`` works directly with asyncpg rows.
    """

    # Identity
    id: str = ""
    player_id: str = ""
    status: str = "active"  # active | won | lost | abandoned
    turn_number: int = 0
    settlement_name: str = "Unnamed Settlement"

    # Resources
    population: int = 50
    food: int = 100
    scrap: int = 80
    morale: int = 70   # 0-100
    defense: int = 30   # 0-100

    # Starvation tracker
    food_zero_turns: int = 0

    # Faction reputations (-100 to +100)
    raiders_rep: int = 0
    traders_rep: int = 0
    remnants_rep: int = 0

    # Player style (0.0 - 1.0)
    style_aggression: float = 0.5
    style_commerce: float = 0.5
    style_exploration: float = 0.5
    style_diplomacy: float = 0.5

    # Complex state stored as JSON in DB
    buildings: dict[str, int] = field(default_factory=dict)
    active_effects: list[dict] = field(default_factory=list)
    narrator_memory: list[str] = field(default_factory=list)

    # Timestamps (kept as strings; only used for display / logging)
    started_at: str | None = None
    ended_at: str | None = None
    updated_at: str | None = None

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_db_row(cls, row: dict) -> GameState:
        """Build a ``GameState`` from an asyncpg ``Record`` converted to dict.

        Handles UUID -> str coercion and JSONB text -> Python object parsing.
        """
        data: dict[str, Any] = {}

        for key in (
            "id",
            "player_id",
            "status",
            "turn_number",
            "settlement_name",
            "population",
            "food",
            "scrap",
            "morale",
            "defense",
            "food_zero_turns",
            "raiders_rep",
            "traders_rep",
            "remnants_rep",
            "style_aggression",
            "style_commerce",
            "style_exploration",
            "style_diplomacy",
        ):
            if key in row:
                data[key] = row[key]

        # UUID fields -> str
        for uid_key in ("id", "player_id"):
            if uid_key in data and data[uid_key] is not None:
                data[uid_key] = str(data[uid_key])

        # JSONB columns may already be parsed by asyncpg or may be strings.
        for json_key in ("buildings", "active_effects", "narrator_memory"):
            raw = row.get(json_key)
            if raw is None:
                continue
            if isinstance(raw, str):
                data[json_key] = json.loads(raw)
            else:
                data[json_key] = raw

        # Timestamps -> str (or None)
        for ts_key in ("started_at", "ended_at", "updated_at"):
            val = row.get(ts_key)
            data[ts_key] = str(val) if val is not None else None

        return cls(**data)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def snapshot_resources(self) -> dict[str, int]:
        """Return a plain dict of current resource values.

        Useful for computing deltas (before / after).
        """
        return {
            "population": self.population,
            "food": self.food,
            "scrap": self.scrap,
            "morale": self.morale,
            "defense": self.defense,
        }

    def clamp_resources(self) -> None:
        """Enforce hard boundaries on bounded resources."""
        self.morale = max(0, min(100, self.morale))
        self.defense = max(0, min(100, self.defense))
        # Population and food may not go below zero.
        self.population = max(0, self.population)
        self.food = max(0, self.food)
        self.scrap = max(0, self.scrap)
        # Faction reps clamped -100..+100
        self.raiders_rep = max(-100, min(100, self.raiders_rep))
        self.traders_rep = max(-100, min(100, self.traders_rep))
        self.remnants_rep = max(-100, min(100, self.remnants_rep))
        # Styles clamped 0..1
        self.style_aggression = max(0.0, min(1.0, self.style_aggression))
        self.style_commerce = max(0.0, min(1.0, self.style_commerce))
        self.style_exploration = max(0.0, min(1.0, self.style_exploration))
        self.style_diplomacy = max(0.0, min(1.0, self.style_diplomacy))


@dataclass
class TurnResult:
    """Immutable outcome of processing a single turn."""

    narration: str
    new_state: GameState
    outcome: str  # "continue" | "won" | "lost"
    event: dict | None
    deltas: dict[str, int]

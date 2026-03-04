"""Item catalog, loot rolling, and inventory helpers.

Items come in four rarities (common, uncommon, rare, legendary) and two types:
- **passive**: equippable gear that grants per-turn or situational bonuses.
- **consumable**: single-use items that apply an immediate effect.

Inventory is stored as ``list[dict]`` in ``game_state.inventory``.  Each entry
has the shape ``{"id": str, "qty": int, "equipped": bool}``.
"""

from __future__ import annotations

import random
from typing import Any


# ---------------------------------------------------------------------------
# Item catalog
# ---------------------------------------------------------------------------
# Each entry defines:
#   name        - dict with en/ru translations
#   rarity      - common | uncommon | rare | legendary
#   type        - passive | consumable
#   effect      - dict of stat keys -> numeric values
#   flavor      - dict with en/ru flavour text
# ---------------------------------------------------------------------------

ITEMS: dict[str, dict] = {
    # ── Common (drop weight 60%) ──────────────────────────────────────────
    "rusty_tools": {
        "name": {"en": "Rusty Tools", "ru": "Ржавые инструменты"},
        "rarity": "common",
        "type": "passive",
        "effect": {"scrap_per_turn": 2},
        "flavor": {
            "en": "Bent but functional.",
            "ru": "Погнутые, но рабочие.",
        },
    },
    "dried_rations": {
        "name": {"en": "Dried Rations", "ru": "Сухой паёк"},
        "rarity": "common",
        "type": "consumable",
        "effect": {"food": 25},
        "flavor": {
            "en": "Vacuum-sealed. Tastes like cardboard, but it's calories.",
            "ru": "В вакуумной упаковке. На вкус как картон, но калории есть.",
        },
    },
    "scrap_armor": {
        "name": {"en": "Scrap Armor", "ru": "Хламовая броня"},
        "rarity": "common",
        "type": "passive",
        "effect": {"defense_per_turn": 1},
        "flavor": {
            "en": "Duct tape and car doors. Better than nothing.",
            "ru": "Скотч и автомобильные двери. Лучше, чем ничего.",
        },
    },
    "herbal_pouch": {
        "name": {"en": "Herbal Pouch", "ru": "Травяной мешочек"},
        "rarity": "common",
        "type": "consumable",
        "effect": {"morale": 15},
        "flavor": {
            "en": "Smells like the old world. Calming.",
            "ru": "Пахнет старым миром. Успокаивает.",
        },
    },
    "rusty_knife": {
        "name": {"en": "Rusty Knife", "ru": "Ржавый нож"},
        "rarity": "common",
        "type": "passive",
        "effect": {"explore_pop_loss_reduce": 1},
        "flavor": {
            "en": "Dull edge, but it still cuts.",
            "ru": "Тупое лезвие, но всё ещё режет.",
        },
    },
    "water_flask": {
        "name": {"en": "Water Flask", "ru": "Фляга воды"},
        "rarity": "common",
        "type": "consumable",
        "effect": {"food": 15, "morale": 5},
        "flavor": {
            "en": "Lukewarm and slightly metallic. Delicious.",
            "ru": "Тёплая и слегка металлическая. Восхитительно.",
        },
    },
    "signal_flare": {
        "name": {"en": "Signal Flare", "ru": "Сигнальная ракета"},
        "rarity": "common",
        "type": "consumable",
        "effect": {"defense": 10},
        "flavor": {
            "en": "Bright enough to scare off most threats.",
            "ru": "Достаточно яркая, чтобы отпугнуть большинство угроз.",
        },
    },
    "torn_map": {
        "name": {"en": "Torn Map", "ru": "Рваная карта"},
        "rarity": "common",
        "type": "passive",
        "effect": {"explore_scrap_bonus": 2},
        "flavor": {
            "en": "Half the roads are gone, but the landmarks remain.",
            "ru": "Половина дорог исчезла, но ориентиры на месте.",
        },
    },
    "makeshift_bandage": {
        "name": {"en": "Makeshift Bandage", "ru": "Самодельный бинт"},
        "rarity": "common",
        "type": "consumable",
        "effect": {"population": 2},
        "flavor": {
            "en": "Torn shirt strips. Stops the bleeding, mostly.",
            "ru": "Полоски от рубашки. В основном останавливают кровь.",
        },
    },

    # ── Uncommon (drop weight 25%) ────────────────────────────────────────
    "scout_binoculars": {
        "name": {"en": "Scout Binoculars", "ru": "Бинокль разведчика"},
        "rarity": "uncommon",
        "type": "passive",
        "effect": {"explore_scrap_bonus": 5},
        "flavor": {
            "en": "Military-grade optics. One lens is cracked.",
            "ru": "Военная оптика. Одна линза треснула.",
        },
    },
    "water_purifier": {
        "name": {"en": "Water Purifier", "ru": "Очиститель воды"},
        "rarity": "uncommon",
        "type": "passive",
        "effect": {"food_per_turn": 3},
        "flavor": {
            "en": "Filters the worst of the radiation out. Mostly.",
            "ru": "Отфильтровывает большую часть радиации. В основном.",
        },
    },
    "medkit": {
        "name": {"en": "Medkit", "ru": "Аптечка"},
        "rarity": "uncommon",
        "type": "consumable",
        "effect": {"population": 5, "morale": 10},
        "flavor": {
            "en": "Pre-war medical supplies. Half-expired but effective.",
            "ru": "Довоенные медикаменты. Наполовину просрочены, но работают.",
        },
    },
    "trade_ledger": {
        "name": {"en": "Trade Ledger", "ru": "Торговая книга"},
        "rarity": "uncommon",
        "type": "passive",
        "effect": {"trade_gold_bonus": 3},
        "flavor": {
            "en": "Notes on who owes what. Knowledge is currency.",
            "ru": "Записи о долгах. Знание — это валюта.",
        },
    },
    "reinforced_walls": {
        "name": {"en": "Reinforced Walls", "ru": "Укреплённые стены"},
        "rarity": "uncommon",
        "type": "passive",
        "effect": {"defense_decay_reduce": 1},
        "flavor": {
            "en": "Steel plates welded over weak spots.",
            "ru": "Стальные пластины, приваренные к слабым местам.",
        },
    },
    "morale_banner": {
        "name": {"en": "Morale Banner", "ru": "Знамя надежды"},
        "rarity": "uncommon",
        "type": "passive",
        "effect": {"morale_per_turn": 2},
        "flavor": {
            "en": "A tattered flag that somehow inspires hope.",
            "ru": "Потрёпанный флаг, который каким-то образом вселяет надежду.",
        },
    },
    "lucky_coin": {
        "name": {"en": "Lucky Coin", "ru": "Счастливая монета"},
        "rarity": "uncommon",
        "type": "passive",
        "effect": {"gold_per_turn": 1},
        "flavor": {
            "en": "Found in a skeleton's pocket. Lucky for you, not for them.",
            "ru": "Найдена в кармане скелета. Вам повезло, ему — нет.",
        },
    },
    "field_radio": {
        "name": {"en": "Field Radio", "ru": "Полевая рация"},
        "rarity": "uncommon",
        "type": "passive",
        "effect": {"diplomacy_rep_bonus": 2},
        "flavor": {
            "en": "Crackly signal, but the factions can hear you.",
            "ru": "Хриплый сигнал, но фракции вас слышат.",
        },
    },
    "stimpak": {
        "name": {"en": "Stimpak", "ru": "Стимулятор"},
        "rarity": "uncommon",
        "type": "consumable",
        "effect": {"population": 3, "morale": 5, "food": 10},
        "flavor": {
            "en": "One shot of adrenaline and painkillers. Instant relief.",
            "ru": "Один укол адреналина и обезболивающего. Мгновенное облегчение.",
        },
    },

    # ── Rare (drop weight 12%) ────────────────────────────────────────────
    "hazmat_suit": {
        "name": {"en": "Hazmat Suit", "ru": "Костюм химзащиты"},
        "rarity": "rare",
        "type": "passive",
        "effect": {"event_damage_reduce_pct": 20},
        "flavor": {
            "en": "Bright yellow and mostly intact. Radiation? What radiation?",
            "ru": "Ярко-жёлтый и почти целый. Радиация? Какая радиация?",
        },
    },
    "prewar_radio": {
        "name": {"en": "Pre-War Radio", "ru": "Довоенное радио"},
        "rarity": "rare",
        "type": "passive",
        "effect": {"morale_per_turn": 3, "traders_rep_per_turn": 1},
        "flavor": {
            "en": "Plays old songs. People gather around it every evening.",
            "ru": "Играет старые песни. Люди собираются вокруг каждый вечер.",
        },
    },
    "auto_turret": {
        "name": {"en": "Auto Turret", "ru": "Автотурель"},
        "rarity": "rare",
        "type": "passive",
        "effect": {"defense_per_turn": 3},
        "flavor": {
            "en": "Pre-war tech. Shoots anything that moves too fast.",
            "ru": "Довоенные технологии. Стреляет во всё, что двигается слишком быстро.",
        },
    },
    "supply_cache": {
        "name": {"en": "Supply Cache", "ru": "Тайник припасов"},
        "rarity": "rare",
        "type": "consumable",
        "effect": {"food": 50, "scrap": 50, "gold": 10},
        "flavor": {
            "en": "Someone buried this before the bombs fell. Their loss.",
            "ru": "Кто-то закопал это до бомбёжки. Их потеря.",
        },
    },
    "genetic_serum": {
        "name": {"en": "Genetic Serum", "ru": "Генетическая сыворотка"},
        "rarity": "rare",
        "type": "consumable",
        "effect": {"population": 10},
        "flavor": {
            "en": "Accelerates healing. Side effects may include extra fingers.",
            "ru": "Ускоряет исцеление. Побочные эффекты могут включать лишние пальцы.",
        },
    },
    "master_blueprint": {
        "name": {"en": "Master Blueprint", "ru": "Мастер-чертёж"},
        "rarity": "rare",
        "type": "consumable",
        "effect": {"building_cost_reduce_next": 50},
        "flavor": {
            "en": "Detailed schematics. Your next build will cost half.",
            "ru": "Подробные схемы. Следующая постройка обойдётся в полцены.",
        },
    },

    # ── Legendary (drop weight 3%) ────────────────────────────────────────
    "navigators_map": {
        "name": {"en": "Navigator's Map", "ru": "Карта навигатора"},
        "rarity": "legendary",
        "type": "passive",
        "effect": {"explore_scrap_bonus": 10, "item_drop_bonus_pct": 15},
        "flavor": {
            "en": "Every cache, bunker, and shortcut — marked in red.",
            "ru": "Каждый тайник, бункер и короткий путь — отмечены красным.",
        },
    },
    "nuclear_core": {
        "name": {"en": "Nuclear Core", "ru": "Ядерное ядро"},
        "rarity": "legendary",
        "type": "passive",
        "effect": {"building_effect_bonus_pct": 25},
        "flavor": {
            "en": "Hums softly. Powers everything around it.",
            "ru": "Тихо гудит. Питает всё вокруг.",
        },
    },
    "golden_pipboy": {
        "name": {"en": "Golden Pip-Boy", "ru": "Золотой Пип-Бой"},
        "rarity": "legendary",
        "type": "passive",
        "effect": {"all_per_turn": 1},
        "flavor": {
            "en": "A relic of the old world. Boosts everything, just a little.",
            "ru": "Реликвия старого мира. Усиливает всё, понемногу.",
        },
    },
    "quantum_cell": {
        "name": {"en": "Quantum Cell", "ru": "Квантовая ячейка"},
        "rarity": "legendary",
        "type": "consumable",
        "effect": {"xp": 500},
        "flavor": {
            "en": "Pure crystallised experience. Knowledge floods your mind.",
            "ru": "Чистый кристаллизованный опыт. Знание заполняет разум.",
        },
    },
}


# ---------------------------------------------------------------------------
# Rarity configuration
# ---------------------------------------------------------------------------

_RARITY_ORDER = ("common", "uncommon", "rare", "legendary")

_RARITY_EMOJI: dict[str, str] = {
    "common": "⚪",
    "uncommon": "🟢",
    "rare": "🔵",
    "legendary": "🟡",
}

_RARITY_LABEL: dict[str, dict[str, str]] = {
    "common":    {"en": "Common",    "ru": "Обычный"},
    "uncommon":  {"en": "Uncommon",  "ru": "Необычный"},
    "rare":      {"en": "Rare",      "ru": "Редкий"},
    "legendary": {"en": "Legendary", "ru": "Легендарный"},
}

# Base drop weights per rarity (must sum to 100).
_RARITY_WEIGHTS: dict[str, int] = {
    "common": 60,
    "uncommon": 25,
    "rare": 12,
    "legendary": 3,
}

# Base drop chance per action.
_ACTION_DROP_CHANCE: dict[str, float] = {
    "explore": 0.30,
    "trade": 0.15,
    "defend": 0.10,
    "rest": 0.05,
    "build": 0.05,
    "diplomacy": 0.08,
}

# Maximum equipped passive items.
MAX_EQUIPPED = 5

# Maximum stack size for consumables.
MAX_CONSUMABLE_STACK = 10


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def get_item(item_id: str) -> dict | None:
    """Look up an item by ID.  Returns the catalog entry or ``None``."""
    return ITEMS.get(item_id)


def get_item_name(item_id: str, lang: str = "en") -> str:
    """Return the localised name of *item_id*."""
    spec = ITEMS.get(item_id)
    if spec is None:
        return item_id
    return spec["name"].get(lang, spec["name"]["en"])


def get_rarity_emoji(rarity: str) -> str:
    """Return the emoji for *rarity* (common=⚪, uncommon=🟢, rare=🔵, legendary=🟡)."""
    return _RARITY_EMOJI.get(rarity, "⚪")


def get_rarity_label(rarity: str, lang: str = "en") -> str:
    """Return the localised label for *rarity*."""
    entry = _RARITY_LABEL.get(rarity, _RARITY_LABEL["common"])
    return entry.get(lang, entry["en"])


# ---------------------------------------------------------------------------
# Loot rolling
# ---------------------------------------------------------------------------


def roll_item_drop(
    zone: int,
    action: str,
    equipped_bonuses: dict[str, Any] | None = None,
) -> str | None:
    """Roll for an item drop after an action.

    Returns an ``item_id`` on success or ``None`` if nothing drops.

    Parameters
    ----------
    zone:
        Current game zone (higher zones slightly boost rare/legendary weight).
    action:
        The action the player performed (explore, trade, defend, rest, build, diplomacy).
    equipped_bonuses:
        Aggregated passive bonuses (from :func:`get_equipped_bonuses`).
        ``item_drop_bonus_pct`` increases the base drop chance.
    """
    base_chance = _ACTION_DROP_CHANCE.get(action, 0.05)

    # Apply item_drop_bonus_pct from equipped items (e.g. Navigator's Map).
    if equipped_bonuses:
        bonus_pct = equipped_bonuses.get("item_drop_bonus_pct", 0)
        if bonus_pct > 0:
            base_chance += base_chance * (bonus_pct / 100.0)

    # Roll for whether a drop happens at all.
    if random.random() > base_chance:
        return None

    # Build adjusted rarity weights — zone shifts weight toward rare/legendary.
    weights = dict(_RARITY_WEIGHTS)
    zone_bonus = min(zone - 1, 10)  # cap at zone 11+
    if zone_bonus > 0:
        # Shift a few points from common to rare and legendary.
        shift_rare = zone_bonus
        shift_legendary = zone_bonus // 2
        weights["common"] = max(10, weights["common"] - shift_rare - shift_legendary)
        weights["rare"] += shift_rare
        weights["legendary"] += shift_legendary

    # Pick a rarity.
    rarity = random.choices(
        list(weights.keys()),
        weights=list(weights.values()),
        k=1,
    )[0]

    # Pick a random item of that rarity.
    candidates = [
        iid for iid, spec in ITEMS.items() if spec["rarity"] == rarity
    ]
    if not candidates:
        return None

    return random.choice(candidates)


# ---------------------------------------------------------------------------
# Inventory management
# ---------------------------------------------------------------------------


def get_equipped_bonuses(inventory: list[dict]) -> dict[str, Any]:
    """Aggregate all passive bonuses from equipped items.

    Returns a dict like ``{"scrap_per_turn": 7, "defense_per_turn": 4, ...}``.
    Only items with ``equipped=True`` and ``type="passive"`` are counted.
    """
    totals: dict[str, Any] = {}
    for entry in inventory:
        item_id = entry.get("id")
        if not entry.get("equipped"):
            continue
        spec = ITEMS.get(item_id)
        if spec is None or spec["type"] != "passive":
            continue
        for key, value in spec["effect"].items():
            totals[key] = totals.get(key, 0) + value
    return totals


def add_item_to_inventory(
    inventory: list[dict],
    item_id: str,
) -> list[dict]:
    """Add one copy of *item_id* to *inventory*.

    Consumables stack (up to :data:`MAX_CONSUMABLE_STACK`).  Passive items are
    added as individual entries (qty is always 1).

    Returns the modified inventory list.
    """
    spec = ITEMS.get(item_id)
    if spec is None:
        return inventory

    if spec["type"] == "consumable":
        # Try to stack onto an existing entry.
        for entry in inventory:
            if entry["id"] == item_id:
                if entry["qty"] < MAX_CONSUMABLE_STACK:
                    entry["qty"] += 1
                    return inventory
                break  # stack full — don't add a second entry
        # No existing entry or stack full — new entry.
        if not any(e["id"] == item_id for e in inventory) or all(
            e.get("qty", 1) >= MAX_CONSUMABLE_STACK
            for e in inventory
            if e["id"] == item_id
        ):
            inventory.append({"id": item_id, "qty": 1, "equipped": False})
    else:
        # Passive items don't stack — one entry each.
        # Check if already in inventory (passives are unique).
        if any(e["id"] == item_id for e in inventory):
            return inventory  # already have it
        inventory.append({"id": item_id, "qty": 1, "equipped": False})

    return inventory


def remove_item_from_inventory(
    inventory: list[dict],
    item_id: str,
    qty: int = 1,
) -> list[dict]:
    """Remove *qty* copies of *item_id* from *inventory*.

    If the quantity drops to 0 the entry is removed entirely.
    Returns the modified inventory list.
    """
    for entry in inventory:
        if entry["id"] == item_id:
            entry["qty"] = max(0, entry.get("qty", 1) - qty)
            if entry["qty"] <= 0:
                inventory.remove(entry)
            return inventory
    return inventory


def equip_item(
    inventory: list[dict],
    item_id: str,
) -> tuple[list[dict], bool]:
    """Toggle the equipped state of a passive item.

    If equipping would exceed :data:`MAX_EQUIPPED`, the operation fails.
    Returns ``(updated_inventory, success)``.
    """
    spec = ITEMS.get(item_id)
    if spec is None or spec["type"] != "passive":
        return inventory, False

    entry = None
    for e in inventory:
        if e["id"] == item_id:
            entry = e
            break

    if entry is None:
        return inventory, False

    currently_equipped = entry.get("equipped", False)

    if currently_equipped:
        # Unequip — always succeeds.
        entry["equipped"] = False
        return inventory, True

    # Equip — check slot limit.
    equipped_count = sum(
        1 for e in inventory
        if e.get("equipped") and ITEMS.get(e["id"], {}).get("type") == "passive"
    )
    if equipped_count >= MAX_EQUIPPED:
        return inventory, False

    entry["equipped"] = True
    return inventory, True


def get_inventory_display(inventory: list[dict], lang: str = "en") -> str:
    """Format the full inventory as a text block for display.

    Passive items show ``[equipped]`` or ``[unequipped]``.
    Consumables show the quantity.
    """
    if not inventory:
        if lang == "ru":
            return "Инвентарь пуст."
        return "Inventory is empty."

    # Separate passives and consumables.
    passives: list[str] = []
    consumables: list[str] = []

    for entry in inventory:
        item_id = entry["id"]
        spec = ITEMS.get(item_id)
        if spec is None:
            continue

        emoji = get_rarity_emoji(spec["rarity"])
        name = spec["name"].get(lang, spec["name"]["en"])
        flavor = spec["flavor"].get(lang, spec["flavor"]["en"])

        if spec["type"] == "passive":
            if lang == "ru":
                status = "[экипировано]" if entry.get("equipped") else "[не экипировано]"
            else:
                status = "[equipped]" if entry.get("equipped") else "[unequipped]"
            passives.append(f"{emoji} *{name}* {status}\n      _{flavor}_")
        else:
            qty = entry.get("qty", 1)
            consumables.append(f"{emoji} *{name}* x{qty}\n      _{flavor}_")

    lines: list[str] = []

    if passives:
        header = "Снаряжение" if lang == "ru" else "Equipment"
        lines.append(f"*{header}*")
        lines.extend(passives)
        lines.append("")

    if consumables:
        header = "Расходники" if lang == "ru" else "Consumables"
        lines.append(f"*{header}*")
        lines.extend(consumables)

    equipped_count = sum(
        1 for e in inventory
        if e.get("equipped") and ITEMS.get(e["id"], {}).get("type") == "passive"
    )
    if lang == "ru":
        lines.append(f"\nЭкипировано: {equipped_count}/{MAX_EQUIPPED}")
    else:
        lines.append(f"\nEquipped: {equipped_count}/{MAX_EQUIPPED}")

    return "\n".join(lines)


def format_effect_description(effect: dict[str, Any], lang: str = "en") -> str:
    """Return a human-readable description of an item's effect dict."""
    parts: list[str] = []
    _labels = {
        "food": "🌾",
        "scrap": "🔩",
        "gold": "💰",
        "population": "👥",
        "morale": "😊",
        "defense": "🛡",
        "xp": "✨",
        "food_per_turn": "🌾/turn" if lang != "ru" else "🌾/ход",
        "scrap_per_turn": "🔩/turn" if lang != "ru" else "🔩/ход",
        "gold_per_turn": "💰/turn" if lang != "ru" else "💰/ход",
        "morale_per_turn": "😊/turn" if lang != "ru" else "😊/ход",
        "defense_per_turn": "🛡/turn" if lang != "ru" else "🛡/ход",
        "all_per_turn": ("all/turn" if lang != "ru" else "все/ход"),
        "explore_scrap_bonus": "🔩 explore" if lang != "ru" else "🔩 разведка",
        "explore_pop_loss_reduce": ("👥 explore loss -" if lang != "ru"
                                    else "👥 потери разведки -"),
        "trade_gold_bonus": "💰 trade" if lang != "ru" else "💰 торговля",
        "defense_decay_reduce": ("🛡 decay -" if lang != "ru"
                                 else "🛡 износ -"),
        "diplomacy_rep_bonus": ("🤝 rep" if lang != "ru" else "🤝 репутация"),
        "event_damage_reduce_pct": ("event dmg -%"
                                    if lang != "ru" else "урон событий -%"),
        "item_drop_bonus_pct": ("🎁 drop +%" if lang != "ru" else "🎁 дроп +%"),
        "building_effect_bonus_pct": ("🏗 building +%"
                                      if lang != "ru" else "🏗 здания +%"),
        "building_cost_reduce_next": ("🏗 next build -%"
                                      if lang != "ru" else "🏗 след. здание -%"),
        "traders_rep_per_turn": ("💰 traders rep/turn"
                                 if lang != "ru" else "💰 репутация торговцев/ход"),
    }
    for key, value in effect.items():
        label = _labels.get(key, key)
        parts.append(f"+{value} {label}")
    return ", ".join(parts) if parts else "—"

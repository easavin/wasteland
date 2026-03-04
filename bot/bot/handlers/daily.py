"""Handler for /daily command — daily login streak rewards."""

from __future__ import annotations

import logging
import math
import random
from datetime import date, datetime, timedelta, timezone

from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from bot.db.queries.players import get_player_by_telegram_id
from bot.db.queries.game_states import get_active_game, update_game_state
from bot.engine.game_state import GameState
from bot.i18n import get_text

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Day reward table (1-7 repeating cycle)
# ---------------------------------------------------------------------------
# Types: "resource" (scrap/food/gold) or "item" (uncommon/rare)
DAY_REWARDS: list[dict] = [
    # Day 1
    {"type": "resource", "resource": "scrap", "amount": 30, "emoji": "🔩"},
    # Day 2
    {"type": "resource", "resource": "food", "amount": 20, "emoji": "🌾"},
    # Day 3
    {"type": "resource", "resource": "gold", "amount": 5, "emoji": "💰"},
    # Day 4
    {"type": "resource", "resource": "scrap", "amount": 50, "emoji": "🔩"},
    # Day 5
    {"type": "item", "rarity": "uncommon"},
    # Day 6
    {"type": "resource", "resource": "gold", "amount": 10, "emoji": "💰"},
    # Day 7
    {"type": "item", "rarity": "rare"},
]

# Items that can drop as daily rewards
DAILY_ITEMS: dict[str, list[dict]] = {
    "uncommon": [
        {
            "name": {"en": "Rusty Toolkit", "ru": "Ржавый набор инструментов"},
            "description": {"en": "A battered but functional set of tools.", "ru": "Потрёпанный, но рабочий набор инструментов."},
            "rarity": "uncommon",
            "emoji": "🔧",
        },
        {
            "name": {"en": "Scavenger's Map", "ru": "Карта старателя"},
            "description": {"en": "Crude map marking salvage spots.", "ru": "Грубая карта с отметками мест для сбора."},
            "rarity": "uncommon",
            "emoji": "🗺",
        },
        {
            "name": {"en": "Water Purifier", "ru": "Очиститель воды"},
            "description": {"en": "Portable filter — turns mud into drinkable water.", "ru": "Портативный фильтр — превращает грязь в питьевую воду."},
            "rarity": "uncommon",
            "emoji": "💧",
        },
        {
            "name": {"en": "Reinforced Tarp", "ru": "Усиленный брезент"},
            "description": {"en": "Durable shelter material for your settlement.", "ru": "Прочный материал для укрытий поселения."},
            "rarity": "uncommon",
            "emoji": "🏚",
        },
        {
            "name": {"en": "Med Pouch", "ru": "Аптечка"},
            "description": {"en": "Basic medical supplies — bandages, antiseptic, painkillers.", "ru": "Базовые медикаменты — бинты, антисептик, обезболивающие."},
            "rarity": "uncommon",
            "emoji": "💊",
        },
    ],
    "rare": [
        {
            "name": {"en": "Pre-War Generator", "ru": "Довоенный генератор"},
            "description": {"en": "A working generator from the old world. Precious beyond measure.", "ru": "Работающий генератор из старого мира. Бесценная находка."},
            "rarity": "rare",
            "emoji": "⚡",
        },
        {
            "name": {"en": "Encrypted Data Chip", "ru": "Зашифрованный чип данных"},
            "description": {"en": "Contains fragments of pre-war knowledge.", "ru": "Содержит фрагменты довоенных знаний."},
            "rarity": "rare",
            "emoji": "💾",
        },
        {
            "name": {"en": "Military-Grade Armor", "ru": "Военная броня"},
            "description": {"en": "Composite plating — lightweight and nearly impenetrable.", "ru": "Композитное покрытие — лёгкое и почти непробиваемое."},
            "rarity": "rare",
            "emoji": "🛡",
        },
        {
            "name": {"en": "Nano-Med Injector", "ru": "Нано-медицинский инъектор"},
            "description": {"en": "One shot can heal wounds that would kill in hours.", "ru": "Один укол исцеляет раны, от которых умирают за часы."},
            "rarity": "rare",
            "emoji": "💉",
        },
        {
            "name": {"en": "AI Core Fragment", "ru": "Фрагмент ядра ИИ"},
            "description": {"en": "A shard of a pre-war artificial intelligence. It hums softly.", "ru": "Осколок довоенного искусственного интеллекта. Тихо гудит."},
            "rarity": "rare",
            "emoji": "🧠",
        },
    ],
}

# Tier names for display
TIER_NAMES: dict[int, dict[str, str]] = {
    0: {"en": "Newcomer", "ru": "Новичок"},
    1: {"en": "Regular", "ru": "Завсегдатай"},
    2: {"en": "Devoted", "ru": "Преданный"},
    3: {"en": "Veteran", "ru": "Ветеран"},
    4: {"en": "Legendary", "ru": "Легендарный"},
    5: {"en": "Mythic", "ru": "Мифический"},
}


# ---------------------------------------------------------------------------
# DB helper
# ---------------------------------------------------------------------------

async def update_daily_streak(
    pool, player_id: str, streak: int, tier: int, claim_date: date,
) -> None:
    """Update daily streak columns on the players table."""
    await pool.execute(
        """
        UPDATE players
           SET daily_streak      = $1,
               daily_streak_tier = $2,
               last_daily_claim  = $3,
               updated_at        = NOW()
         WHERE id = $4
        """,
        streak, tier, claim_date, player_id,
    )


# ---------------------------------------------------------------------------
# Command handler
# ---------------------------------------------------------------------------

async def handle_daily(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/daily — claim daily login reward."""
    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, update.effective_user.id)
    if not player:
        await update.message.reply_text(get_text("free_text_no_game", "en"))
        return

    lang = player.get("language", "en")
    player_id = str(player["id"])

    game_row = await get_active_game(pool, player_id)
    if not game_row:
        await update.message.reply_text(get_text("free_text_no_game", lang))
        return

    state = GameState.from_db_row(game_row)

    today = date.today()
    last_claim = player.get("last_daily_claim")
    old_streak = player.get("daily_streak", 0)
    streak_tier = player.get("daily_streak_tier", 0)

    # --- Already claimed today ---
    if last_claim == today:
        day_in_cycle = (old_streak - 1) % 7 + 1
        tomorrow_day = old_streak % 7 + 1
        tomorrow_reward = DAY_REWARDS[tomorrow_day - 1]
        tomorrow_preview = _format_reward_preview(tomorrow_reward, lang, streak_tier)

        # Countdown to midnight
        now = datetime.now(timezone.utc)
        midnight = datetime.combine(today + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
        delta = midnight - now
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60

        text = get_text(
            "daily_already_claimed", lang,
            hours=hours, minutes=minutes,
            tomorrow_preview=tomorrow_preview,
            progress=_format_streak_progress(old_streak, lang),
        )
        try:
            await update.message.reply_text(text, parse_mode="Markdown")
        except BadRequest:
            await update.message.reply_text(text)
        return

    # --- Calculate new streak ---
    if last_claim is not None and last_claim == today - timedelta(days=1):
        # Consecutive day
        new_streak = old_streak + 1
    else:
        # Streak broken or first claim
        new_streak = 1

    day_in_cycle = (new_streak - 1) % 7 + 1
    reward_spec = DAY_REWARDS[day_in_cycle - 1]

    # Check if day 7 was just completed (streak tier up)
    new_tier = streak_tier
    tier_up = False
    if day_in_cycle == 7:
        new_tier = min(5, streak_tier + 1)
        tier_up = True

    # --- Apply reward ---
    reward_text = ""
    if reward_spec["type"] == "resource":
        resource = reward_spec["resource"]
        base_amount = reward_spec["amount"]
        # Apply tier multiplier: +10% per tier (floor)
        amount = base_amount + math.floor(base_amount * 0.10 * streak_tier)
        emoji = reward_spec["emoji"]

        # Update game state
        current_val = getattr(state, resource, 0)
        setattr(state, resource, current_val + amount)
        await update_game_state(pool, state.id, **{resource: getattr(state, resource)})

        resource_names = {
            "scrap": {"en": "scrap", "ru": "хлама"},
            "food": {"en": "food", "ru": "еды"},
            "gold": {"en": "gold", "ru": "золота"},
        }
        rname = resource_names.get(resource, {}).get(lang, resource)
        reward_text = f"{emoji} +{amount} {rname}"
        if streak_tier > 0 and amount > base_amount:
            bonus = amount - base_amount
            bonus_label = {"en": "tier bonus", "ru": "бонус ранга"}.get(lang, "tier bonus")
            reward_text += f" _(+{bonus} {bonus_label})_"

    elif reward_spec["type"] == "item":
        rarity = reward_spec["rarity"]
        item = random.choice(DAILY_ITEMS[rarity])
        item_name = item["name"].get(lang, item["name"]["en"])
        item_emoji = item["emoji"]

        # Add to inventory
        inv_entry = {
            "name": item["name"]["en"],
            "name_ru": item["name"].get("ru", item["name"]["en"]),
            "description": item["description"]["en"],
            "description_ru": item["description"].get("ru", item["description"]["en"]),
            "rarity": item["rarity"],
            "emoji": item_emoji,
            "source": "daily_reward",
        }
        state.inventory.append(inv_entry)
        await update_game_state(pool, state.id, inventory=state.inventory)

        rarity_labels = {
            "uncommon": {"en": "Uncommon", "ru": "Необычный"},
            "rare": {"en": "Редкий", "ru": "Rare"},
        }
        rarity_label = rarity_labels.get(rarity, {}).get(lang, rarity.title())
        reward_text = f"{item_emoji} *{item_name}* ({rarity_label})"

    # --- Update player streak ---
    await update_daily_streak(pool, player_id, new_streak, new_tier, today)

    # --- Build response ---
    progress = _format_streak_progress(new_streak, lang)

    # Tomorrow preview
    if day_in_cycle < 7:
        tomorrow_day = day_in_cycle + 1
    else:
        tomorrow_day = 1
    tomorrow_reward = DAY_REWARDS[tomorrow_day - 1]
    tomorrow_preview = _format_reward_preview(tomorrow_reward, lang, new_tier)

    # Tier-up message
    tier_msg = ""
    if tier_up:
        tier_name = TIER_NAMES.get(new_tier, {}).get(lang, f"Tier {new_tier}")
        tier_msg = get_text("daily_tier_up", lang, tier=new_tier, tier_name=tier_name)

    text = get_text(
        "daily_claimed", lang,
        day=day_in_cycle,
        streak=new_streak,
        reward=reward_text,
        progress=progress,
        tomorrow=tomorrow_preview,
        tier_msg=tier_msg,
    )

    try:
        await update.message.reply_text(text, parse_mode="Markdown")
    except BadRequest:
        await update.message.reply_text(text)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _format_streak_progress(current_streak: int, lang: str) -> str:
    """Visual progress bar for day 1-7 cycle.

    Example: ✅✅✅⬜⬜⬜⬜ (Day 3/7)
    """
    day_in_cycle = (current_streak - 1) % 7 + 1 if current_streak > 0 else 0
    boxes = ""
    for d in range(1, 8):
        if d <= day_in_cycle:
            boxes += "✅"
        else:
            boxes += "⬜"
    day_label = {"en": "Day", "ru": "День"}.get(lang, "Day")
    return f"{boxes} ({day_label} {day_in_cycle}/7)"


def _format_reward_preview(reward: dict, lang: str, tier: int) -> str:
    """Short text describing what tomorrow's reward is."""
    if reward["type"] == "resource":
        resource = reward["resource"]
        base = reward["amount"]
        amount = base + math.floor(base * 0.10 * tier)
        emoji = reward["emoji"]
        resource_names = {
            "scrap": {"en": "scrap", "ru": "хлама"},
            "food": {"en": "food", "ru": "еды"},
            "gold": {"en": "gold", "ru": "золота"},
        }
        rname = resource_names.get(resource, {}).get(lang, resource)
        return f"{emoji} +{amount} {rname}"
    elif reward["type"] == "item":
        rarity = reward["rarity"]
        rarity_labels = {
            "uncommon": {"en": "Uncommon item", "ru": "Необычный предмет"},
            "rare": {"en": "Rare item", "ru": "Редкий предмет"},
        }
        label = rarity_labels.get(rarity, {}).get(lang, f"{rarity} item")
        emoji = "🎁"
        return f"{emoji} {label}"
    return "?"


# ---------------------------------------------------------------------------
# i18n strings — to be bulk-merged into bot/i18n/__init__.py later
# ---------------------------------------------------------------------------

DAILY_STRINGS: dict[str, dict[str, str]] = {
    "daily_already_claimed": {
        "en": (
            "📅 *Daily Reward*\n\n"
            "You already claimed today's reward!\n"
            "Next reward in *{hours}h {minutes}m*.\n\n"
            "{progress}\n\n"
            "Tomorrow: {tomorrow_preview}"
        ),
        "ru": (
            "📅 *Ежедневная награда*\n\n"
            "Ты уже забрал(а) сегодняшнюю награду!\n"
            "Следующая через *{hours}ч {minutes}мин*.\n\n"
            "{progress}\n\n"
            "Завтра: {tomorrow_preview}"
        ),
    },
    "daily_claimed": {
        "en": (
            "📅 *Daily Reward — Day {day}*\n\n"
            "🔥 Streak: *{streak} days*\n\n"
            "Reward: {reward}\n\n"
            "{progress}\n\n"
            "Tomorrow: {tomorrow}"
            "{tier_msg}"
        ),
        "ru": (
            "📅 *Ежедневная награда — День {day}*\n\n"
            "🔥 Серия: *{streak} дней*\n\n"
            "Награда: {reward}\n\n"
            "{progress}\n\n"
            "Завтра: {tomorrow}"
            "{tier_msg}"
        ),
    },
    "daily_tier_up": {
        "en": (
            "\n\n🏆 *STREAK TIER UP!*\n"
            "You reached *Tier {tier}: {tier_name}*!\n"
            "All resource rewards now get a +{tier}0% bonus!"
        ),
        "ru": (
            "\n\n🏆 *РАНГ СЕРИИ ПОВЫШЕН!*\n"
            "Ты достиг(ла) *Ранга {tier}: {tier_name}*!\n"
            "Все ресурсные награды теперь получают бонус +{tier}0%!"
        ),
    },
}

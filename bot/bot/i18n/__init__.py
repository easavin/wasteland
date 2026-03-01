"""Internationalisation helpers and string catalog for Wasteland Chronicles.

Usage::

    from bot.i18n import get_text

    msg = get_text("welcome", language="ru", name="Evgeny")
"""

from __future__ import annotations

_STRINGS: dict[str, dict[str, str]] = {
    # --- Start / onboarding ---
    "welcome": {
        "en": (
            "Welcome to the Wasteland, {name}.\n\n"
            "The world ended. What remained is dust, rust, and desperate survivors.\n"
            "You founded *{settlement}* -- a fragile settlement on the edge of nothing.\n\n"
            "50 turns. That is all you have to build something that endures.\n"
            "Gather resources, raise walls, forge alliances -- or perish.\n\n"
            "Your people are watching. Lead them."
        ),
        "ru": (
            "Добро пожаловать в Пустошь, {name}.\n\n"
            "Мир погиб. Остались пыль, ржавчина и отчаявшиеся выжившие.\n"
            "Ты основал(а) *{settlement}* -- хрупкое поселение на краю пустоты.\n\n"
            "50 ходов. Столько у тебя есть, чтобы построить что-то, что выстоит.\n"
            "Собирай ресурсы, возводи стены, заключай союзы -- или погибни.\n\n"
            "Твои люди смотрят. Веди их."
        ),
    },
    "welcome_back": {
        "en": (
            "Welcome back, {name}.\n\n"
            "*{settlement}* still stands. Your people await your orders.\n"
            "Turn {turn}/50."
        ),
        "ru": (
            "С возвращением, {name}.\n\n"
            "*{settlement}* всё ещё стоит. Твои люди ждут приказов.\n"
            "Ход {turn}/50."
        ),
    },
    "settlement_default_name": {
        "en": "{name}'s Haven",
        "ru": "Убежище {name}",
    },
    # --- Status ---
    "status_header": {
        "en": "--- *{settlement}* --- Turn {turn}/50 ---",
        "ru": "--- *{settlement}* --- Ход {turn}/50 ---",
    },
    "status_resources": {
        "en": "Resources:",
        "ru": "Ресурсы:",
    },
    "status_factions": {
        "en": "Factions:",
        "ru": "Фракции:",
    },
    "status_buildings": {
        "en": "Buildings:",
        "ru": "Постройки:",
    },
    "status_no_buildings": {
        "en": "  (none yet)",
        "ru": "  (пока нет)",
    },
    # --- Actions ---
    "action_build": {
        "en": "Build",
        "ru": "Строить",
    },
    "action_explore": {
        "en": "Explore",
        "ru": "Разведка",
    },
    "action_trade": {
        "en": "Trade",
        "ru": "Торговля",
    },
    "action_defend": {
        "en": "Defend",
        "ru": "Оборона",
    },
    "action_diplomacy": {
        "en": "Diplomacy",
        "ru": "Дипломатия",
    },
    "action_rest": {
        "en": "Rest",
        "ru": "Отдых",
    },
    "action_status": {
        "en": "Status",
        "ru": "Статус",
    },
    "action_back": {
        "en": "Back",
        "ru": "Назад",
    },
    # --- Build menu ---
    "build_menu_header": {
        "en": "Choose a building to construct:",
        "ru": "Выберите постройку:",
    },
    # --- Turn results ---
    "turn_rate_limited": {
        "en": (
            "You've used all {max_turns} turns for today.\n"
            "Upgrade to Premium for unlimited turns!"
        ),
        "ru": (
            "Вы использовали все {max_turns} ходов за сегодня.\n"
            "Перейдите на Премиум для безлимитных ходов!"
        ),
    },
    "turn_invalid_action": {
        "en": "Unknown action: {action}. Choose from the buttons below.",
        "ru": "Неизвестное действие: {action}. Выберите из кнопок ниже.",
    },
    "delta_summary": {
        "en": "Changes:",
        "ru": "Изменения:",
    },
    # --- Win / Loss ---
    "game_won": {
        "en": (
            "VICTORY!\n\n"
            "*{settlement}* has become a beacon of hope in the Wasteland.\n"
            "Population: {population} | Morale: {morale}\n\n"
            "Your legacy will be remembered. Start /newgame to try again."
        ),
        "ru": (
            "ПОБЕДА!\n\n"
            "*{settlement}* стал маяком надежды в Пустоши.\n"
            "Население: {population} | Мораль: {morale}\n\n"
            "Твоё наследие запомнят. Начни /newgame, чтобы попробовать снова."
        ),
    },
    "game_lost": {
        "en": (
            "DEFEAT.\n\n"
            "The Wasteland has claimed *{settlement}*.\n"
            "The dust settles over what remains.\n\n"
            "Start /newgame to try again."
        ),
        "ru": (
            "ПОРАЖЕНИЕ.\n\n"
            "Пустошь поглотила *{settlement}*.\n"
            "Пыль оседает на руинах.\n\n"
            "Начни /newgame, чтобы попробовать снова."
        ),
    },
    # --- New game ---
    "new_game_abandoned": {
        "en": "Your previous settlement has been abandoned. A new chapter begins.",
        "ru": "Ваше предыдущее поселение было покинуто. Начинается новая глава.",
    },
    "new_game_started": {
        "en": "A new settlement rises from the dust.",
        "ru": "Новое поселение поднимается из пыли.",
    },
    # --- Help ---
    "help_text": {
        "en": (
            "*Wasteland Chronicles* -- Survival Strategy Bot\n\n"
            "*Commands:*\n"
            "/start -- Begin or resume your game\n"
            "/status -- View settlement status\n"
            "/newgame -- Start a new game (abandons current)\n"
            "/help -- Show this help\n\n"
            "*Actions (use buttons or type):*\n"
            "Build -- Construct buildings (costs scrap)\n"
            "Explore -- Scavenge for scrap (risky)\n"
            "Trade -- Exchange scrap for food\n"
            "Defend -- Fortify your settlement\n"
            "Diplomacy -- Improve faction relations\n"
            "Rest -- Recover morale\n\n"
            "*Resources:*\n"
            "Population -- Your settlers (0 = defeat)\n"
            "Food -- Consumed each turn (0 for 2 turns = defeat)\n"
            "Scrap -- Building material and trade currency\n"
            "Morale -- Affects population growth (0-100)\n"
            "Defense -- Protection from attacks (0-100)\n\n"
            "*Win:* Reach turn 50 with 100+ population and 60+ morale\n"
            "*Lose:* Population hits 0, or food stays at 0 for 2+ turns\n\n"
            "You get {max_turns} turns/day. Premium = unlimited."
        ),
        "ru": (
            "*Хроники Пустоши* -- Стратегический бот выживания\n\n"
            "*Команды:*\n"
            "/start -- Начать или продолжить игру\n"
            "/status -- Посмотреть статус поселения\n"
            "/newgame -- Начать новую игру (текущая будет брошена)\n"
            "/help -- Показать справку\n\n"
            "*Действия (кнопки или текст):*\n"
            "Строить -- Возводить постройки (стоит хлам)\n"
            "Разведка -- Искать хлам (рискованно)\n"
            "Торговля -- Менять хлам на еду\n"
            "Оборона -- Укреплять поселение\n"
            "Дипломатия -- Улучшать отношения с фракциями\n"
            "Отдых -- Восстановить мораль\n\n"
            "*Ресурсы:*\n"
            "Население -- Ваши поселенцы (0 = поражение)\n"
            "Еда -- Расходуется каждый ход (0 два хода = поражение)\n"
            "Хлам -- Стройматериал и валюта\n"
            "Мораль -- Влияет на рост населения (0-100)\n"
            "Оборона -- Защита от атак (0-100)\n\n"
            "*Победа:* Дожить до 50 хода с 100+ населением и 60+ моралью\n"
            "*Поражение:* Население = 0, или еда = 0 два хода подряд\n\n"
            "У вас {max_turns} ходов/день. Премиум = безлимит."
        ),
    },
    # --- Onboarding tutorial ---
    "onboarding_guide": {
        "en": (
            "*Survivor's Field Guide*\n\n"
            "You have *50 weeks* to build a settlement worth surviving for.\n\n"
            "*Resources — watch these like your life depends on it:*\n"
            "👥 *Population* — your people. If this hits 0, it's over.\n"
            "🌾 *Food* — consumed every week. Two weeks at zero = collapse.\n"
            "🔩 *Scrap* — metal, wire, salvage. Your build currency.\n"
            "😊 *Morale* — keep it up or your people stop growing.\n"
            "🛡 *Defense* — protection when the Raiders come knocking.\n\n"
            "*Your weekly actions:*\n"
            "🏗 *Build* — spend scrap to raise farms, workshops, walls, and more.\n"
            "🔍 *Explore* — scavenge ruins for scrap. Risky. Worth it.\n"
            "💰 *Trade* — swap scrap for food with passing caravans.\n"
            "🛡 *Defend* — reinforce your walls before the next attack.\n"
            "🤝 *Diplomacy* — negotiate with Raiders, Traders, or Remnants.\n"
            "😴 *Rest* — let everyone breathe. Morale recovers.\n\n"
            "*Win:* Reach Week 50 with 100+ population and 60+ morale.\n"
            "*Lose:* Population hits 0, or you starve for 2 weeks running.\n\n"
            "One action per week. Choose carefully."
        ),
        "ru": (
            "*Полевое руководство выжившего*\n\n"
            "У тебя *50 недель*, чтобы построить поселение, достойное выживания.\n\n"
            "*Ресурсы — следи за ними, как за жизнью:*\n"
            "👥 *Население* — твои люди. Упадёт до 0 — конец.\n"
            "🌾 *Еда* — расходуется каждую неделю. Два хода без еды = крах.\n"
            "🔩 *Хлам* — металл, провода, мусор. Твоя строительная валюта.\n"
            "😊 *Мораль* — держи на уровне, иначе люди перестанут прибывать.\n"
            "🛡 *Оборона* — защита, когда рейдеры придут постучать.\n\n"
            "*Твои еженедельные действия:*\n"
            "🏗 *Строить* — трать хлам на фермы, мастерские, стены и не только.\n"
            "🔍 *Разведка* — рыскай по руинам в поисках хлама. Рискованно. Выгодно.\n"
            "💰 *Торговля* — меняй хлам на еду у проходящих торговцев.\n"
            "🛡 *Оборона* — укрепляй стены до следующего налёта.\n"
            "🤝 *Дипломатия* — переговоры с Рейдерами, Торговцами или Остатками.\n"
            "😴 *Отдых* — дай людям передышку. Мораль восстановится.\n\n"
            "*Победа:* Дожить до недели 50 с 100+ населением и 60+ моралью.\n"
            "*Поражение:* Население = 0, или голод два хода подряд.\n\n"
            "Одно действие в неделю. Выбирай осторожно."
        ),
    },
    # --- Free text parsing ---
    "free_text_no_narrator": {
        "en": "I couldn't understand that. Use the action buttons or type: build, explore, trade, defend, diplomacy, rest.",
        "ru": "Не удалось понять. Используйте кнопки или напишите: строить, разведка, торговля, оборона, дипломатия, отдых.",
    },
    "free_text_no_game": {
        "en": "You don't have an active game. Send /start to begin!",
        "ru": "У вас нет активной игры. Отправьте /start, чтобы начать!",
    },
    # --- Faction status labels ---
    "faction_allied": {"en": "Allied", "ru": "Союзник"},
    "faction_friendly": {"en": "Friendly", "ru": "Дружелюбный"},
    "faction_neutral": {"en": "Neutral", "ru": "Нейтральный"},
    "faction_unfriendly": {"en": "Враждебный", "ru": "Недружелюбный"},
    "faction_hostile": {"en": "Hostile", "ru": "Враждебный"},
}


def get_text(key: str, language: str = "en", **kwargs: object) -> str:
    """Look up a localised string by *key* and format it with *kwargs*.

    Falls back to English if the requested language is missing, and returns
    the raw key if the string is not found at all.
    """
    entry = _STRINGS.get(key)
    if entry is None:
        return str(key)
    template = entry.get(language, entry.get("en", str(key)))
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError):
        return template

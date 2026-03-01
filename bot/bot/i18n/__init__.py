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
            "Gather resources, raise walls, forge alliances -- or perish.\n"
            "Level up, grow stronger, conquer new zones.\n\n"
            "Your people are watching. Lead them."
        ),
        "ru": (
            "Добро пожаловать в Пустошь, {name}.\n\n"
            "Мир погиб. Остались пыль, ржавчина и отчаявшиеся выжившие.\n"
            "Ты основал(а) *{settlement}* -- хрупкое поселение на краю пустоты.\n\n"
            "Собирай ресурсы, возводи стены, заключай союзы -- или погибни.\n"
            "Повышай уровень, становись сильнее, покоряй новые зоны.\n\n"
            "Твои люди смотрят. Веди их."
        ),
    },
    "welcome_back": {
        "en": (
            "Welcome back, {name}.\n\n"
            "*{settlement}* still stands. Your people await your orders.\n"
            "Week {turn}."
        ),
        "ru": (
            "С возвращением, {name}.\n\n"
            "*{settlement}* всё ещё стоит. Твои люди ждут приказов.\n"
            "Неделя {turn}."
        ),
    },
    "pre_class_intro": {
        "en": (
            "\\*khhh\\* ... signal acquired ... \\*khhh\\*\n\n"
            "You hear that? That's the sound of a shortwave radio finding its frequency.\n\n"
            "You've been walking for weeks. Fifty souls behind you, "
            "half-starved, carrying what's left of the old world on their backs. "
            "But you found it — a ruin. Walls. A place that could become something.\n\n"
            "I'm the Navigator. I've been watching this frequency, waiting "
            "for someone worth talking to. Maybe that's you.\n\n"
            "Before we go further — *who are you?*\n"
            "Your past matters out here. It decides how you survive.\n\n"
            "Tap a class to select, or tap ℹ️ to learn more about each one."
        ),
        "ru": (
            "\\*кшшш\\* ... сигнал пойман ... \\*кшшш\\*\n\n"
            "Слышишь? Это коротковолновое радио нашло частоту.\n\n"
            "Ты шёл(а) неделями. Пятьдесят душ за спиной, "
            "полуголодных, тащат на себе обломки старого мира. "
            "Но ты нашёл(а) это — руины. Стены. Место, которое может стать чем-то.\n\n"
            "Я — Навигатор. Я слушал эту частоту, ждал "
            "кого-то, с кем стоит говорить. Может, это ты.\n\n"
            "Прежде чем продолжим — *кто ты?*\n"
            "Твоё прошлое решает, как ты выживешь.\n\n"
            "Нажми на класс, чтобы выбрать, или ℹ️ чтобы узнать подробнее."
        ),
    },
    "class_selection": {
        "en": (
            "Before you step into the Wasteland, choose who you are.\n\n"
            "🔍 *Scavenger* -- Finds more scrap exploring ruins\n"
            "🛡 *Warden* -- Military leader, walls hold longer\n"
            "💰 *Trader* -- Caravan boss, better trade deals\n"
            "🕊 *Diplomat* -- Smooth talker, faster faction rep\n"
            "💊 *Medic* -- Field surgeon, keeps people alive\n\n"
            "Choose your path:"
        ),
        "ru": (
            "Прежде чем шагнуть в Пустошь, выбери, кто ты.\n\n"
            "🔍 *Старатель* -- Находит больше хлама в руинах\n"
            "🛡 *Страж* -- Военный лидер, стены стоят дольше\n"
            "💰 *Торговец* -- Глава каравана, лучшие сделки\n"
            "🕊 *Дипломат* -- Мастер переговоров, быстрее рост репутации\n"
            "💊 *Медик* -- Полевой хирург, спасает людей\n\n"
            "Выбери свой путь:"
        ),
    },
    "class_info_scavenger": {
        "en": (
            "🔍 *Scavenger — Wasteland Salvage Expert*\n\n"
            "*Strengths:*\n"
            "  ✅ +20% scrap from exploring ruins\n"
            "  ✅ +1 morale bonus when exploring\n"
            "  ✅ Starts with extra scrap (110 vs 80)\n\n"
            "*Weaknesses:*\n"
            "  ❌ Starts with less food (90 vs 100)\n"
            "  ❌ No combat or diplomatic bonuses\n\n"
            "*Passive:* _Resourceful_ — every expedition brings back more.\n"
            "*Best for:* Players who love exploring and building."
        ),
        "ru": (
            "🔍 *Старатель — Мастер поиска в Пустоши*\n\n"
            "*Сильные стороны:*\n"
            "  ✅ +20% хлама при разведке руин\n"
            "  ✅ +1 бонус морали при разведке\n"
            "  ✅ Начинает с доп. хламом (110 vs 80)\n\n"
            "*Слабые стороны:*\n"
            "  ❌ Начинает с меньшим кол-вом еды (90 vs 100)\n"
            "  ❌ Нет боевых или дипломатических бонусов\n\n"
            "*Пассивка:* _Находчивость_ — каждая экспедиция приносит больше.\n"
            "*Лучше всего для:* Игроков, которые любят исследовать и строить."
        ),
    },
    "class_info_warden": {
        "en": (
            "🛡 *Warden — Military Discipline Leader*\n\n"
            "*Strengths:*\n"
            "  ✅ Defense decays slowly (-1/turn vs -3/turn)\n"
            "  ✅ +5 extra defense when fortifying\n"
            "  ✅ Starts with high defense (50) and morale (75)\n\n"
            "*Weaknesses:*\n"
            "  ❌ No economic bonuses\n"
            "  ❌ Default starting food and scrap\n\n"
            "*Passive:* _Fortified_ — your walls endure where others crumble.\n"
            "*Best for:* Players who want a safe, well-defended settlement."
        ),
        "ru": (
            "🛡 *Страж — Военный лидер*\n\n"
            "*Сильные стороны:*\n"
            "  ✅ Оборона падает медленнее (-1/ход vs -3/ход)\n"
            "  ✅ +5 доп. обороны при укреплении\n"
            "  ✅ Начинает с высокой обороной (50) и моралью (75)\n\n"
            "*Слабые стороны:*\n"
            "  ❌ Нет экономических бонусов\n"
            "  ❌ Стандартный запас еды и хлама\n\n"
            "*Пассивка:* _Укреплён_ — стены стоят там, где у других рушатся.\n"
            "*Лучше всего для:* Игроков, предпочитающих безопасность."
        ),
    },
    "class_info_trader": {
        "en": (
            "💰 *Trader — Caravan Boss*\n\n"
            "*Strengths:*\n"
            "  ✅ +10 extra food from every trade\n"
            "  ✅ Trade costs less scrap (10 vs 15)\n"
            "  ✅ Starts with Trader Guild rep +15\n"
            "  ✅ Starts with extra food (120)\n\n"
            "*Weaknesses:*\n"
            "  ❌ Starts with less scrap (90 vs 80)\n"
            "  ❌ No combat or exploration bonuses\n\n"
            "*Passive:* _Connected_ — the caravans know your name.\n"
            "*Best for:* Players who want a strong economy."
        ),
        "ru": (
            "💰 *Торговец — Глава каравана*\n\n"
            "*Сильные стороны:*\n"
            "  ✅ +10 доп. еды за каждую сделку\n"
            "  ✅ Торговля стоит меньше хлама (10 vs 15)\n"
            "  ✅ Начинает с репутацией Гильдии Торговцев +15\n"
            "  ✅ Начинает с доп. едой (120)\n\n"
            "*Слабые стороны:*\n"
            "  ❌ Начинает с меньшим хламом (90 vs 80)\n"
            "  ❌ Нет боевых или разведывательных бонусов\n\n"
            "*Пассивка:* _Связи_ — караваны знают твоё имя.\n"
            "*Лучше всего для:* Игроков, строящих сильную экономику."
        ),
    },
    "class_info_diplomat": {
        "en": (
            "🕊 *Diplomat — Smooth Talker*\n\n"
            "*Strengths:*\n"
            "  ✅ Diplomacy costs half the food (5 vs 10)\n"
            "  ✅ +50% faction reputation gains\n"
            "  ✅ +3 extra morale from diplomacy\n"
            "  ✅ Starts with high morale (80) and pop (55)\n\n"
            "*Weaknesses:*\n"
            "  ❌ No combat or scrap bonuses\n"
            "  ❌ Default starting food and defense\n\n"
            "*Passive:* _Silver Tongue_ — words are your sharpest weapon.\n"
            "*Best for:* Players who want to ally with factions fast."
        ),
        "ru": (
            "🕊 *Дипломат — Мастер переговоров*\n\n"
            "*Сильные стороны:*\n"
            "  ✅ Дипломатия стоит вдвое меньше еды (5 vs 10)\n"
            "  ✅ +50% к росту репутации фракций\n"
            "  ✅ +3 доп. морали от дипломатии\n"
            "  ✅ Начинает с высокой моралью (80) и населением (55)\n\n"
            "*Слабые стороны:*\n"
            "  ❌ Нет боевых и ресурсных бонусов\n"
            "  ❌ Стандартный запас еды и обороны\n\n"
            "*Пассивка:* _Серебряный язык_ — слова — твоё острейшее оружие.\n"
            "*Лучше всего для:* Игроков, желающих быстро подружиться с фракциями."
        ),
    },
    "class_info_medic": {
        "en": (
            "💊 *Medic — Field Surgeon*\n\n"
            "*Strengths:*\n"
            "  ✅ Survives 3 starvation turns (vs 2 for others)\n"
            "  ✅ -1 population loss from dangerous events\n"
            "  ✅ +5 morale and +3 food from resting\n"
            "  ✅ Starts with extra pop (60) and food (110)\n\n"
            "*Weaknesses:*\n"
            "  ❌ No scrap, defense, or trade bonuses\n"
            "  ❌ Default starting defense and morale\n\n"
            "*Passive:* _Triage_ — your people die less. Period.\n"
            "*Best for:* Players who want to keep their settlement alive."
        ),
        "ru": (
            "💊 *Медик — Полевой хирург*\n\n"
            "*Сильные стороны:*\n"
            "  ✅ Выживает 3 хода голода (vs 2 у остальных)\n"
            "  ✅ -1 потеря населения от опасных событий\n"
            "  ✅ +5 морали и +3 еды от отдыха\n"
            "  ✅ Начинает с доп. населением (60) и едой (110)\n\n"
            "*Слабые стороны:*\n"
            "  ❌ Нет бонусов к хламу, обороне или торговле\n"
            "  ❌ Стандартная оборона и мораль\n\n"
            "*Пассивка:* _Сортировка_ — твои люди умирают реже. Точка.\n"
            "*Лучше всего для:* Игроков, которые хотят сохранить поселение живым."
        ),
    },
    "class_info_back": {
        "en": "↩️ Back to class selection",
        "ru": "↩️ Назад к выбору класса",
    },
    "settlement_default_name": {
        "en": "{name}'s Haven",
        "ru": "Убежище {name}",
    },
    # --- Status ---
    "status_header": {
        "en": "--- *{settlement}* --- Week {turn} ---",
        "ru": "--- *{settlement}* --- Неделя {turn} ---",
    },
    "status_header_rpg": {
        "en": "--- *{settlement}* --- Week {turn} ---",
        "ru": "--- *{settlement}* --- Неделя {turn} ---",
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
            "You've used all {max_turns} free turns for today.\n"
            "Free turns reset at midnight UTC — come back tomorrow.\n\n"
            "⭐ *Premium* — unlimited turns + richer AI narration\n"
            "{price} Stars for 30 days. Tap the button below to pay with Telegram Stars."
        ),
        "ru": (
            "Вы использовали все {max_turns} бесплатных хода за сегодня.\n"
            "Ходы обновятся в полночь UTC — возвращайтесь завтра.\n\n"
            "⭐ *Премиум* — безлимитные ходы + расширенное повествование ИИ\n"
            "{price} звёзд на 30 дней. Нажмите кнопку ниже, чтобы оплатить звёздами Telegram."
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
            "*Wasteland Chronicles* -- Post-Apocalyptic RPG\n\n"
            "*Commands:*\n"
            "/start -- Begin or resume your game\n"
            "/status -- View settlement status\n"
            "/newgame -- Start a new game (abandons current)\n"
            "/help -- Show this help\n\n"
            "*Actions (type in chat):*\n"
            "Build -- Construct buildings (costs scrap)\n"
            "Explore -- Scavenge for scrap and gold (risky)\n"
            "Trade -- Exchange scrap for food and gold\n"
            "Defend -- Fortify your settlement\n"
            "Diplomacy -- Improve faction relations\n"
            "Rest -- Recover morale\n\n"
            "*Resources:*\n"
            "Population -- Your settlers (0 = defeat)\n"
            "Food -- Consumed each turn (0 for 2+ turns = defeat)\n"
            "Scrap -- Building material\n"
            "Gold -- Premium currency for special purchases\n"
            "Morale -- Affects population growth (0-100)\n"
            "Defense -- Protection from attacks (0-100)\n\n"
            "*Progression:*\n"
            "Earn XP each turn to level up. Higher levels unlock new\n"
            "buildings, harder zones, and skill points.\n\n"
            "*Lose:* Population hits 0, or food stays at 0 for 2+ turns\n\n"
            "You get {max_turns} turns/day. Premium = unlimited."
        ),
        "ru": (
            "*Хроники Пустоши* -- Постапокалиптическая RPG\n\n"
            "*Команды:*\n"
            "/start -- Начать или продолжить игру\n"
            "/status -- Посмотреть статус поселения\n"
            "/newgame -- Начать новую игру (текущая будет брошена)\n"
            "/help -- Показать справку\n\n"
            "*Действия (пишите в чат):*\n"
            "Строить -- Возводить постройки (стоит хлам)\n"
            "Разведка -- Искать хлам и золото (рискованно)\n"
            "Торговля -- Менять хлам на еду и золото\n"
            "Оборона -- Укреплять поселение\n"
            "Дипломатия -- Улучшать отношения с фракциями\n"
            "Отдых -- Восстановить мораль\n\n"
            "*Ресурсы:*\n"
            "Население -- Ваши поселенцы (0 = поражение)\n"
            "Еда -- Расходуется каждый ход (0 два хода = поражение)\n"
            "Хлам -- Стройматериал\n"
            "Золото -- Валюта для особых покупок\n"
            "Мораль -- Влияет на рост населения (0-100)\n"
            "Оборона -- Защита от атак (0-100)\n\n"
            "*Прогресс:*\n"
            "Получайте XP каждый ход для повышения уровня. Выше уровень =\n"
            "новые постройки, сложные зоны, очки навыков.\n\n"
            "*Поражение:* Население = 0, или еда = 0 два хода подряд\n\n"
            "У вас {max_turns} ходов/день. Премиум = безлимит."
        ),
    },
    # --- Onboarding tutorial ---
    "onboarding_guide": {
        "en": (
            "*— The Navigator, back on the line: —*\n\n"
            "\"Good. You can hear me. That's a start.\n\n"
            "Just talk to me — plain language, no commands needed. "
            "Ask questions, give orders, think out loud. I'll understand.\"\n\n"
            "*Try saying something like:*\n"
            "  · _\"where exactly are we?\"_\n"
            "  · _\"what do you know about the raiders nearby?\"_\n"
            "  · _\"I want to build a farm\"_\n"
            "  · _\"send scouts to explore the ruins\"_\n"
            "  · _\"open negotiations with the Trader Guild\"_\n"
            "  · _\"let everyone rest this week\"_\n\n"
            "There is no time limit — grow as far as you can. "
            "Earn XP, level up, unlock new buildings and zones. "
            "Run out of food for two weeks, or lose everyone — and it's over.\n\n"
            "Press 📊 Status anytime. Now — what do you want to do first?"
        ),
        "ru": (
            "*— Навигатор снова в эфире: —*\n\n"
            "\"Хорошо. Слышишь меня. Уже что-то.\n\n"
            "Просто говори — обычным языком, никаких команд не надо. "
            "Задавай вопросы, отдавай приказы, думай вслух. Я пойму.\"\n\n"
            "*Попробуй написать что-нибудь вроде:*\n"
            "  · _«где именно мы находимся?»_\n"
            "  · _«что знаешь про рейдеров поблизости?»_\n"
            "  · _«хочу построить ферму»_\n"
            "  · _«разведчиков — в руины»_\n"
            "  · _«начать переговоры с Торговой Гильдией»_\n"
            "  · _«дать всем отдохнуть на этой неделе»_\n\n"
            "Времени нет — расти, пока можешь. "
            "Зарабатывай XP, повышай уровень, открывай новые постройки и зоны. "
            "Голод два хода или нет людей — конец.\n\n"
            "Нажми 📊 Статус в любой момент. Ну — что делаем первым делом?"
        ),
    },
    # --- Free text parsing ---
    "free_text_no_narrator": {
        "en": "I didn't catch that. Try: explore, build a farm, trade, defend, rest, or negotiate with raiders/traders/remnants.",
        "ru": "Не понял. Попробуй: разведка, построить ферму, торговля, оборона, отдых, переговоры с рейдерами/торговцами/остатками.",
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
    # --- Skills ---
    "skills_header": {
        "en": "🔮 *Skills* — {points} point(s) available",
        "ru": "🔮 *Навыки* — {points} очков доступно",
    },
    "skill_learned": {
        "en": "✅ *{skill}* upgraded to rank {rank} (effect: +{effect}). {remaining} point(s) remaining.",
        "ru": "✅ *{skill}* улучшен до ранга {rank} (эффект: +{effect}). Осталось {remaining} очков.",
    },
    "skill_cannot_learn": {
        "en": "Cannot learn skill: {reason}",
        "ru": "Невозможно изучить навык: {reason}",
    },
    "skills_no_points": {
        "en": "You have no skill points. Earn more by leveling up (1 point every 5 levels).",
        "ru": "У вас нет очков навыков. Получайте их за повышение уровня (1 очко каждые 5 уровней).",
    },
    # --- Shop ---
    "shop_header": {
        "en": "🏪 *Shop* — You have {gold} 💰 gold",
        "ru": "🏪 *Магазин* — У вас {gold} 💰 золота",
    },
    "shop_purchased": {
        "en": "✅ Purchased *{item}* for {cost} 💰. Remaining gold: {gold}.",
        "ru": "✅ Куплено *{item}* за {cost} 💰. Осталось золота: {gold}.",
    },
    "shop_not_enough_gold": {
        "en": "Not enough gold. Need {cost} 💰, you have {gold} 💰.",
        "ru": "Недостаточно золота. Нужно {cost} 💰, у вас {gold} 💰.",
    },
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

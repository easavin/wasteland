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
    "display_name_prompt": {
        "en": (
            "Choose your display name — how other survivors will see you.\n\n"
            "Type it now (2–40 characters):"
        ),
        "ru": (
            "Выбери отображаемое имя — как тебя будут видеть другие выжившие.\n\n"
            "Напиши его сейчас (2–40 символов):"
        ),
    },
    "display_name_length": {
        "en": "Name must be 2–40 characters. Try again:",
        "ru": "Имя должно быть от 2 до 40 символов. Попробуй снова:",
    },
    "display_name_rejected": {
        "en": "That name isn't allowed. Try another (2–40 chars):",
        "ru": "Это имя нельзя использовать. Попробуй другое (2–40 символов):",
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
            "/npc -- Play minigames with NPCs\n"
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
            "/npc -- Мини-игры с NPC\n"
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
    # --- Quick onboarding (first steps) ---
    "quick_onboarding": {
        "en": (
            "🚀 *Quick start — try these first:*\n"
            "• {class_tip}\n"
            "• Build a farm — food runs out fast\n"
            "• Say _rest_ when morale is low\n"
            "• /chat — talk to other survivors in your world"
        ),
        "ru": (
            "🚀 *Быстрый старт — попробуй первым:*\n"
            "• {class_tip}\n"
            "• Построй ферму — еда быстро кончается\n"
            "• Напиши _отдых_ когда мораль низкая\n"
            "• /chat — общайся с другими выжившими"
        ),
    },
    "quick_tip_scavenger": {
        "en": "Explore the ruins — you find bonus scrap",
        "ru": "Исследуй руины — ты найдёшь больше хлама",
    },
    "quick_tip_warden": {
        "en": "Fortify defenses — say _defend_ to strengthen walls",
        "ru": "Укрепи оборону — напиши _оборона_ для стен",
    },
    "quick_tip_trader": {
        "en": "Trade scrap for food — you get better deals",
        "ru": "Меняй хлам на еду — у тебя лучшие условия",
    },
    "quick_tip_diplomat": {
        "en": "Open diplomacy with a faction — raiders, traders, or remnants",
        "ru": "Начни дипломатию с фракцией — рейдеры, торговцы или остатки",
    },
    "quick_tip_medic": {
        "en": "Let people rest — you recover more morale and food",
        "ru": "Дай людям отдохнуть — ты восстанавливаешь больше морали и еды",
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
    # --- Chat ---
    "chat_no_world": {"en": "You're not in a shared world.", "ru": "Вы не в общем мире."},
    "quest_list_header": {"en": "📜 *NPCs in your zone*", "ru": "📜 *NPC в вашей зоне*"},
    "quest_no_npcs": {"en": "No NPCs in your zone yet.", "ru": "В вашей зоне пока нет NPC."},
    "quest_npc_not_found": {"en": "NPC not found.", "ru": "NPC не найден."},
    "quest_npc_no_quests": {"en": "{name} has no quests available.", "ru": "У {name} нет квестов."},
    "quest_npc_header": {"en": "📜 *{name}* — Available quests:", "ru": "📜 *{name}* — Доступные квесты:"},
    "quest_completed": {"en": "Completed", "ru": "Выполнено"},
    "quest_active": {"en": "In progress", "ru": "В процессе"},
    "quest_accept_usage": {"en": "Usage: /quest accept <quest_key> <npc_name>", "ru": "Использование: /quest accept <ключ> <имя_npc>"},
    "quest_not_found": {"en": "Quest not found.", "ru": "Квест не найден."},
    "quest_accepted": {"en": "Quest *{name}* accepted!", "ru": "Квест *{name}* принят!"},
    "quest_already_active": {"en": "You already have this quest.", "ru": "У вас уже есть этот квест."},
    "chat_rate_limit": {"en": "Slow down. Wait a few seconds.", "ru": "Подождите несколько секунд."},
    "chat_empty": {"en": "Type a message after the command.", "ru": "Напишите сообщение после команды."},
    "chat_sent": {"en": "Sent to {count} survivor(s).", "ru": "Отправлено {count} выживш(им/им)."},
    "chat_no_guild": {"en": "You're not in a guild. Use /guild create or /guild accept.", "ru": "Вы не в гильдии."},
    "chat_log_empty": {"en": "No messages yet.", "ru": "Пока нет сообщений."},
    "whisper_usage": {"en": "Usage: /whisper @username message", "ru": "Использование: /whisper @username сообщение"},
    "whisper_not_found": {"en": "Player not found.", "ru": "Игрок не найден."},
    "whisper_npc": {"en": "NPCs cannot receive whispers.", "ru": "NPC не получают личные сообщения."},
    "whisper_no_game": {"en": "That player has no active game.", "ru": "У этого игрока нет активной игры."},
    "whisper_sent": {"en": "Whisper sent.", "ru": "Шёпот отправлен."},
    "whisper_failed": {"en": "Could not send whisper.", "ru": "Не удалось отправить."},
    # --- Guilds ---
    "guild_help": {"en": "Usage: /guild create <name>, /guild invite @user, /guild accept, /guild leave, /guild roster, /guild info", "ru": "Использование: /guild create <имя>, /guild invite @user, /guild accept, /guild leave, /guild roster, /guild info"},
    "guild_already_in": {"en": "You're already in a guild.", "ru": "Вы уже в гильдии."},
    "guild_name_invalid": {"en": "Guild name: 2–30 chars, letters, numbers, spaces, hyphens.", "ru": "Имя гильдии: 2–30 символов."},
    "guild_name_taken": {"en": "That name is taken.", "ru": "Это имя занято."},
    "guild_created": {"en": "Guild *{name}* created!", "ru": "Гильдия *{name}* создана!"},
    "guild_not_officer": {"en": "Only leaders and officers can invite.", "ru": "Приглашать могут только лидеры и офицеры."},
    "guild_invite_not_found": {"en": "Player not found.", "ru": "Игрок не найден."},
    "guild_invite_npc": {"en": "Cannot invite NPCs to guilds.", "ru": "Нельзя пригласить NPC в гильдию."},
    "guild_invite_no_game": {"en": "That player has no active game.", "ru": "У игрока нет активной игры."},
    "guild_invite_wrong_world": {"en": "That player is in a different world.", "ru": "Игрок в другом мире."},
    "guild_invite_already_in": {"en": "They're already in a guild.", "ru": "Они уже в гильдии."},
    "guild_invite_sent": {"en": "Invite sent.", "ru": "Приглашение отправлено."},
    "guild_invite_received": {"en": "**{inviter}** invited you to guild *{guild}*. Use /guild accept or /guild decline.", "ru": "**{inviter}** пригласил вас в гильдию *{guild}*. /guild accept или /guild decline."},
    "guild_accept_btn": {"en": "Accept", "ru": "Принять"},
    "guild_decline_btn": {"en": "Decline", "ru": "Отклонить"},
    "guild_no_invite": {"en": "No pending invite.", "ru": "Нет приглашения."},
    "guild_joined": {"en": "Joined *{name}*!", "ru": "Вступили в *{name}*!"},
    "guild_invite_expired": {"en": "Invite expired.", "ru": "Приглашение истекло."},
    "guild_declined": {"en": "Invite declined.", "ru": "Приглашение отклонено."},
    "guild_left": {"en": "Left the guild.", "ru": "Вы вышли из гильдии."},
    "guild_leader_transfer": {"en": "As leader, transfer leadership or disband first.", "ru": "Передайте лидерство или распустите гильдию."},
    "guild_info": {"en": "*{name}* — Leader: {leader}, Members: {count}", "ru": "*{name}* — Лидер: {leader}, Участников: {count}"},
    # --- Trade / Market ---
    "market_empty": {"en": "Marketplace is empty.", "ru": "Рынок пуст."},
    "market_list_header": {"en": "📦 *Marketplace* (buy: /market buy <id>)", "ru": "📦 *Рынок* (купить: /market buy <id>)"},
    "market_sell_usage": {"en": "Usage: /market sell <food|scrap> <amount> <price_in_gold>", "ru": "Использование: /market sell <еда|хлам> <кол-во> <цена_в_золоте>"},
    "market_invalid_resource": {"en": "Use food or scrap.", "ru": "Используйте food или scrap."},
    "market_invalid_numbers": {"en": "Invalid amount or price.", "ru": "Неверное количество или цена."},
    "market_insufficient": {"en": "Not enough {resource}. You have {have}.", "ru": "Недостаточно {resource}. У вас {have}."},
    "market_sold": {"en": "Posted {amount} {resource} for {price} 💰 (id: {id})", "ru": "Выставлено {amount} {resource} за {price} 💰"},
    "market_buy_usage": {"en": "Usage: /market buy <offer_id>", "ru": "Использование: /market buy <id>"},
    "market_bought": {"en": "Bought {amount} {resource} for {price} 💰!", "ru": "Купили {amount} {resource} за {price} 💰!"},
    "market_offer_gone": {"en": "Offer not found or sold.", "ru": "Предложение не найдено или продано."},
    "market_no_gold": {"en": "Not enough gold.", "ru": "Недостаточно золота."},
    "market_seller_empty": {"en": "Seller no longer has the resources.", "ru": "У продавца больше нет ресурсов."},
    "market_not_yours": {"en": "That offer is for someone else.", "ru": "Это предложение для другого."},
    "market_error": {"en": "Trade failed.", "ru": "Сделка не удалась."},
    "market_cancel_usage": {"en": "Usage: /market cancel <offer_id>", "ru": "Использование: /market cancel <id>"},
    "market_cancelled": {"en": "Offer cancelled.", "ru": "Предложение отменено."},
    "market_cancel_failed": {"en": "Could not cancel. Is it yours?", "ru": "Не удалось отменить."},
    "trade_direct_usage": {"en": "Usage: /trade @username <resource> <amount> <price>", "ru": "Использование: /trade @username <ресурс> <кол-во> <цена>"},
    "trade_accept_usage": {"en": "Usage: /trade accept <offer_id>", "ru": "Использование: /trade accept <id>"},
    "trade_target_not_found": {"en": "Player not found.", "ru": "Игрок не найден."},
    "trade_target_npc": {"en": "You cannot send direct trade offers to NPCs.", "ru": "Нельзя отправлять предложения NPC."},
    "trade_target_no_game": {"en": "That player has no active game.", "ru": "У игрока нет активной игры."},
    "trade_same_world": {"en": "That player is in a different world.", "ru": "Игрок в другом мире."},
    "trade_offer_received": {"en": "**{seller}** offers {amount} {resource} for {price} 💰. /trade accept {id}", "ru": "**{seller}** предлагает {amount} {resource} за {price} 💰. /trade accept {id}"},
    "trade_offer_sent": {"en": "Trade offer sent.", "ru": "Предложение отправлено."},
    # --- Combat ---
    "challenge_usage": {"en": "Usage: /challenge @username [siege|raid]", "ru": "Использование: /challenge @username [siege|raid]"},
    "challenge_not_found": {"en": "Player not found.", "ru": "Игрок не найден."},
    "challenge_npc": {"en": "You cannot challenge NPCs.", "ru": "Нельзя вызвать NPC на бой."},
    "challenge_no_game": {"en": "That player has no active game.", "ru": "У игрока нет активной игры."},
    "challenge_self": {"en": "You can't challenge yourself.", "ru": "Нельзя вызвать себя."},
    "challenge_wrong_world": {"en": "That player is in a different world.", "ru": "Игрок в другом мире."},
    "challenge_sent": {"en": "Challenge sent to {target}.", "ru": "Вызов отправлен {target}."},
    "challenge_received": {"en": "**{challenger}** challenges you to a {ctype}! Use the buttons or /challenge accept / /challenge decline.", "ru": "**{challenger}** вызывает вас на {ctype}! Кнопки или /challenge accept / /challenge decline."},
    "challenge_accept_btn": {"en": "Accept", "ru": "Принять"},
    "challenge_decline_btn": {"en": "Decline", "ru": "Отклонить"},
    "challenge_expired": {"en": "Challenge expired.", "ru": "Вызов истёк."},
    "challenge_declined": {"en": "Challenge declined.", "ru": "Вызов отклонён."},
    "challenge_none_pending": {"en": "No pending challenge.", "ru": "Нет ожидающих вызовов."},
    "challenge_result": {"en": "⚔️ Battle over! *{winner}* defeated *{loser}*.", "ru": "⚔️ Бой окончен! *{winner}* победил *{loser}*."},
    # --- Display name ---
    "name_updated": {"en": "Display name updated to *{name}*.", "ru": "Имя изменено на *{name}*."},
    "name_rate_limit": {"en": "You can change your name once per day.", "ru": "Имя можно менять раз в день."},

    # ── NPC Minigames (general) ──
    "npc_no_npcs": {"en": "No NPCs nearby.", "ru": "Поблизости нет NPC."},
    "npc_no_games": {"en": "No minigames available here.", "ru": "Здесь нет мини-игр."},
    "npc_not_found": {"en": "That NPC isn't around here.", "ru": "Этого NPC здесь нет."},
    "npc_game_expired": {"en": "That game session has expired. Start a new one with /npc.", "ru": "Сессия игры истекла. Начните новую через /npc."},
    "npc_cooldown": {
        "en": "They're busy. Come back in {mins}m {secs}s.",
        "ru": "Они заняты. Возвращайтесь через {mins}м {secs}с.",
    },
    "npc_games_header": {
        "en": (
            "🎮 *NPC Encounters*\n\n"
            "Play a minigame with a local NPC to earn rewards.\n"
            "Choose who to visit:"
        ),
        "ru": (
            "🎮 *Встречи с NPC*\n\n"
            "Сыграйте в мини-игру с местным NPC и получите награды.\n"
            "Выберите, к кому пойти:"
        ),
    },
    "npc_game_name_scrap_roulette": {"en": "Scrap Roulette", "ru": "Хлам-Рулетка"},
    "npc_game_name_field_triage": {"en": "Field Triage", "ru": "Полевая Сортировка"},
    "npc_game_name_perimeter_breach": {"en": "Perimeter Breach", "ru": "Прорыв Периметра"},

    # ── Scrap Roulette (Old Trader) ──
    "roulette_no_scrap": {
        "en": "Old Trader squints at you. \"No scrap, no game. You need {cost} 🔩, got {have}.\"",
        "ru": "Старый Торговец щурится. \"Нет хлама — нет игры. Нужно {cost} 🔩, у тебя {have}.\"",
    },
    "roulette_intro": {
        "en": (
            "🏪 *Old Trader's Scrap Roulette*\n\n"
            "The trader slaps three dusty crates on the counter.\n\n"
            "\"Pick one. Could be treasure, could be trash. "
            "Costs you {cost} 🔩 scrap to play.\"\n\n"
            "Choose a crate:"
        ),
        "ru": (
            "🏪 *Хлам-Рулетка Старого Торговца*\n\n"
            "Торговец шлёпает три пыльных ящика на прилавок.\n\n"
            "\"Выбирай. Может сокровище, может мусор. "
            "Стоит {cost} 🔩 хлама.\"\n\n"
            "Выберите ящик:"
        ),
    },
    "roulette_crate_jackpot": {"en": "Jackpot! Pre-war tech cache", "ru": "Джекпот! Довоенный тайник"},
    "roulette_crate_good": {"en": "Nice find — tools & rations", "ru": "Неплохо — инструменты и пайки"},
    "roulette_crate_decent": {"en": "Decent — some useful parts", "ru": "Сойдёт — полезные запчасти"},
    "roulette_crate_junk": {"en": "Junk — rusty screws", "ru": "Мусор — ржавые гвозди"},
    "roulette_crate_trap": {"en": "Booby-trapped! Explosion!", "ru": "Заминировано! Взрыв!"},
    "roulette_crate_empty": {"en": "Empty — nothing but dust", "ru": "Пусто — одна пыль"},
    "roulette_nothing": {"en": "nothing gained, nothing lost", "ru": "ни выигрыша, ни потерь"},
    "roulette_result": {
        "en": (
            "🏪 You picked crate *{picked}* — {emoji} *{content}*\n\n"
            "All crates revealed:\n{reveal}\n\n"
            "📊 {deltas}"
        ),
        "ru": (
            "🏪 Вы выбрали ящик *{picked}* — {emoji} *{content}*\n\n"
            "Все ящики:\n{reveal}\n\n"
            "📊 {deltas}"
        ),
    },

    # ── Field Triage (Doc) ──
    "triage_intro": {
        "en": (
            "💊 *Doc's Field Triage*\n\n"
            "Doc wipes blood off her hands. \"Got {rounds} patients. "
            "Help me diagnose them — right call saves lives, wrong one... doesn't.\"\n\n"
            "Get ready."
        ),
        "ru": (
            "💊 *Полевая Сортировка Дока*\n\n"
            "Док вытирает кровь с рук. \"{rounds} пациента ждут. "
            "Помоги поставить диагноз — правильный ответ спасёт жизни, неправильный... нет.\"\n\n"
            "Приготовьтесь."
        ),
    },
    "triage_patient": {
        "en": "💊 *Patient {round}/{total}*\n\n{symptom}\n\nChoose treatment:",
        "ru": "💊 *Пациент {round}/{total}*\n\n{symptom}\n\nВыберите лечение:",
    },
    "triage_case_radiation": {
        "en": "Patient shows hair loss, bleeding gums, severe fatigue. Geiger counter is clicking.",
        "ru": "Выпадение волос, кровоточащие дёсны, сильная усталость. Счётчик Гейгера трещит.",
    },
    "triage_case_broken_leg": {
        "en": "Survivor dragged in with a twisted, swollen leg. Can't put weight on it. Bone visible through skin.",
        "ru": "Выжившего притащили с опухшей ногой. Не может встать. Кость видна сквозь кожу.",
    },
    "triage_case_fever": {
        "en": "High fever, chills, infected wound on the arm. Red streaks spreading from the cut.",
        "ru": "Высокая температура, озноб, инфицированная рана на руке. Красные полосы от пореза.",
    },
    "triage_case_wound": {
        "en": "Deep gash across the torso, won't stop bleeding. Patient is pale and fading.",
        "ru": "Глубокая рана на торсе, кровь не останавливается. Пациент бледнеет.",
    },
    "triage_case_toxin": {
        "en": "Vomiting, confusion, dilated pupils. Ate something from the old district.",
        "ru": "Рвота, спутанность сознания, расширенные зрачки. Съел что-то из старого района.",
    },
    "triage_case_dehydration": {
        "en": "Cracked lips, sunken eyes, hasn't had water in days. Barely conscious.",
        "ru": "Потрескавшиеся губы, запавшие глаза, без воды несколько дней. Еле в сознании.",
    },
    "triage_opt_radaway": {"en": "💉 Anti-radiation meds", "ru": "💉 Антирадиационные препараты"},
    "triage_opt_bandage": {"en": "🩹 Bandage and rest", "ru": "🩹 Перевязка и отдых"},
    "triage_opt_rest": {"en": "😴 Just let them sleep", "ru": "😴 Пусть поспит"},
    "triage_opt_splint": {"en": "🦴 Set the bone and splint", "ru": "🦴 Вправить и наложить шину"},
    "triage_opt_herbs": {"en": "🌿 Herbal poultice", "ru": "🌿 Травяной компресс"},
    "triage_opt_amputation": {"en": "🪚 Amputate", "ru": "🪚 Ампутировать"},
    "triage_opt_antibiotics": {"en": "💊 Antibiotics", "ru": "💊 Антибиотики"},
    "triage_opt_cold_water": {"en": "💧 Cold water compress", "ru": "💧 Холодный компресс"},
    "triage_opt_ignore": {"en": "🤷 Ignore it, they'll be fine", "ru": "🤷 Само пройдёт"},
    "triage_opt_stitch": {"en": "🪡 Stitch the wound shut", "ru": "🪡 Зашить рану"},
    "triage_opt_cauterize": {"en": "🔥 Cauterize with hot metal", "ru": "🔥 Прижечь раскалённым металлом"},
    "triage_opt_prayer": {"en": "🙏 Pray for the best", "ru": "🙏 Молиться"},
    "triage_opt_charcoal": {"en": "⬛ Activated charcoal", "ru": "⬛ Активированный уголь"},
    "triage_opt_whiskey": {"en": "🥃 Old world whiskey (it's medicine, right?)", "ru": "🥃 Старый виски (это же лекарство?)"},
    "triage_opt_sleep": {"en": "😴 Sleep it off", "ru": "😴 Проспаться"},
    "triage_opt_clean_water": {"en": "💧 Clean water, slowly", "ru": "💧 Чистая вода, понемногу"},
    "triage_opt_stimpak": {"en": "💉 Stimpak injection", "ru": "💉 Укол стимулятора"},
    "triage_opt_food": {"en": "🍖 Give them food", "ru": "🍖 Дать еды"},
    "triage_correct": {"en": "✅ *Correct!* Doc nods approvingly.", "ru": "✅ *Верно!* Док одобрительно кивает."},
    "triage_wrong": {
        "en": "❌ *Wrong.* Doc sighs. \"Should've gone with {correct}.\"",
        "ru": "❌ *Неверно.* Док вздыхает. \"Надо было — {correct}.\"",
    },
    "triage_result": {
        "en": (
            "💊 *Triage Complete!*\n\n"
            "Score: *{score}/{total}*\n"
            "👥 +{pop} population | 😊 {morale:+d} morale"
        ),
        "ru": (
            "💊 *Сортировка окончена!*\n\n"
            "Результат: *{score}/{total}*\n"
            "👥 +{pop} населения | 😊 {morale:+d} морали"
        ),
    },

    # ── Perimeter Breach (Sentry) ──
    "breach_intro": {
        "en": (
            "🎯 *Sentry's Perimeter Breach*\n\n"
            "Sentry hands you binoculars. \"Movement on {rounds} sectors. "
            "I need snap decisions — shoot, negotiate, or take cover. "
            "Wrong call costs lives.\"\n\n"
            "Scanning perimeter..."
        ),
        "ru": (
            "🎯 *Прорыв Периметра Часового*\n\n"
            "Часовой протягивает бинокль. \"Движение на {rounds} секторах. "
            "Мне нужны быстрые решения — стрелять, договариваться или укрыться. "
            "Неправильный ответ стоит жизней.\"\n\n"
            "Сканирую периметр..."
        ),
    },
    "breach_alert": {
        "en": "🚨 *Sector {sector} — Alert {round}/{total}*\n\n{threat}\n\nYour call:",
        "ru": "🚨 *Сектор {sector} — Тревога {round}/{total}*\n\n{threat}\n\nВаше решение:",
    },
    "breach_threat_raiders": {
        "en": "Armed raiders approaching fast. Weapons drawn, no flag of truce.",
        "ru": "Вооружённые рейдеры приближаются. Оружие наготове, белого флага нет.",
    },
    "breach_threat_mutants": {
        "en": "Pack of irradiated mutant hounds. Teeth bared, moving in formation.",
        "ru": "Стая облучённых мутантов. Оскалены, движутся строем.",
    },
    "breach_threat_traders": {
        "en": "Caravan with white flags. Loaded wagons, guards relaxed.",
        "ru": "Караван с белыми флагами. Нагруженные повозки, охрана расслаблена.",
    },
    "breach_threat_refugees": {
        "en": "Ragged group of civilians. Women and children. Waving for help.",
        "ru": "Оборванная группа гражданских. Женщины и дети. Машут, просят о помощи.",
    },
    "breach_threat_sandstorm": {
        "en": "Massive dust wall on the horizon. Moving fast. Sky turning brown.",
        "ru": "Огромная стена пыли на горизонте. Движется быстро. Небо темнеет.",
    },
    "breach_threat_drones": {
        "en": "Pre-war automated drones. Red targeting lasers sweeping the ground.",
        "ru": "Довоенные дроны. Красные лазеры прицеливания сканируют землю.",
    },
    "breach_threat_scavengers": {
        "en": "Lone scavengers poking around the perimeter. Look nervous, not hostile.",
        "ru": "Одинокие старатели бродят у периметра. Выглядят нервно, не враждебно.",
    },
    "breach_threat_radstorm": {
        "en": "Green glow on the horizon. Radiation storm incoming. Geiger's screaming.",
        "ru": "Зелёное свечение на горизонте. Радиационный шторм. Счётчик зашкаливает.",
    },
    "breach_opt_shoot": {"en": "Open fire", "ru": "Открыть огонь"},
    "breach_opt_negotiate": {"en": "Talk to them", "ru": "Переговоры"},
    "breach_opt_hide": {"en": "Take cover", "ru": "В укрытие"},
    "breach_opt_trap": {"en": "Set a trap", "ru": "Поставить ловушку"},
    "breach_opt_run": {"en": "Fall back", "ru": "Отступить"},
    "breach_correct": {"en": "✅ *Good call!* Sentry nods. \"You've got instincts.\"", "ru": "✅ *Верное решение!* Часовой кивает. \"У тебя чутьё.\""},
    "breach_wrong": {
        "en": "❌ *Bad call.* Sentry winces. \"Should've gone with: {correct}.\"",
        "ru": "❌ *Плохой выбор.* Часовой морщится. \"Надо было: {correct}.\"",
    },
    "breach_result": {
        "en": (
            "🎯 *Perimeter Secured!*\n\n"
            "Score: *{score}/{total}*\n"
            "🛡 {defense:+d} defense | 😊 +{morale} morale | 👥 {pop:+d} population"
        ),
        "ru": (
            "🎯 *Периметр защищён!*\n\n"
            "Результат: *{score}/{total}*\n"
            "🛡 {defense:+d} оборона | 😊 +{morale} мораль | 👥 {pop:+d} население"
        ),
    },
    "breach_result_no_reward": {
        "en": "🎯 Drill complete, but your game session expired.",
        "ru": "🎯 Учения окончены, но ваша сессия истекла.",
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

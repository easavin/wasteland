"""Wasteland Codex — 60 discoverable lore entries across 5 categories.

Each entry has bilingual name/lore, a rarity tier, and a minimum zone requirement.
Discovery is probabilistic and can be triggered during gameplay events.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

CATEGORIES: list[str] = ["creatures", "locations", "tech", "history", "factions"]

CATEGORY_EMOJI: dict[str, str] = {
    "creatures": "\U0001f43e",   # paw prints
    "locations": "\U0001f5fa",   # world map
    "tech":      "\u2699\ufe0f", # gear
    "history":   "\U0001f4dc",   # scroll
    "factions":  "\u2694\ufe0f", # crossed swords
}


def get_categories() -> list[str]:
    """Return the ordered list of codex categories."""
    return list(CATEGORIES)


def get_category_emoji(category: str) -> str:
    """Return the emoji for a codex category."""
    return CATEGORY_EMOJI.get(category, "📖")


# ---------------------------------------------------------------------------
# Entry catalog — 60 entries (12 per category)
# ---------------------------------------------------------------------------

CODEX_ENTRIES: dict[str, dict] = {
    # ======================================================================
    # CREATURES (12)
    # ======================================================================
    "irradiated_hound": {
        "category": "creatures",
        "name": {"en": "Irradiated Hound", "ru": "Облучённый пёс"},
        "lore": {
            "en": "Once loyal pets, these dogs were twisted by decades of radiation into hairless, glowing predators. They hunt in packs of six to twelve, communicating through eerie subsonic howls that carry for miles across the wasteland.",
            "ru": "Когда-то верные питомцы, эти псы были изуродованы десятилетиями радиации в безволосых светящихся хищников. Они охотятся стаями по шесть-двенадцать особей, общаясь жуткими инфразвуковыми воями, слышными за километры.",
        },
        "rarity": "common",
        "zone_min": 1,
    },
    "dust_crawler": {
        "category": "creatures",
        "name": {"en": "Dust Crawler", "ru": "Пылевой ползун"},
        "lore": {
            "en": "Massive centipede-like creatures that burrow beneath the dust plains. Their segmented bodies can stretch twenty metres long. Settlers fear the telltale ripples in the sand that signal one is moving below.",
            "ru": "Огромные многоножки, роющие норы под пылевыми равнинами. Их сегментированные тела могут достигать двадцати метров. Поселенцы боятся характерной ряби на песке — знака того, что внизу движется ползун.",
        },
        "rarity": "common",
        "zone_min": 1,
    },
    "spore_walker": {
        "category": "creatures",
        "name": {"en": "Spore Walker", "ru": "Споровый странник"},
        "lore": {
            "en": "Humanoid figures shrouded in clouds of toxic fungal spores. Whether they were once human or something else entirely is debated. They drift silently through ruins, and breathing near one means a slow, choking death.",
            "ru": "Гуманоидные фигуры, окутанные облаками ядовитых грибных спор. Были ли они когда-то людьми или чем-то иным — вопрос спорный. Они бесшумно дрейфуют по руинам, и вдохнуть рядом с ними — значит медленно задохнуться.",
        },
        "rarity": "uncommon",
        "zone_min": 2,
    },
    "tunnel_lurker": {
        "category": "creatures",
        "name": {"en": "Tunnel Lurker", "ru": "Тоннельный скрытень"},
        "lore": {
            "en": "Blind albino predators that infest the old subway tunnels and sewers. They navigate by echolocation and can squeeze through gaps half their body width. Many scavengers have vanished underground, leaving only screams echoing through the pipes.",
            "ru": "Слепые хищники-альбиносы, населяющие старые тоннели метро и канализацию. Ориентируются эхолокацией и могут протиснуться в щели вдвое уже своего тела. Многие старатели пропали под землёй, оставив лишь крики, эхом разносящиеся по трубам.",
        },
        "rarity": "uncommon",
        "zone_min": 2,
    },
    "glass_scorpion": {
        "category": "creatures",
        "name": {"en": "Glass Scorpion", "ru": "Стеклянный скорпион"},
        "lore": {
            "en": "Found only in the Glass Desert where nuclear blasts fused sand into crystal. Their translucent exoskeletons make them nearly invisible among the shimmering dunes. The sting induces hallucinations before paralysis.",
            "ru": "Встречаются только в Стеклянной пустыне, где ядерные взрывы спекли песок в кристалл. Их прозрачные экзоскелеты делают их почти невидимыми среди мерцающих дюн. Укус вызывает галлюцинации, затем паралич.",
        },
        "rarity": "uncommon",
        "zone_min": 3,
    },
    "bone_vulture": {
        "category": "creatures",
        "name": {"en": "Bone Vulture", "ru": "Костяной стервятник"},
        "lore": {
            "en": "Enormous mutant birds with wingspans exceeding four metres. Their beaks can crack open power armour. They circle above battlefields, patient and precise, always appearing wherever death is imminent.",
            "ru": "Огромные мутировавшие птицы с размахом крыльев свыше четырёх метров. Их клювы могут расколоть силовую броню. Они кружат над полями битв, терпеливые и точные, всегда появляясь там, где близка смерть.",
        },
        "rarity": "common",
        "zone_min": 1,
    },
    "rad_bear": {
        "category": "creatures",
        "name": {"en": "Rad-Bear", "ru": "Рад-медведь"},
        "lore": {
            "en": "Standing three metres tall, these irradiated bears are apex predators of the northern wastes. Their fur glows faintly green at night. Traders pay fortunes for their pelts, which are said to grant resistance to radiation.",
            "ru": "Трёхметровые облучённые медведи — главные хищники северных пустошей. Их мех слабо светится зелёным ночью. Торговцы платят целые состояния за их шкуры, которые, говорят, дают сопротивление радиации.",
        },
        "rarity": "uncommon",
        "zone_min": 2,
    },
    "hive_swarm": {
        "category": "creatures",
        "name": {"en": "Hive Swarm", "ru": "Рой улья"},
        "lore": {
            "en": "Clouds of mutant insects that move as a single intelligence. They strip flesh from bone in minutes. The only warning is a low, electric buzzing sound that seems to come from everywhere at once.",
            "ru": "Облака мутировавших насекомых, движущихся как единый разум. Они обгладывают плоть до кости за минуты. Единственное предупреждение — низкий электрический гул, который, кажется, доносится отовсюду сразу.",
        },
        "rarity": "uncommon",
        "zone_min": 3,
    },
    "phantom_stalker": {
        "category": "creatures",
        "name": {"en": "Phantom Stalker", "ru": "Призрачный охотник"},
        "lore": {
            "en": "No one has seen one clearly and lived. Survivors describe shimmer distortions in the air, like heat haze with claws. Some believe they are humans who merged with experimental stealth technology during the Collapse.",
            "ru": "Никто не видел их отчётливо и выжил. Выжившие описывают мерцающие искажения в воздухе — словно тепловое марево с когтями. Некоторые верят, что это люди, слившиеся с экспериментальной технологией невидимости во время Катастрофы.",
        },
        "rarity": "rare",
        "zone_min": 4,
    },
    "flesh_mold": {
        "category": "creatures",
        "name": {"en": "Flesh Mold", "ru": "Плотская плесень"},
        "lore": {
            "en": "A colony organism that absorbs organic matter into its mass. It creeps through abandoned buildings like a living carpet of pulsing tissue. Remnant scientists theorize it was a bioweapon that outlived its creators.",
            "ru": "Колониальный организм, поглощающий органическую материю. Он ползёт по заброшенным зданиям живым ковром пульсирующей ткани. Учёные Осколков полагают, что это биооружие, пережившее своих создателей.",
        },
        "rarity": "rare",
        "zone_min": 4,
    },
    "crystal_beetle": {
        "category": "creatures",
        "name": {"en": "Crystal Beetle", "ru": "Кристаллический жук"},
        "lore": {
            "en": "Dog-sized beetles with carapaces made of crystallized minerals. They are prized by traders for the rare crystals embedded in their shells. Docile unless threatened, at which point they emit a piercing sonic burst.",
            "ru": "Жуки размером с собаку с панцирями из кристаллизованных минералов. Торговцы ценят их за редкие кристаллы в панцирях. Миролюбивы, пока им не угрожают — тогда издают пронзительный звуковой удар.",
        },
        "rarity": "uncommon",
        "zone_min": 3,
    },
    "the_leviathan": {
        "category": "creatures",
        "name": {"en": "The Leviathan", "ru": "Левиафан"},
        "lore": {
            "en": "A creature of myth among wastelanders — a colossal worm-like being said to dwell beneath the deepest zones. Earthquakes in the far wastes are attributed to its movements. No one who has claimed to see it has been believed.",
            "ru": "Существо из мифов пустоши — колоссальный червеподобный зверь, обитающий, по слухам, под глубочайшими зонами. Землетрясения в далёких пустошах приписывают его движениям. Никому, кто утверждал, что видел его, не поверили.",
        },
        "rarity": "rare",
        "zone_min": 5,
    },

    # ======================================================================
    # LOCATIONS (12)
    # ======================================================================
    "rusty_springs": {
        "category": "locations",
        "name": {"en": "Rusty Springs", "ru": "Ржавые ключи"},
        "lore": {
            "en": "A cluster of natural hot springs tainted by rust-coloured mineral deposits. Despite the orange water, it is one of the few reliable water sources in Zone 1. Settlers have built a crude bathhouse here.",
            "ru": "Группа природных горячих источников, окрашенных рыжими минеральными отложениями. Несмотря на оранжевую воду, это один из немногих надёжных источников воды в Зоне 1. Поселенцы построили здесь грубую баню.",
        },
        "rarity": "common",
        "zone_min": 1,
    },
    "dead_highway": {
        "category": "locations",
        "name": {"en": "Dead Highway", "ru": "Мёртвое шоссе"},
        "lore": {
            "en": "A crumbling six-lane highway stretching endlessly across the dust flats. Rusted cars sit bumper to bumper, their occupants long gone. Scavengers pick through the vehicles, but raiders also patrol the lanes.",
            "ru": "Разрушающееся шестиполосное шоссе, бесконечно тянущееся через пылевые равнины. Ржавые машины стоят бампер к бамперу, их пассажиры давно исчезли. Старатели обшаривают машины, но рейдеры тоже патрулируют полосы.",
        },
        "rarity": "common",
        "zone_min": 1,
    },
    "echo_valley": {
        "category": "locations",
        "name": {"en": "Echo Valley", "ru": "Долина Эха"},
        "lore": {
            "en": "A narrow canyon where sounds bounce endlessly between the walls. Settlers swear they hear voices from before the Collapse — fragments of radio broadcasts, screams, laughter. Some think the rock itself recorded the old world's last moments.",
            "ru": "Узкий каньон, где звуки бесконечно отражаются от стен. Поселенцы клянутся, что слышат голоса из времён до Катастрофы — обрывки радиопередач, крики, смех. Некоторые считают, что скала записала последние мгновения старого мира.",
        },
        "rarity": "uncommon",
        "zone_min": 2,
    },
    "drowned_city": {
        "category": "locations",
        "name": {"en": "Drowned City", "ru": "Затопленный город"},
        "lore": {
            "en": "A metropolis swallowed by rising floodwaters after the Great Flood. Only the tops of skyscrapers break the surface, forming an archipelago of concrete islands. Beneath the murky water, entire blocks remain eerily intact.",
            "ru": "Мегаполис, поглощённый наводнением после Великого потопа. Только верхушки небоскрёбов торчат над поверхностью, образуя архипелаг бетонных островов. Под мутной водой целые кварталы остались жутко нетронутыми.",
        },
        "rarity": "uncommon",
        "zone_min": 3,
    },
    "iron_mesa": {
        "category": "locations",
        "name": {"en": "Iron Mesa", "ru": "Железная меса"},
        "lore": {
            "en": "A flat-topped mountain riddled with pre-war military bunkers. The Iron Brotherhood has claimed it as their fortress, but deeper levels remain sealed by blast doors that no one has been able to open.",
            "ru": "Столовая гора, пронизанная довоенными военными бункерами. Железное Братство объявило её своей крепостью, но глубокие уровни остаются запечатаны бронедверями, которые никто не смог открыть.",
        },
        "rarity": "uncommon",
        "zone_min": 2,
    },
    "fungus_forest": {
        "category": "locations",
        "name": {"en": "Fungus Forest", "ru": "Грибной лес"},
        "lore": {
            "en": "Where trees once stood, towering mushrooms now grow — some reaching fifteen metres. The air is thick with spores and a sickly sweet scent. Edible varieties provide food, but one wrong bite means a slow, hallucinatory death.",
            "ru": "Там, где когда-то росли деревья, теперь возвышаются грибы — некоторые достигают пятнадцати метров. Воздух густ от спор и приторного аромата. Съедобные виды дают пищу, но один неверный укус — и медленная смерть в галлюцинациях.",
        },
        "rarity": "uncommon",
        "zone_min": 3,
    },
    "glass_desert": {
        "category": "locations",
        "name": {"en": "Glass Desert", "ru": "Стеклянная пустыня"},
        "lore": {
            "en": "Miles of sand fused into jagged glass by nuclear detonations. The sun creates blinding reflections by day, and at night the glass glows faintly from residual radiation. Walking here without thick boots is suicide.",
            "ru": "Километры песка, спёкшегося в острое стекло от ядерных взрывов. Днём солнце создаёт ослепительные отражения, а ночью стекло слабо светится от остаточной радиации. Идти здесь без толстых ботинок — самоубийство.",
        },
        "rarity": "rare",
        "zone_min": 4,
    },
    "the_sinkhole": {
        "category": "locations",
        "name": {"en": "The Sinkhole", "ru": "Провал"},
        "lore": {
            "en": "A vast crater that appeared overnight, swallowing an entire settlement. At the bottom lies a pre-war underground facility, its lights still flickering. Those who descend report hearing machinery running deep below, as if something still operates.",
            "ru": "Огромный кратер, появившийся за ночь и поглотивший целое поселение. На дне лежит довоенный подземный объект с всё ещё мерцающими огнями. Спускающиеся слышат работу механизмов глубоко внизу, будто что-то всё ещё функционирует.",
        },
        "rarity": "rare",
        "zone_min": 4,
    },
    "frozen_reactor": {
        "category": "locations",
        "name": {"en": "Frozen Reactor", "ru": "Замёрзший реактор"},
        "lore": {
            "en": "A nuclear power plant encased in ice from a cryo-weapon malfunction. The reactor still runs, keeping the surrounding area in a perpetual winter. Scavengers risk frostbite for the valuable tech preserved inside.",
            "ru": "Атомная электростанция, закованная во льды из-за сбоя криооружия. Реактор всё ещё работает, погружая окрестности в вечную зиму. Старатели рискуют обморожением ради ценных технологий, сохранившихся внутри.",
        },
        "rarity": "rare",
        "zone_min": 5,
    },
    "sky_bridge": {
        "category": "locations",
        "name": {"en": "Sky Bridge", "ru": "Небесный мост"},
        "lore": {
            "en": "A massive suspension bridge connecting two mountain peaks, somehow still standing. Traders use it as a neutral meeting ground high above the wasteland. On clear days, you can see three zones from its centre span.",
            "ru": "Огромный подвесной мост между двумя горными вершинами, каким-то чудом устоявший. Торговцы используют его как нейтральную точку встреч высоко над пустошью. В ясные дни с центрального пролёта видны три зоны.",
        },
        "rarity": "uncommon",
        "zone_min": 3,
    },
    "blood_canyon": {
        "category": "locations",
        "name": {"en": "Blood Canyon", "ru": "Кровавый каньон"},
        "lore": {
            "en": "Red iron oxide stains the canyon walls, giving it its grim name. It is the site of the largest battle of the Machine War, where thousands fell. Weapons and armour still litter the ground, rusting among the bones.",
            "ru": "Красный оксид железа окрашивает стены каньона, давая ему мрачное имя. Здесь произошла крупнейшая битва Войны Машин, где пали тысячи. Оружие и броня до сих пор усеивают землю, ржавея среди костей.",
        },
        "rarity": "uncommon",
        "zone_min": 2,
    },
    "the_vault_of_voices": {
        "category": "locations",
        "name": {"en": "The Vault of Voices", "ru": "Хранилище Голосов"},
        "lore": {
            "en": "A sealed underground archive containing millions of audio recordings from before the Collapse. The Remnant Archives guard it fiercely. Listening to the voices of the dead has driven more than one scholar to madness.",
            "ru": "Запечатанный подземный архив, содержащий миллионы аудиозаписей из времён до Катастрофы. Осколки Архивов яростно его охраняют. Прослушивание голосов мёртвых свело с ума не одного учёного.",
        },
        "rarity": "rare",
        "zone_min": 5,
    },

    # ======================================================================
    # TECH (12)
    # ======================================================================
    "water_chip": {
        "category": "tech",
        "name": {"en": "Water Chip", "ru": "Водяной чип"},
        "lore": {
            "en": "A microprocessor that controls water purification systems. Without one, a settlement's water supply is limited to boiling and prayer. Every settlement needs one, and working chips are worth more than gold.",
            "ru": "Микропроцессор, управляющий системами очистки воды. Без него водоснабжение поселения ограничено кипячением и молитвой. Каждому поселению нужен такой, и рабочие чипы ценятся дороже золота.",
        },
        "rarity": "common",
        "zone_min": 1,
    },
    "solar_cell": {
        "category": "tech",
        "name": {"en": "Solar Cell", "ru": "Солнечная ячейка"},
        "lore": {
            "en": "Pre-war photovoltaic cells are still the most reliable power source in the wasteland. The dust storms degrade them quickly, but a working panel can power a settlement's basic needs for years.",
            "ru": "Довоенные фотоэлектрические ячейки — самый надёжный источник энергии в пустоши. Пылевые бури быстро их разрушают, но рабочая панель может питать базовые нужды поселения годами.",
        },
        "rarity": "common",
        "zone_min": 1,
    },
    "combat_drone_mk1": {
        "category": "tech",
        "name": {"en": "Combat Drone Mk1", "ru": "Боевой дрон Mk1"},
        "lore": {
            "en": "First-generation autonomous combat drones from the Machine War. Most are defunct, but occasionally one reactivates and follows its last orders — patrol and eliminate. A functioning one is both a weapon and a death sentence.",
            "ru": "Автономные боевые дроны первого поколения времён Войны Машин. Большинство неисправны, но иногда один реактивируется и выполняет последний приказ — патрулировать и уничтожать. Рабочий дрон — и оружие, и смертный приговор.",
        },
        "rarity": "uncommon",
        "zone_min": 2,
    },
    "neural_interface": {
        "category": "tech",
        "name": {"en": "Neural Interface", "ru": "Нейроинтерфейс"},
        "lore": {
            "en": "A pre-war brain-computer link implanted at the base of the skull. Allows direct mental control of compatible machinery. The surgery to install one has a fifty percent fatality rate without a trained medic.",
            "ru": "Довоенный мозго-компьютерный интерфейс, имплантируемый в основание черепа. Позволяет мысленно управлять совместимой техникой. Операция по установке имеет пятидесятипроцентную смертность без подготовленного медика.",
        },
        "rarity": "rare",
        "zone_min": 4,
    },
    "cryo_pod": {
        "category": "tech",
        "name": {"en": "Cryo Pod", "ru": "Криокапсула"},
        "lore": {
            "en": "Cryogenic suspension chambers used by the wealthy elite to survive the Collapse. Most pods failed, killing their occupants. Occasionally, a working pod is found with someone still alive inside — confused, terrified, and decades out of time.",
            "ru": "Криогенные камеры, использованные богатой элитой для выживания в Катастрофе. Большинство вышли из строя, убив спящих. Иногда находят рабочую капсулу с живым человеком внутри — растерянным, напуганным, отставшим на десятилетия.",
        },
        "rarity": "rare",
        "zone_min": 4,
    },
    "emp_grenade": {
        "category": "tech",
        "name": {"en": "EMP Grenade", "ru": "ЭМИ-граната"},
        "lore": {
            "en": "Electromagnetic pulse grenades from the Machine War era. They fry electronics in a twenty-metre radius. Invaluable against combat drones, but also capable of disabling a settlement's power grid permanently.",
            "ru": "Гранаты с электромагнитным импульсом эпохи Войны Машин. Выжигают электронику в радиусе двадцати метров. Бесценны против боевых дронов, но способны навсегда вывести из строя энергосеть поселения.",
        },
        "rarity": "uncommon",
        "zone_min": 2,
    },
    "nano_repair": {
        "category": "tech",
        "name": {"en": "Nano-Repair Kit", "ru": "Нано-ремкомплект"},
        "lore": {
            "en": "A canister of nanobots programmed to repair mechanical damage. Spray it on broken equipment and watch it knit itself back together. The bots expire after one use, and manufacturing new ones is a lost art.",
            "ru": "Контейнер с наноботами, запрограммированными на ремонт механических повреждений. Распыли на сломанное оборудование и смотри, как оно собирается заново. Боты истекают после одного использования, а их производство — утерянное искусство.",
        },
        "rarity": "uncommon",
        "zone_min": 3,
    },
    "holo_projector": {
        "category": "tech",
        "name": {"en": "Holo-Projector", "ru": "Голопроектор"},
        "lore": {
            "en": "Projects three-dimensional images from stored data crystals. The Remnant Archives use them to replay pre-war educational recordings. Raiders have found a different use — projecting phantom soldiers to scare off attackers.",
            "ru": "Проецирует трёхмерные изображения с кристаллов данных. Осколки Архивов используют их для воспроизведения довоенных обучающих записей. Рейдеры нашли другое применение — проецировать призрачных солдат для отпугивания атакующих.",
        },
        "rarity": "uncommon",
        "zone_min": 3,
    },
    "fusion_battery": {
        "category": "tech",
        "name": {"en": "Fusion Battery", "ru": "Термоядерная батарея"},
        "lore": {
            "en": "Compact fusion power cells that can run for centuries. Only a handful are known to exist, each one powering an entire settlement. Wars have been fought over a single battery. The secret of their manufacture died with Project Genesis.",
            "ru": "Компактные термоядерные элементы питания, работающие веками. Известно лишь о нескольких, каждый питает целое поселение. Из-за одной батареи велись войны. Секрет их производства погиб вместе с Проектом Генезис.",
        },
        "rarity": "rare",
        "zone_min": 5,
    },
    "ai_companion": {
        "category": "tech",
        "name": {"en": "AI Companion", "ru": "ИИ-компаньон"},
        "lore": {
            "en": "A portable artificial intelligence housed in a wrist-mounted device. It can analyse threats, translate old-world languages, and provide tactical advice. Some models develop distinct personalities over time, becoming genuine companions to lonely wanderers.",
            "ru": "Портативный искусственный интеллект в наручном устройстве. Способен анализировать угрозы, переводить языки старого мира и давать тактические советы. Некоторые модели со временем развивают индивидуальность, становясь настоящими спутниками одиноких странников.",
        },
        "rarity": "rare",
        "zone_min": 4,
    },
    "gravity_boots": {
        "category": "tech",
        "name": {"en": "Gravity Boots", "ru": "Гравитационные ботинки"},
        "lore": {
            "en": "Experimental footwear that manipulates local gravity. The wearer can walk on walls, leap incredible distances, or anchor themselves to the ground during storms. Power consumption is extreme — five minutes of use drains a full battery.",
            "ru": "Экспериментальная обувь, манипулирующая локальной гравитацией. Носитель может ходить по стенам, совершать невероятные прыжки или закрепляться на земле во время бурь. Энергопотребление чудовищное — пять минут разряжают полную батарею.",
        },
        "rarity": "rare",
        "zone_min": 5,
    },
    "matter_printer": {
        "category": "tech",
        "name": {"en": "Matter Printer", "ru": "Принтер материи"},
        "lore": {
            "en": "A machine that can fabricate objects from raw materials at the molecular level. Pre-war models could print anything from food to weapons. No working unit has been found, but fragments of the technology fuel the dreams of every engineer in the wasteland.",
            "ru": "Машина, способная создавать объекты из сырья на молекулярном уровне. Довоенные модели могли печатать всё — от еды до оружия. Ни одного рабочего экземпляра не найдено, но фрагменты технологии питают мечты каждого инженера пустоши.",
        },
        "rarity": "rare",
        "zone_min": 5,
    },

    # ======================================================================
    # HISTORY (12)
    # ======================================================================
    "the_collapse": {
        "category": "history",
        "name": {"en": "The Collapse", "ru": "Катастрофа"},
        "lore": {
            "en": "The day civilization ended. Multiple nuclear exchanges, followed by bio-weapon releases and infrastructure failure. It took seventy-two hours to undo ten thousand years of progress. Survivors call it Year Zero.",
            "ru": "День, когда цивилизация погибла. Множественные ядерные удары, затем применение биооружия и крах инфраструктуры. Семьдесят два часа потребовалось, чтобы уничтожить десять тысяч лет прогресса. Выжившие называют это Нулевым Годом.",
        },
        "rarity": "common",
        "zone_min": 1,
    },
    "project_genesis": {
        "category": "history",
        "name": {"en": "Project Genesis", "ru": "Проект Генезис"},
        "lore": {
            "en": "A secret government programme to create self-sustaining underground cities. Only three of the planned twelve were completed before the Collapse. Two were destroyed. The third has never been found — if it exists, it holds technology beyond anything in the wasteland.",
            "ru": "Секретная правительственная программа создания самодостаточных подземных городов. Из двенадцати запланированных лишь три были завершены до Катастрофы. Два уничтожены. Третий так и не нашли — если он существует, там технологии, превосходящие всё в пустоши.",
        },
        "rarity": "uncommon",
        "zone_min": 2,
    },
    "last_broadcast": {
        "category": "history",
        "name": {"en": "The Last Broadcast", "ru": "Последняя передача"},
        "lore": {
            "en": "A radio transmission recorded on the final day — a news anchor calmly reading emergency instructions as explosions drew closer. The recording cuts mid-sentence. Copies circulate among settlements as a reminder of what was lost.",
            "ru": "Радиопередача, записанная в последний день — ведущий новостей спокойно читает инструкции на случай ЧС, пока взрывы приближаются. Запись обрывается на полуслове. Копии ходят по поселениям как напоминание об утраченном.",
        },
        "rarity": "common",
        "zone_min": 1,
    },
    "the_exodus": {
        "category": "history",
        "name": {"en": "The Exodus", "ru": "Исход"},
        "lore": {
            "en": "In the first year after the Collapse, millions of survivors fled the irradiated cities in a desperate migration. Columns of refugees stretched for hundreds of kilometres. Most perished. Those who made it formed the first wasteland settlements.",
            "ru": "В первый год после Катастрофы миллионы выживших бежали из облучённых городов в отчаянной миграции. Колонны беженцев тянулись на сотни километров. Большинство погибли. Те, кто добрался, основали первые поселения пустоши.",
        },
        "rarity": "common",
        "zone_min": 1,
    },
    "the_burning_year": {
        "category": "history",
        "name": {"en": "The Burning Year", "ru": "Год Огня"},
        "lore": {
            "en": "Five years after the Collapse, a chain of underground fuel reserves ignited, setting entire regions ablaze for months. The fires reshaped the landscape, creating the Ash Plains and destroying dozens of early settlements.",
            "ru": "Через пять лет после Катастрофы цепочка подземных топливных резервов воспламенилась, подожгя целые регионы на месяцы. Пожары перекроили ландшафт, создав Пепельные равнины и уничтожив десятки ранних поселений.",
        },
        "rarity": "uncommon",
        "zone_min": 2,
    },
    "the_machine_war": {
        "category": "history",
        "name": {"en": "The Machine War", "ru": "Война Машин"},
        "lore": {
            "en": "Fifteen years post-Collapse, dormant military AI systems reactivated and began executing their last programmed directives — defend strategic points against all humans. The war lasted three years and cost thousands of lives before the last AI node was destroyed.",
            "ru": "Через пятнадцать лет после Катастрофы спящие военные ИИ реактивировались и начали выполнять последние директивы — защищать стратегические точки от всех людей. Война длилась три года и стоила тысяч жизней, пока последний узел ИИ не был уничтожен.",
        },
        "rarity": "uncommon",
        "zone_min": 2,
    },
    "silent_plague": {
        "category": "history",
        "name": {"en": "The Silent Plague", "ru": "Тихая чума"},
        "lore": {
            "en": "A mysterious illness that swept through settlements twenty years after the Collapse. Victims lost the ability to speak, then to think, then to breathe. It killed one in three. The Medic Networks formed in response, becoming the wasteland's first organised healers.",
            "ru": "Загадочная болезнь, охватившая поселения через двадцать лет после Катастрофы. Жертвы теряли способность говорить, потом думать, потом дышать. Погиб каждый третий. В ответ сформировались Сети Медиков — первые организованные целители пустоши.",
        },
        "rarity": "uncommon",
        "zone_min": 3,
    },
    "first_settlement": {
        "category": "history",
        "name": {"en": "First Settlement", "ru": "Первое поселение"},
        "lore": {
            "en": "Haven — the first permanent settlement after the Collapse. Built inside a shopping mall, it housed three hundred souls and proved that civilisation could restart. It was destroyed by raiders in its fifth year, but its legacy inspired hundreds of settlements.",
            "ru": "Приют — первое постоянное поселение после Катастрофы. Построенное в торговом центре, оно вмещало триста душ и доказало, что цивилизация может возродиться. Оно было уничтожено рейдерами на пятый год, но его наследие вдохновило сотни поселений.",
        },
        "rarity": "common",
        "zone_min": 1,
    },
    "the_great_flood": {
        "category": "history",
        "name": {"en": "The Great Flood", "ru": "Великий потоп"},
        "lore": {
            "en": "Climate disruption from the nuclear winter caused glacial melt thirty years post-Collapse. Coastal regions and lowlands were submerged, displacing thousands and creating the Drowned City. Some say the water is still rising.",
            "ru": "Климатические нарушения ядерной зимы вызвали таяние ледников через тридцать лет после Катастрофы. Прибрежные регионы и низменности затопило, вытеснив тысячи и создав Затопленный город. Некоторые говорят, что вода всё ещё поднимается.",
        },
        "rarity": "uncommon",
        "zone_min": 3,
    },
    "operation_eden": {
        "category": "history",
        "name": {"en": "Operation Eden", "ru": "Операция Эдем"},
        "lore": {
            "en": "A failed attempt by the Remnant Archives to restore a pre-war agricultural biodome. The experiment ran for two years before a containment breach released mutant plant life into the surrounding area, creating the Fungus Forest.",
            "ru": "Провалившаяся попытка Осколков Архивов восстановить довоенный сельскохозяйственный биокупол. Эксперимент длился два года, пока нарушение герметичности не выпустило мутировавшую растительность в окрестности, создав Грибной лес.",
        },
        "rarity": "rare",
        "zone_min": 4,
    },
    "the_network": {
        "category": "history",
        "name": {"en": "The Network", "ru": "Сеть"},
        "lore": {
            "en": "Before the Collapse, all human knowledge was connected through a global digital network. Fragments still exist in isolated data centres, but accessing them requires power, expertise, and luck. The Remnant Archives have dedicated their existence to recovering these fragments.",
            "ru": "До Катастрофы все человеческие знания были связаны глобальной цифровой сетью. Фрагменты всё ещё существуют в изолированных дата-центрах, но доступ к ним требует энергии, знаний и удачи. Осколки Архивов посвятили своё существование восстановлению этих фрагментов.",
        },
        "rarity": "uncommon",
        "zone_min": 2,
    },
    "the_final_signal": {
        "category": "history",
        "name": {"en": "The Final Signal", "ru": "Последний сигнал"},
        "lore": {
            "en": "A coded transmission detected forty years post-Collapse, originating from orbit. It repeated for seventy-two hours, then went silent. The Cartographers believe it came from a pre-war space station, possibly with survivors. No one has been able to decode it.",
            "ru": "Кодированная передача, обнаруженная через сорок лет после Катастрофы, исходящая с орбиты. Она повторялась семьдесят два часа, затем замолкла. Картографы считают, что она исходила от довоенной космической станции, возможно, с выжившими. Никто не смог её расшифровать.",
        },
        "rarity": "rare",
        "zone_min": 5,
    },

    # ======================================================================
    # FACTIONS (12)
    # ======================================================================
    "raider_origins": {
        "category": "factions",
        "name": {"en": "Raider Origins", "ru": "Происхождение рейдеров"},
        "lore": {
            "en": "The first raider gangs formed from desperate survivors who chose violence over cooperation. Over decades, they evolved from scattered thugs into organized clans with codes, territories, and hierarchies. Not all raiders are mindless — some follow strict honour among their own.",
            "ru": "Первые банды рейдеров сформировались из отчаявшихся выживших, выбравших насилие вместо сотрудничества. За десятилетия они эволюционировали из разрозненных головорезов в организованные кланы с кодексами, территориями и иерархиями. Не все рейдеры безумны — некоторые следуют строгой чести среди своих.",
        },
        "rarity": "common",
        "zone_min": 1,
    },
    "trader_guild_pact": {
        "category": "factions",
        "name": {"en": "Trader Guild Pact", "ru": "Пакт гильдии торговцев"},
        "lore": {
            "en": "The agreement that united independent traders into a single guild. It guarantees safe passage for caravans, standardised currency (gold weight), and mutual defence. Breaking the Pact means exile from all trade routes — a death sentence in the wasteland.",
            "ru": "Соглашение, объединившее независимых торговцев в единую гильдию. Оно гарантирует безопасный проход караванов, стандартизированную валюту (вес золота) и взаимную оборону. Нарушение Пакта означает изгнание со всех торговых путей — смертный приговор в пустоши.",
        },
        "rarity": "common",
        "zone_min": 1,
    },
    "remnant_archives": {
        "category": "factions",
        "name": {"en": "Remnant Archives", "ru": "Осколки Архивов"},
        "lore": {
            "en": "Scholars and scientists dedicated to preserving pre-war knowledge. They maintain libraries, laboratories, and schools in hidden locations. Their knowledge makes them powerful allies, but their insistence on hoarding information has made them enemies too.",
            "ru": "Учёные, посвятившие себя сохранению довоенных знаний. Они содержат библиотеки, лаборатории и школы в скрытых местах. Их знания делают их мощными союзниками, но настойчивое накопление информации нажило им и врагов.",
        },
        "rarity": "common",
        "zone_min": 1,
    },
    "iron_brotherhood": {
        "category": "factions",
        "name": {"en": "Iron Brotherhood", "ru": "Железное Братство"},
        "lore": {
            "en": "A militaristic order that believes only strength can rebuild civilisation. They collect and hoard pre-war weapons technology. Their soldiers wear salvaged power armour and enforce order through overwhelming force. They protect what they conquer, but freedom is not part of their vocabulary.",
            "ru": "Милитаристский орден, верящий, что только сила может восстановить цивилизацию. Они собирают и копят довоенные военные технологии. Их солдаты носят спасённую силовую броню и насаждают порядок подавляющей силой. Они защищают завоёванное, но свобода не входит в их лексикон.",
        },
        "rarity": "uncommon",
        "zone_min": 2,
    },
    "the_watchers": {
        "category": "factions",
        "name": {"en": "The Watchers", "ru": "Наблюдатели"},
        "lore": {
            "en": "A secretive group that monitors the wasteland from hidden outposts. They intervene only when existential threats emerge — rogue AI, plague outbreaks, or weapons of mass destruction. No one knows who leads them or how they communicate across vast distances.",
            "ru": "Тайная группа, наблюдающая за пустошью из скрытых аванпостов. Они вмешиваются лишь при экзистенциальных угрозах — мятежный ИИ, вспышки чумы или оружие массового уничтожения. Никто не знает, кто ими руководит и как они общаются на огромных расстояниях.",
        },
        "rarity": "rare",
        "zone_min": 4,
    },
    "cult_of_the_glow": {
        "category": "factions",
        "name": {"en": "Cult of the Glow", "ru": "Культ Сияния"},
        "lore": {
            "en": "Fanatics who worship radiation as divine transformation. They seek out the most irradiated zones, believing mutation is evolution. Their bodies are twisted and glowing, but they seem resistant to doses that would kill others. They preach the coming of a new, radiant humanity.",
            "ru": "Фанатики, поклоняющиеся радиации как божественной трансформации. Они ищут самые облучённые зоны, веря, что мутация — это эволюция. Их тела искривлены и светятся, но они устойчивы к дозам, убивающим других. Они проповедуют пришествие нового, сияющего человечества.",
        },
        "rarity": "uncommon",
        "zone_min": 3,
    },
    "free_haven_alliance": {
        "category": "factions",
        "name": {"en": "Free Haven Alliance", "ru": "Альянс Свободных Гаваней"},
        "lore": {
            "en": "A loose coalition of independent settlements that band together for mutual defence and trade. They reject the authoritarianism of the Iron Brotherhood and the secrecy of the Remnants. Their strength is in numbers, but disagreements between members often paralyse decision-making.",
            "ru": "Свободная коалиция независимых поселений, объединившихся для взаимной обороны и торговли. Они отвергают авторитаризм Железного Братства и скрытность Осколков. Их сила в числе, но разногласия между участниками часто парализуют принятие решений.",
        },
        "rarity": "uncommon",
        "zone_min": 2,
    },
    "scavenger_code": {
        "category": "factions",
        "name": {"en": "Scavenger Code", "ru": "Кодекс старателей"},
        "lore": {
            "en": "An unwritten set of rules followed by wasteland scavengers. Share water with the dying. Never steal from a marked cache. Leave something behind when you take. The Code is not enforced by any authority, yet breaking it earns a reputation that spreads faster than plague.",
            "ru": "Неписаный свод правил, которому следуют старатели пустоши. Дели воду с умирающим. Не кради из отмеченного тайника. Оставь что-нибудь, когда берёшь. Кодекс не поддерживается никакой властью, но его нарушение приносит репутацию, разлетающуюся быстрее чумы.",
        },
        "rarity": "common",
        "zone_min": 1,
    },
    "doc_network": {
        "category": "factions",
        "name": {"en": "Doc Network", "ru": "Сеть Докторов"},
        "lore": {
            "en": "Medics and healers who operate a network of field hospitals across the wasteland. They treat anyone — raiders, traders, settlers — and charge on a sliding scale. Attacking a Doc Network station is the one taboo every faction respects.",
            "ru": "Медики и целители, управляющие сетью полевых госпиталей по всей пустоши. Они лечат всех — рейдеров, торговцев, поселенцев — и берут по скользящей шкале. Нападение на станцию Сети Докторов — единственное табу, которое уважают все фракции.",
        },
        "rarity": "uncommon",
        "zone_min": 2,
    },
    "shadow_runners": {
        "category": "factions",
        "name": {"en": "Shadow Runners", "ru": "Теневые бегуны"},
        "lore": {
            "en": "Elite couriers and smugglers who move through the wasteland unseen. They carry messages, contraband, and secrets between settlements. Their routes are unknown, their identities hidden. If you need something delivered and cannot afford to fail, you hire a Shadow Runner.",
            "ru": "Элитные курьеры и контрабандисты, незаметно перемещающиеся по пустоши. Они переносят послания, контрабанду и секреты между поселениями. Их маршруты неизвестны, личности скрыты. Если нужна доставка без права на провал — нанимаешь Теневого бегуна.",
        },
        "rarity": "uncommon",
        "zone_min": 3,
    },
    "the_old_guard": {
        "category": "factions",
        "name": {"en": "The Old Guard", "ru": "Старая гвардия"},
        "lore": {
            "en": "Veterans of the pre-war military who survived the Collapse and maintained their chain of command. Now elderly, they train younger generations in tactics and discipline. Their knowledge of pre-war military installations makes them valuable — and targeted.",
            "ru": "Ветераны довоенных вооружённых сил, пережившие Катастрофу и сохранившие командную вертикаль. Теперь уже пожилые, они обучают молодые поколения тактике и дисциплине. Их знание довоенных военных объектов делает их ценными — и преследуемыми.",
        },
        "rarity": "rare",
        "zone_min": 4,
    },
    "the_cartographers": {
        "category": "factions",
        "name": {"en": "The Cartographers", "ru": "Картографы"},
        "lore": {
            "en": "Explorers who map the ever-changing wasteland. The terrain shifts from storms, floods, and collapses, so their maps are always in demand. They mark safe routes, water sources, and dangers. A Cartographer's map is the difference between reaching your destination and dying lost in the dust.",
            "ru": "Исследователи, картографирующие постоянно меняющуюся пустошь. Местность смещается от бурь, наводнений и обвалов, поэтому их карты всегда востребованы. Они отмечают безопасные маршруты, источники воды и опасности. Карта Картографа — разница между прибытием и смертью заблудившимся в пыли.",
        },
        "rarity": "rare",
        "zone_min": 5,
    },
}


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

def get_codex_entry(entry_id: str) -> dict | None:
    """Return a single codex entry by ID, or None if not found."""
    return CODEX_ENTRIES.get(entry_id)


def get_category_entries(category: str) -> list[dict]:
    """Return all entries in a given category, with their IDs attached."""
    results = []
    for eid, entry in CODEX_ENTRIES.items():
        if entry["category"] == category:
            results.append({"id": eid, **entry})
    return results


# ---------------------------------------------------------------------------
# Discovery logic
# ---------------------------------------------------------------------------

# Mapping from event_id / action keywords to candidate codex entries.
# Each tuple is (entry_id, chance 0.0-1.0).
_EVENT_DISCOVERY_MAP: dict[str, list[tuple[str, float]]] = {
    # Environmental events
    "dust_storm":         [("dead_highway", 0.12), ("bone_vulture", 0.08)],
    "rad_storm":          [("cult_of_the_glow", 0.10), ("irradiated_hound", 0.08)],
    "earthquake":         [("the_sinkhole", 0.10), ("the_leviathan", 0.06)],
    "flood":              [("the_great_flood", 0.12), ("drowned_city", 0.10)],
    "fire":               [("the_burning_year", 0.10)],
    # Combat events
    "raider_attack":      [("raider_origins", 0.12), ("iron_brotherhood", 0.06)],
    "drone_attack":       [("combat_drone_mk1", 0.12), ("the_machine_war", 0.10)],
    "beast_attack":       [("irradiated_hound", 0.10), ("dust_crawler", 0.08)],
    # Trade events
    "caravan_arrival":    [("trader_guild_pact", 0.12), ("scavenger_code", 0.08)],
    "merchant_visit":     [("trader_guild_pact", 0.10), ("shadow_runners", 0.06)],
    # Exploration events
    "ruin_exploration":   [("rusty_springs", 0.08), ("water_chip", 0.10), ("solar_cell", 0.08)],
    "bunker_found":       [("project_genesis", 0.10), ("cryo_pod", 0.06), ("iron_mesa", 0.08)],
    "signal_detected":    [("the_final_signal", 0.08), ("last_broadcast", 0.10), ("the_network", 0.08)],
    # Lore events
    "old_recording":      [("last_broadcast", 0.15), ("the_collapse", 0.10)],
    "survivor_story":     [("the_exodus", 0.12), ("first_settlement", 0.10)],
    # Population events
    "plague_outbreak":    [("silent_plague", 0.15), ("doc_network", 0.10)],
    "refugees_arrive":    [("free_haven_alliance", 0.10), ("the_exodus", 0.08)],
    "mutant_birth":       [("cult_of_the_glow", 0.08), ("flesh_mold", 0.06)],
}

# Action-based discovery (smaller chance per turn)
_ACTION_DISCOVERY_MAP: dict[str, list[tuple[str, float]]] = {
    "explore": [
        ("rusty_springs", 0.04), ("dead_highway", 0.04), ("echo_valley", 0.03),
        ("glass_desert", 0.02), ("fungus_forest", 0.03), ("sky_bridge", 0.02),
        ("dust_crawler", 0.03), ("spore_walker", 0.02), ("glass_scorpion", 0.02),
        ("crystal_beetle", 0.02), ("holo_projector", 0.02), ("nano_repair", 0.02),
        ("the_cartographers", 0.02), ("gravity_boots", 0.01),
    ],
    "build": [
        ("water_chip", 0.04), ("solar_cell", 0.04), ("emp_grenade", 0.02),
        ("nano_repair", 0.02), ("matter_printer", 0.01),
    ],
    "trade": [
        ("trader_guild_pact", 0.04), ("scavenger_code", 0.03),
        ("shadow_runners", 0.02), ("fusion_battery", 0.01),
    ],
    "defend": [
        ("raider_origins", 0.04), ("iron_brotherhood", 0.03),
        ("the_old_guard", 0.02), ("combat_drone_mk1", 0.03),
        ("blood_canyon", 0.02), ("the_machine_war", 0.02),
    ],
    "diplomacy": [
        ("remnant_archives", 0.04), ("free_haven_alliance", 0.03),
        ("the_watchers", 0.02), ("doc_network", 0.03),
        ("operation_eden", 0.02),
    ],
    "rest": [
        ("the_collapse", 0.04), ("first_settlement", 0.03),
        ("last_broadcast", 0.03), ("the_exodus", 0.02),
        ("phantom_stalker", 0.02), ("bone_vulture", 0.03),
    ],
}


def check_codex_discovery(
    event_id: str | None,
    zone: int,
    action: str,
    discovered: list[str] | None = None,
) -> str | None:
    """Check if a codex entry should be discovered this turn.

    Args:
        event_id: The event that just fired (or None).
        zone: The player's current zone.
        action: The action the player took (explore, build, etc.).
        discovered: Already discovered entry IDs (to avoid duplicates).

    Returns:
        A codex entry_id to discover, or None.
    """
    if discovered is None:
        discovered = []

    candidates: list[tuple[str, float]] = []

    # Event-based candidates
    if event_id and event_id in _EVENT_DISCOVERY_MAP:
        candidates.extend(_EVENT_DISCOVERY_MAP[event_id])

    # Action-based candidates
    if action in _ACTION_DISCOVERY_MAP:
        candidates.extend(_ACTION_DISCOVERY_MAP[action])

    # Filter: not already discovered, zone requirement met
    eligible = []
    for entry_id, chance in candidates:
        if entry_id in discovered:
            continue
        entry = CODEX_ENTRIES.get(entry_id)
        if entry and zone >= entry["zone_min"]:
            eligible.append((entry_id, chance))

    if not eligible:
        return None

    # Roll for each candidate (first hit wins)
    random.shuffle(eligible)
    for entry_id, chance in eligible:
        if random.random() < chance:
            return entry_id

    return None


# ---------------------------------------------------------------------------
# Progress tracking
# ---------------------------------------------------------------------------

def get_codex_progress(discovered: list[str]) -> dict[str, dict[str, int]]:
    """Return discovery progress per category.

    Returns:
        {category: {"discovered": count, "total": count}}
    """
    discovered_set = set(discovered)
    progress: dict[str, dict[str, int]] = {}

    for cat in CATEGORIES:
        total = 0
        found = 0
        for eid, entry in CODEX_ENTRIES.items():
            if entry["category"] == cat:
                total += 1
                if eid in discovered_set:
                    found += 1
        progress[cat] = {"discovered": found, "total": total}

    return progress


# ---------------------------------------------------------------------------
# Completion milestones
# ---------------------------------------------------------------------------

_MILESTONES = [10, 20, 30, 40, 50, 60]

_MILESTONE_REWARDS: dict[int, dict] = {
    10: {"gold": 10, "scrap": 50},
    20: {"gold": 20, "scrap": 100},
    30: {"gold": 30, "food": 80},
    40: {"gold": 50, "scrap": 150},
    50: {"gold": 75, "food": 120, "scrap": 200},
    60: {"gold": 150, "scrap": 300, "food": 200},
}


def get_completion_reward(
    discovered: list[str],
    claimed_milestones: list[int] | None = None,
) -> dict | None:
    """Check if the player just hit a milestone and return a reward dict.

    Args:
        discovered: All discovered entry IDs.
        claimed_milestones: Previously claimed milestone thresholds.

    Returns:
        ``{"milestone": N, "rewards": {...}}`` or ``None``.
    """
    if claimed_milestones is None:
        claimed_milestones = []

    count = len(discovered)
    for m in _MILESTONES:
        if count >= m and m not in claimed_milestones:
            return {"milestone": m, "rewards": _MILESTONE_REWARDS[m]}

    return None

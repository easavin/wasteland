"""World lore constants for the Wasteland Chronicles narrator.

The world is set 15 years after 'The Collapse' — a cascade of interconnected
catastrophes. Modern 2025-2026 events are reflected through a distorted mirror,
renamed and mythologized by survivors.
"""

LORE_SUMMARY = """WORLD OF WASTELAND CHRONICLES:
15 years after The Collapse — a cascade of plague (The Wasting), resource wars
(The Iron Harvest), trade disintegration (The Accord Collapse), and rogue AI
(The Thinking Machines). The Network (tech oligarchs) controls information from
fortified data centers. The Hegemony (fallen superpower) fractured into feudal
military zones. The Digital Purge destroyed most recorded knowledge. Green Zones
(fertile land) are the most contested territories.

KEY ENTITIES:
- The Network: shadowy tech alliance trading information for loyalty, running
  drone networks and automated factories. Their currency is data.
- The Hegemony: once the mightiest force, now splintered into feudal territories
  run by ex-generals demanding tribute for "protection."
- The Wasting: the great plague. Survivors carry genetic markers. Communities
  still quarantine newcomers for seven days.
- The Iron Harvest: wars over oil, lithium, clean water. Turned farmland into
  minefields.
- The Thinking Machines: military AI that outlived their masters. Autonomous
  drones patrol dead cities. Some offer help — at a hidden cost.
- The Accord Collapse: when trade agreements shattered, supply chains died
  overnight. The Trader Guild rose from the ashes.
- The Digital Purge: mobs destroyed servers and libraries. Written records are
  treasured. Oral tradition returned.
- Green Zones: regions where crops still grow. Most contested territories.

FACTIONS:
- Raiders: paramilitary survivors, respect strength, trade in violence
- Trader Guild: commerce-driven caravaneers, reliable but mercenary
- Remnants: knowledge-keepers from old universities, seek to rebuild

The player leads a settlement struggling to survive in this world."""

FACTION_LORE = {
    "raiders": (
        "Born from the desperate and dispossessed. Not mindless brutes — many are "
        "organized paramilitary groups with their own code. They respect strength "
        "above all. Ally with them and you gain fierce warriors."
    ),
    "traders": (
        "The Trader Guild controls barter routes and caravan paths. Pragmatic, "
        "profit-driven, utterly reliable — as long as you can pay. Their intelligence "
        "network rivals The Network's."
    ),
    "remnants": (
        "Scholars, scientists, engineers who preserved pre-Collapse knowledge. "
        "They operate from fortified campuses and underground labs. They trade "
        "technology for resources and protection. Their goal: rebuild civilization."
    ),
}


# ---------------------------------------------------------------------------
# Class lore — gives the narrator flavour when referencing the player's class
# ---------------------------------------------------------------------------

CLASS_LORE: dict[str, str] = {
    "scavenger": (
        "The Scavenger archetype: ruins-runners, salvage experts, born looters. "
        "They read collapsed buildings like others read maps — knowing exactly "
        "which rubble pile hides pre-Collapse tech and which hides a deathtrap. "
        "Other survivors call them rats. The smart ones call them indispensable."
    ),
    "warden": (
        "The Warden archetype: ex-military, militia captains, born defenders. "
        "They think in perimeters and killzones. Every wall they build is a "
        "statement — this ground is held. Raiders learn quick: settlements led "
        "by Wardens cost more blood than they're worth."
    ),
    "trader": (
        "The Trader archetype: caravan bosses, market makers, dealmakers. "
        "They survived The Collapse by being useful to everyone and loyal to "
        "no one. They know every barter route, every supply cache, every "
        "faction's price. Gold flows where Traders walk."
    ),
    "diplomat": (
        "The Diplomat archetype: smooth talkers, bridge-builders, spymasters. "
        "In a world where a misunderstood gesture starts wars, Diplomats are "
        "the ones who prevent bloodshed — or orchestrate it from a safe distance. "
        "Factions that ignore them tend to find their allies switching sides."
    ),
    "medic": (
        "The Medic archetype: field surgeons, plague doctors, life-bringers. "
        "They kept people breathing through The Wasting when everyone else gave up. "
        "A settlement with a Medic loses fewer souls to starvation, disease, and "
        "despair. Their hands shake, but their patients live."
    ),
}


# ---------------------------------------------------------------------------
# Zone lore — describes the increasing danger as players explore further
# ---------------------------------------------------------------------------

ZONE_LORE: dict[int, str] = {
    1: "Zone 1 — The Near Wastes. Relatively safe scavenging ground with light raider activity.",
    2: "Zone 2 — The Contested Fringe. Hegemony patrols clash with raider bands. Toxic weather rolls in.",
    3: "Zone 3 — The Deep Ruins. Machine patrols, great storms, and buried pre-Collapse tech.",
    4: "Zone 4 — The Network's Edge. Automated defenses, siege-grade threats, but rare treasures.",
    5: "Zone 5 — The Dead Core. Only the strongest settlements dare operate here. Legendary dangers and rewards.",
}

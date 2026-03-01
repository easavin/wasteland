-- Migration 008: NPCs and Mini Quests
-- NPCs are synthetic players that populate the world. Real users can interact
-- with them (trade, quests). Admin controls them from the dashboard.
-- NPCs use negative telegram_id (Telegram never assigns negative IDs).

-- players: mark NPCs
ALTER TABLE players ADD COLUMN IF NOT EXISTS is_npc BOOLEAN NOT NULL DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS idx_players_is_npc ON players(is_npc) WHERE is_npc = TRUE;

-- npc_quests: quest definitions attached to NPCs
CREATE TABLE IF NOT EXISTS npc_quests (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    npc_player_id   UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    quest_key        VARCHAR(80) NOT NULL,
    name            VARCHAR(100) NOT NULL,
    description     TEXT NOT NULL,
    requirements    JSONB NOT NULL DEFAULT '{}',
    rewards         JSONB NOT NULL DEFAULT '{}',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(npc_player_id, quest_key)
);

CREATE INDEX idx_npc_quests_npc ON npc_quests(npc_player_id);
CREATE INDEX idx_npc_quests_active ON npc_quests(npc_player_id, is_active) WHERE is_active = TRUE;

-- player_quest_progress: tracks which players have accepted/completed quests
CREATE TABLE IF NOT EXISTS player_quest_progress (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id       UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    quest_id        UUID NOT NULL REFERENCES npc_quests(id) ON DELETE CASCADE,
    status          VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'completed', 'failed')),
    progress        JSONB NOT NULL DEFAULT '{}',
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    UNIQUE(player_id, quest_id)
);

CREATE INDEX idx_player_quest_progress_player ON player_quest_progress(player_id);
CREATE INDEX idx_player_quest_progress_quest ON player_quest_progress(quest_id);

-- Seed 3 NPCs into the default world
INSERT INTO players (telegram_id, username, first_name, is_npc)
VALUES
  (-1, 'npc_old_trader', 'Old Trader', TRUE),
  (-2, 'npc_doc', 'Doc', TRUE),
  (-3, 'npc_sentry', 'Sentry', TRUE)
ON CONFLICT (telegram_id) DO NOTHING;

INSERT INTO game_states (player_id, settlement_name, display_name, world_id, zone, population, food, scrap, gold)
SELECT id, 'Scrap Haven', 'Old Trader', (SELECT id FROM worlds WHERE is_default = TRUE LIMIT 1), 1, 45, 120, 150, 80
FROM players WHERE telegram_id = -1 AND NOT EXISTS (SELECT 1 FROM game_states gs WHERE gs.player_id = players.id AND gs.status = 'active')
LIMIT 1;

INSERT INTO game_states (player_id, settlement_name, display_name, world_id, zone, population, food, scrap, gold)
SELECT id, 'Last Hope Clinic', 'Doc', (SELECT id FROM worlds WHERE is_default = TRUE LIMIT 1), 1, 30, 80, 40, 120
FROM players WHERE telegram_id = -2 AND NOT EXISTS (SELECT 1 FROM game_states gs WHERE gs.player_id = players.id AND gs.status = 'active')
LIMIT 1;

INSERT INTO game_states (player_id, settlement_name, display_name, world_id, zone, population, food, scrap, gold)
SELECT id, 'Outpost Delta', 'Sentry', (SELECT id FROM worlds WHERE is_default = TRUE LIMIT 1), 2, 60, 90, 120, 45
FROM players WHERE telegram_id = -3 AND NOT EXISTS (SELECT 1 FROM game_states gs WHERE gs.player_id = players.id AND gs.status = 'active')
LIMIT 1;

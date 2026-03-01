-- Wasteland Chronicles - Database Schema (Neon Postgres)
-- Run migrations in shared/migrations/ for incremental updates.
-- This file reflects the target schema after all migrations.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- WORLDS (realms for sharding)
CREATE TABLE IF NOT EXISTS worlds (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(100) NOT NULL,
    is_default      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- PLAYERS
CREATE TABLE players (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telegram_id     BIGINT UNIQUE NOT NULL,
    username        VARCHAR(255),
    first_name      VARCHAR(255),
    language        VARCHAR(5) NOT NULL DEFAULT 'en',
    is_premium      BOOLEAN NOT NULL DEFAULT FALSE,
    premium_expires TIMESTAMPTZ,
    turns_today     INT NOT NULL DEFAULT 0,
    last_turn_date  DATE,
    comm_profile    JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_banned       BOOLEAN NOT NULL DEFAULT FALSE,
    is_npc          BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_players_telegram_id ON players(telegram_id);
CREATE INDEX idx_players_is_npc ON players(is_npc) WHERE is_npc = TRUE;
CREATE INDEX idx_players_created_at ON players(created_at);

-- GAME STATES
CREATE TABLE game_states (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id       UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    status          VARCHAR(20) NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'won', 'lost', 'abandoned')),
    turn_number     INT NOT NULL DEFAULT 0,
    settlement_name VARCHAR(100) NOT NULL,
    display_name    VARCHAR(40),
    world_id        UUID REFERENCES worlds(id) ON DELETE SET NULL,

    player_class    VARCHAR(20) NOT NULL DEFAULT '',

    population      INT NOT NULL DEFAULT 50,
    food            INT NOT NULL DEFAULT 100,
    scrap           INT NOT NULL DEFAULT 80,
    morale          INT NOT NULL DEFAULT 70,
    defense         INT NOT NULL DEFAULT 30,
    gold            INT NOT NULL DEFAULT 0,

    food_zero_turns INT NOT NULL DEFAULT 0,

    raiders_rep     INT NOT NULL DEFAULT 0,
    traders_rep     INT NOT NULL DEFAULT 0,
    remnants_rep    INT NOT NULL DEFAULT 0,

    style_aggression   FLOAT NOT NULL DEFAULT 0.5,
    style_commerce     FLOAT NOT NULL DEFAULT 0.5,
    style_exploration  FLOAT NOT NULL DEFAULT 0.5,
    style_diplomacy    FLOAT NOT NULL DEFAULT 0.5,

    buildings       JSONB NOT NULL DEFAULT '{}',
    active_effects  JSONB NOT NULL DEFAULT '[]',
    narrator_memory JSONB NOT NULL DEFAULT '[]',

    xp              INT NOT NULL DEFAULT 0,
    level           INT NOT NULL DEFAULT 1,
    skill_points    INT NOT NULL DEFAULT 0,
    skills          JSONB NOT NULL DEFAULT '{}',
    milestones      JSONB NOT NULL DEFAULT '[]',
    zone            INT NOT NULL DEFAULT 1,
    inventory       JSONB NOT NULL DEFAULT '[]',

    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at        TIMESTAMPTZ,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_one_active_game
    ON game_states(player_id) WHERE status = 'active';
CREATE INDEX idx_game_states_player ON game_states(player_id);
CREATE INDEX idx_game_states_status ON game_states(status);

-- TURN HISTORY
CREATE TABLE turn_history (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id         UUID NOT NULL REFERENCES game_states(id) ON DELETE CASCADE,
    turn_number     INT NOT NULL,
    player_action   VARCHAR(50) NOT NULL,
    action_target   VARCHAR(100),

    pop_before      INT NOT NULL,
    food_before     INT NOT NULL,
    scrap_before    INT NOT NULL,
    morale_before   INT NOT NULL,
    defense_before  INT NOT NULL,

    pop_delta       INT NOT NULL DEFAULT 0,
    food_delta      INT NOT NULL DEFAULT 0,
    scrap_delta     INT NOT NULL DEFAULT 0,
    morale_delta    INT NOT NULL DEFAULT 0,
    defense_delta   INT NOT NULL DEFAULT 0,

    event_id        VARCHAR(50),
    event_outcome   TEXT,

    narration       TEXT NOT NULL,
    narration_lang  VARCHAR(5) NOT NULL DEFAULT 'en',

    xp_earned       INT NOT NULL DEFAULT 0,
    gold_before     INT NOT NULL DEFAULT 0,
    gold_delta      INT NOT NULL DEFAULT 0,
    level_before    INT NOT NULL DEFAULT 1,
    level_after     INT NOT NULL DEFAULT 1,

    voice_input     BOOLEAN NOT NULL DEFAULT FALSE,
    voice_text      TEXT,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_turns_game ON turn_history(game_id, turn_number);

-- PAYMENTS
CREATE TABLE payments (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id       UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    payment_type    VARCHAR(20) NOT NULL
                        CHECK (payment_type IN ('stars')),
    status          VARCHAR(20) NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    amount          DECIMAL(12, 2) NOT NULL,
    currency        VARCHAR(10) NOT NULL,
    stars_amount    INT,
    telegram_charge_id VARCHAR(255),
    provider_charge_id VARCHAR(255),
    premium_days    INT NOT NULL DEFAULT 30,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

CREATE INDEX idx_payments_player ON payments(player_id);
CREATE INDEX idx_payments_status ON payments(status);

-- ANALYTICS EVENTS
CREATE TABLE analytics_events (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id       UUID REFERENCES players(id) ON DELETE SET NULL,
    event_type      VARCHAR(50) NOT NULL,
    event_data      JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_analytics_type ON analytics_events(event_type);
CREATE INDEX idx_analytics_created ON analytics_events(created_at);
CREATE INDEX idx_analytics_player ON analytics_events(player_id);

-- NPC QUESTS
CREATE TABLE npc_quests (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    npc_player_id   UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    quest_key       VARCHAR(80) NOT NULL,
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

-- PLAYER QUEST PROGRESS
CREATE TABLE player_quest_progress (
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

-- ADMIN USERS
CREATE TABLE admin_users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    role            VARCHAR(20) NOT NULL DEFAULT 'admin'
                        CHECK (role IN ('superadmin', 'admin', 'viewer')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login      TIMESTAMPTZ
);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_players_updated_at
    BEFORE UPDATE ON players FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER set_game_states_updated_at
    BEFORE UPDATE ON game_states FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Migration 009: Retention systems — daily streaks, codex, daily missions, NPC bonds, referrals, comeback
-- Adds engagement layers: items already use existing inventory JSONB on game_states.

-- ── Daily streak columns on players ──
ALTER TABLE players ADD COLUMN IF NOT EXISTS daily_streak        INT NOT NULL DEFAULT 0;
ALTER TABLE players ADD COLUMN IF NOT EXISTS daily_streak_tier   INT NOT NULL DEFAULT 0;
ALTER TABLE players ADD COLUMN IF NOT EXISTS last_daily_claim    DATE;

-- ── Comeback / anti-churn ──
ALTER TABLE players ADD COLUMN IF NOT EXISTS last_active_at      TIMESTAMPTZ;
ALTER TABLE players ADD COLUMN IF NOT EXISTS comeback_tier       INT NOT NULL DEFAULT 0;

-- ── Referral system ──
ALTER TABLE players ADD COLUMN IF NOT EXISTS referred_by         UUID REFERENCES players(id);
ALTER TABLE players ADD COLUMN IF NOT EXISTS referral_count      INT NOT NULL DEFAULT 0;

-- ── Codex on game_states ──
ALTER TABLE game_states ADD COLUMN IF NOT EXISTS codex JSONB NOT NULL DEFAULT '[]';

-- ── Daily missions table ──
CREATE TABLE IF NOT EXISTS daily_missions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id       UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    mission_date    DATE NOT NULL,
    missions        JSONB NOT NULL DEFAULT '[]',
    bonus_claimed   BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(player_id, mission_date)
);

CREATE INDEX IF NOT EXISTS idx_daily_missions_player_date
    ON daily_missions(player_id, mission_date);

-- ── NPC bond tracking ──
CREATE TABLE IF NOT EXISTS npc_bonds (
    player_id        UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    npc_id           TEXT NOT NULL,
    bond_xp          INT NOT NULL DEFAULT 0,
    interactions     INT NOT NULL DEFAULT 0,
    last_interaction TIMESTAMPTZ,
    PRIMARY KEY (player_id, npc_id)
);

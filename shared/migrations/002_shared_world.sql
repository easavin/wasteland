-- Migration 002: Shared World Foundation + Display Names
-- Adds worlds table, world_id and display_name to game_states, enables multiplayer.

-- WORLDS table (realms for sharding)
CREATE TABLE IF NOT EXISTS worlds (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(100) NOT NULL,
    is_default      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_worlds_default ON worlds(is_default) WHERE is_default = TRUE;

-- Create default world (run once; safe to run multiple times)
INSERT INTO worlds (name, is_default)
SELECT 'The Wasteland', TRUE
WHERE NOT EXISTS (SELECT 1 FROM worlds WHERE is_default = TRUE);

-- game_states: display_name (how other players see you)
ALTER TABLE game_states ADD COLUMN IF NOT EXISTS display_name VARCHAR(40);

-- game_states: world_id
ALTER TABLE game_states ADD COLUMN IF NOT EXISTS world_id UUID REFERENCES worlds(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_game_states_world_zone ON game_states(world_id, zone) WHERE status = 'active';

-- Backfill existing game_states to default world
UPDATE game_states
   SET world_id = (SELECT id FROM worlds WHERE is_default = TRUE LIMIT 1)
 WHERE world_id IS NULL
   AND status = 'active';

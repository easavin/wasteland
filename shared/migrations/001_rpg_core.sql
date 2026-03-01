-- Migration 001: RPG Core Transformation
-- Adds player classes, XP/level progression, gold economy, skills, and zones.

-- game_states: new columns
ALTER TABLE game_states ADD COLUMN IF NOT EXISTS player_class VARCHAR(20) NOT NULL DEFAULT '';
ALTER TABLE game_states ADD COLUMN IF NOT EXISTS xp INT NOT NULL DEFAULT 0;
ALTER TABLE game_states ADD COLUMN IF NOT EXISTS level INT NOT NULL DEFAULT 1;
ALTER TABLE game_states ADD COLUMN IF NOT EXISTS gold INT NOT NULL DEFAULT 0;
ALTER TABLE game_states ADD COLUMN IF NOT EXISTS skill_points INT NOT NULL DEFAULT 0;
ALTER TABLE game_states ADD COLUMN IF NOT EXISTS skills JSONB NOT NULL DEFAULT '{}';
ALTER TABLE game_states ADD COLUMN IF NOT EXISTS milestones JSONB NOT NULL DEFAULT '[]';
ALTER TABLE game_states ADD COLUMN IF NOT EXISTS zone INT NOT NULL DEFAULT 1;
ALTER TABLE game_states ADD COLUMN IF NOT EXISTS inventory JSONB NOT NULL DEFAULT '[]';

-- turn_history: new columns for XP/gold/level tracking
ALTER TABLE turn_history ADD COLUMN IF NOT EXISTS xp_earned INT NOT NULL DEFAULT 0;
ALTER TABLE turn_history ADD COLUMN IF NOT EXISTS gold_before INT NOT NULL DEFAULT 0;
ALTER TABLE turn_history ADD COLUMN IF NOT EXISTS gold_delta INT NOT NULL DEFAULT 0;
ALTER TABLE turn_history ADD COLUMN IF NOT EXISTS level_before INT NOT NULL DEFAULT 1;
ALTER TABLE turn_history ADD COLUMN IF NOT EXISTS level_after INT NOT NULL DEFAULT 1;

-- Remove the 'won' status constraint — game is now unlimited.
-- We keep 'won' in the CHECK for backwards compat with historical data.
-- No constraint change needed.

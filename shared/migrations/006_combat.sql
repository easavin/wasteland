-- Migration 006: PvP Combat challenges
-- combat_challenges: siege and raid challenges between settlements

CREATE TABLE IF NOT EXISTS combat_challenges (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    challenger_game_id  UUID NOT NULL REFERENCES game_states(id) ON DELETE CASCADE,
    defender_game_id    UUID NOT NULL REFERENCES game_states(id) ON DELETE CASCADE,
    challenge_type      VARCHAR(20) NOT NULL DEFAULT 'siege'
        CHECK (challenge_type IN ('siege', 'raid')),
    status              VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'accepted', 'declined', 'resolved')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at         TIMESTAMPTZ,
    outcome             JSONB
);

CREATE INDEX idx_combat_defender ON combat_challenges(defender_game_id, status);
CREATE INDEX idx_combat_challenger ON combat_challenges(challenger_game_id);

-- Migration 004: Guilds for shared world
-- guilds, guild_members, guild_invites

CREATE TABLE IF NOT EXISTS guilds (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    world_id        UUID NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    name            VARCHAR(50) NOT NULL,
    leader_game_id  UUID NOT NULL REFERENCES game_states(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(world_id, name)
);

CREATE TABLE IF NOT EXISTS guild_members (
    guild_id        UUID NOT NULL REFERENCES guilds(id) ON DELETE CASCADE,
    game_id         UUID NOT NULL REFERENCES game_states(id) ON DELETE CASCADE,
    role            VARCHAR(20) NOT NULL DEFAULT 'member'
        CHECK (role IN ('leader', 'officer', 'member')),
    joined_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (guild_id, game_id),
    UNIQUE(game_id)
);

CREATE TABLE IF NOT EXISTS guild_invites (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    guild_id        UUID NOT NULL REFERENCES guilds(id) ON DELETE CASCADE,
    inviter_game_id UUID NOT NULL REFERENCES game_states(id) ON DELETE CASCADE,
    invitee_game_id UUID NOT NULL REFERENCES game_states(id) ON DELETE CASCADE,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'accepted', 'declined')),
    expires_at      TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(guild_id, invitee_game_id)
);

CREATE INDEX idx_guild_members_guild ON guild_members(guild_id);
CREATE INDEX idx_guild_invites_invitee ON guild_invites(invitee_game_id, status);

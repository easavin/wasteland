-- Migration 003: Chat system for shared world communication
-- chat_messages: global, zone, and guild chat

CREATE TABLE IF NOT EXISTS chat_messages (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    world_id        UUID NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    zone            INT,
    guild_id        UUID,
    sender_game_id  UUID NOT NULL REFERENCES game_states(id) ON DELETE CASCADE,
    player_id       UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    text            TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_chat_scope CHECK (
        (zone IS NULL AND guild_id IS NULL) OR
        (zone IS NOT NULL AND guild_id IS NULL) OR
        (zone IS NULL AND guild_id IS NOT NULL)
    )
);

CREATE INDEX idx_chat_world_created ON chat_messages(world_id, created_at DESC);
CREATE INDEX idx_chat_zone ON chat_messages(world_id, zone, created_at DESC) WHERE zone IS NOT NULL;
CREATE INDEX idx_chat_guild ON chat_messages(guild_id, created_at DESC) WHERE guild_id IS NOT NULL;

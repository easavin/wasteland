-- Migration 005: Trading / marketplace
-- trade_offers: marketplace and direct player-to-player trade

CREATE TABLE IF NOT EXISTS trade_offers (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    world_id        UUID NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    seller_game_id  UUID NOT NULL REFERENCES game_states(id) ON DELETE CASCADE,
    resource        VARCHAR(30) NOT NULL,
    amount          INT NOT NULL CHECK (amount > 0),
    price_gold      INT NOT NULL CHECK (price_gold >= 0),
    buyer_game_id   UUID REFERENCES game_states(id) ON DELETE SET NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'completed', 'cancelled')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

CREATE INDEX idx_trade_world_status ON trade_offers(world_id, status);
CREATE INDEX idx_trade_seller ON trade_offers(seller_game_id);
CREATE INDEX idx_trade_buyer ON trade_offers(buyer_game_id) WHERE buyer_game_id IS NOT NULL;

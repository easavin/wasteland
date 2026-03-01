-- Migration 007: Reset all users for new onboarding (display name + LLM moderation)
-- Deletes all players; CASCADE removes game_states, turn_history, payments, guilds,
-- guild_members, guild_invites, chat_messages, trade_offers, combat_challenges.
-- Keeps: worlds, admin_users. analytics_events kept with player_id=NULL.

DELETE FROM players;

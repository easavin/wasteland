"""Handler for /invite command — referral system using Telegram deep links."""

from __future__ import annotations

import logging
import uuid

from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from bot.db.queries.players import get_player_by_telegram_id
from bot.i18n import get_text

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# /invite command
# ---------------------------------------------------------------------------

async def handle_invite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/invite — show referral link and stats."""
    pool = context.bot_data["db_pool"]
    player = await get_player_by_telegram_id(pool, update.effective_user.id)
    if not player:
        await update.message.reply_text(get_text("free_text_no_game", "en"))
        return

    lang = player.get("language", "en")
    player_id = str(player["id"])

    # Get or generate referral code (use first 8 chars of player UUID)
    ref_code = player_id[:8]
    bot_username = (await context.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start=ref_{ref_code}"

    referral_count = player.get("referral_count", 0)

    if lang == "ru":
        text = (
            "👥 *Пригласи друзей!*\n\n"
            f"Твоя ссылка:\n`{invite_link}`\n\n"
            f"Приглашено: *{referral_count}* игроков\n\n"
            "За каждого нового игрока вы оба получите:\n"
            "  🔩 +50 scrap\n"
            "  💰 +10 gold\n"
            "  ✨ +100 XP"
        )
    else:
        text = (
            "👥 *Invite Friends!*\n\n"
            f"Your link:\n`{invite_link}`\n\n"
            f"Referred: *{referral_count}* players\n\n"
            "For each new player you both get:\n"
            "  🔩 +50 scrap\n"
            "  💰 +10 gold\n"
            "  ✨ +100 XP"
        )

    try:
        await update.message.reply_text(text, parse_mode="Markdown")
    except BadRequest:
        await update.message.reply_text(text)


# ---------------------------------------------------------------------------
# Referral processing (called from start handler)
# ---------------------------------------------------------------------------

async def process_referral(pool, new_player_id: str, ref_code: str) -> str | None:
    """Process a referral when a new player starts with ?start=ref_<code>.

    Returns the referrer player_id if successful, or None.
    """
    # Find the referrer by matching the first 8 chars of their player UUID
    row = await pool.fetchrow(
        """
        SELECT id FROM players
        WHERE CAST(id AS TEXT) LIKE $1 || '%'
          AND id != $2
        LIMIT 1
        """,
        ref_code, new_player_id,
    )
    if not row:
        return None

    referrer_id = str(row["id"])

    # Update referrer count
    await pool.execute(
        """
        UPDATE players
           SET referral_count = referral_count + 1,
               updated_at = NOW()
         WHERE id = $1
        """,
        referrer_id,
    )

    # Mark new player as referred
    await pool.execute(
        """
        UPDATE players
           SET referred_by = $1,
               updated_at = NOW()
         WHERE id = $2
        """,
        referrer_id, new_player_id,
    )

    # Award referral bonuses to both players' active games
    for pid in (referrer_id, new_player_id):
        game = await pool.fetchrow(
            "SELECT id, scrap, gold, xp FROM game_states WHERE player_id = $1 AND status = 'active'",
            pid,
        )
        if game:
            await pool.execute(
                """
                UPDATE game_states
                   SET scrap = scrap + 50,
                       gold = gold + 10,
                       xp = xp + 100,
                       updated_at = NOW()
                 WHERE id = $1
                """,
                str(game["id"]),
            )

    return referrer_id

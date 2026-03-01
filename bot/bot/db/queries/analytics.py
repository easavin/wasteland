"""Analytics event database queries."""

import json
import logging
from datetime import datetime

import asyncpg

logger = logging.getLogger(__name__)


async def log_event(
    pool: asyncpg.Pool,
    player_id: str | None,
    event_type: str,
    event_data: dict | None = None,
) -> None:
    """Insert a single analytics event.

    Args:
        player_id: The player's UUID, or ``None`` for system-level events.
        event_type: A short tag such as ``'game_started'`` or ``'turn_taken'``.
        event_data: Arbitrary JSON-serialisable payload.  Defaults to ``{}``.
    """
    await pool.execute(
        """
        INSERT INTO analytics_events (player_id, event_type, event_data)
        VALUES ($1, $2, $3::jsonb)
        """,
        player_id,
        event_type,
        json.dumps(event_data) if event_data is not None else "{}",
    )


async def get_events_since(
    pool: asyncpg.Pool,
    since_timestamp: datetime,
    event_type: str | None = None,
) -> list[dict]:
    """Return analytics events created after *since_timestamp*.

    Args:
        since_timestamp: Only events with ``created_at`` strictly after this
            value are returned.
        event_type: If provided, filter to this specific event type.

    Returns:
        A list of event dicts ordered by ``created_at`` ascending.
    """
    if event_type is not None:
        rows = await pool.fetch(
            """
            SELECT *
              FROM analytics_events
             WHERE created_at > $1
               AND event_type = $2
             ORDER BY created_at ASC
            """,
            since_timestamp,
            event_type,
        )
    else:
        rows = await pool.fetch(
            """
            SELECT *
              FROM analytics_events
             WHERE created_at > $1
             ORDER BY created_at ASC
            """,
            since_timestamp,
        )
    return [dict(r) for r in rows]

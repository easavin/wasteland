"""Async connection pool for Neon Postgres via asyncpg."""

import logging

import asyncpg

logger = logging.getLogger(__name__)


async def init_db_pool(database_url: str) -> asyncpg.Pool:
    """Create and return an asyncpg connection pool.

    Args:
        database_url: PostgreSQL connection string
            (e.g. ``postgresql://user:pass@host/db?sslmode=require``).

    Returns:
        An initialised :class:`asyncpg.Pool` ready for queries.
    """
    logger.info("Initialising database connection pool …")
    pool = await asyncpg.create_pool(
        dsn=database_url,
        # Lazy pool: open nothing at startup and close idle connections after
        # 60s, so an idle bot holds no connections. That lets Neon suspend and
        # keeps the container quiet enough for Railway App Sleeping.
        min_size=0,
        max_size=5,
        max_inactive_connection_lifetime=60,
        command_timeout=30,
        # Neon requires SSL; asyncpg respects the sslmode param in the DSN,
        # but we also set statement_cache_size=0 because Neon's connection
        # pooler (pgbouncer) does not support prepared statements.
        statement_cache_size=0,
    )
    logger.info("Database pool created (lazy, max=5)")
    return pool


async def close_db_pool(pool: asyncpg.Pool) -> None:
    """Gracefully close every connection in the pool.

    Args:
        pool: The pool returned by :func:`init_db_pool`.
    """
    if pool is None:
        return
    logger.info("Closing database connection pool …")
    await pool.close()
    logger.info("Database pool closed")

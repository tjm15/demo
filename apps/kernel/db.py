"""Database utilities for the kernel services.
Designed to degrade gracefully when DB client libraries are unavailable.
"""
import os
from contextlib import contextmanager
from typing import Iterator, Any

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://tpa:tpa@127.0.0.1:5432/tpa")


@contextmanager
def get_conn() -> Iterator[Any]:
    """Yield a psycopg connection with pgvector registered.

    If psycopg is not installed, raise RuntimeError so callers can
    fallback to fixture-based logic without import-time failures.
    """
    try:
        import psycopg  # type: ignore
        from pgvector.psycopg import register_vector  # type: ignore
    except Exception as e:
        raise RuntimeError("Database client not available") from e

    conn = psycopg.connect(DATABASE_URL)
    try:
        register_vector(conn)
        yield conn
    finally:
        conn.close()


def to_vector(values: list[float]) -> Any:
    """Convert list of floats to pgvector Vector for parameter binding.

    If pgvector is unavailable, return the original values. This is safe
    because code paths that require a DB connection will raise earlier,
    and fixture fallbacks will be used instead.
    """
    try:
        from pgvector.psycopg import Vector  # type: ignore
        return Vector(values)
    except Exception:
        return values


# Async pool support (optional). Use get_async_pool() to obtain an asyncpg pool
_async_pool = None


async def get_async_pool():
    """Create or return an existing asyncpg pool.

    This is lazy-initialized to avoid import-time overhead. Callers should
    `await get_async_pool()` and then `async with pool.acquire()` to run
    queries.
    """
    global _async_pool
    if _async_pool is not None:
        return _async_pool

    try:
        import asyncpg
    except Exception as e:
        raise RuntimeError("asyncpg is not installed") from e

    _async_pool = await asyncpg.create_pool(dsn=DATABASE_URL, min_size=1, max_size=10)
    return _async_pool


class AsyncAcquire:
    def __init__(self, pool):
        self._pool = pool

    async def __aenter__(self):
        self._conn = await self._pool.acquire()
        return self._conn

    async def __aexit__(self, exc_type, exc, tb):
        await self._pool.release(self._conn)


async def acquire_async_conn():
    """Helper to use with `async with acquire_async_conn()` to get a connection."""
    pool = await get_async_pool()
    return AsyncAcquire(pool)

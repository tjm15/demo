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

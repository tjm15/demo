"""Database utilities for the kernel services.
Uses psycopg (sync) with simple helper functions and pgvector adapter.
"""
import os
from contextlib import contextmanager
import psycopg
from pgvector.psycopg import register_vector, Vector

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://tpa:tpa@127.0.0.1:5432/tpa")

@contextmanager
def get_conn():
    conn = psycopg.connect(DATABASE_URL)
    try:
        # register pgvector type on this connection
        register_vector(conn)
        yield conn
    finally:
        conn.close()

def to_vector(values: list[float]) -> Vector:
    """Convert list of floats to pgvector Vector for parameter binding."""
    return Vector(values)

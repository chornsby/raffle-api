from pathlib import Path

import aiosql
import psycopg
import psycopg.rows
import psycopg_pool

from .config import Settings

migrations_path = Path(__file__).parent / "migrations"
migrations = aiosql.from_path(migrations_path, "psycopg")

queries_path = Path(__file__).parent / "queries"
queries = aiosql.from_path(queries_path, "psycopg")


GLOBAL_CONNECTION_SETTINGS = {
    "autocommit": True,
    "row_factory": psycopg.rows.namedtuple_row,
}


def create_pool(settings: Settings) -> psycopg_pool.ConnectionPool:
    """Return a connection pool used for the entire application lifecycle."""

    def configure(conn: psycopg.Connection):
        for attribute, value in GLOBAL_CONNECTION_SETTINGS.items():
            setattr(conn, attribute, value)

    return psycopg_pool.ConnectionPool(settings.db_url, configure=configure)


def create_connection(settings: Settings) -> psycopg.Connection:
    """Return an individual connection used for ad-hoc queries."""
    return psycopg.connect(settings.db_url, **GLOBAL_CONNECTION_SETTINGS)

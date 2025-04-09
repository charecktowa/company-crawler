"""
Database connection management with connection pooling.
"""

import sqlite3
import logging
from contextlib import contextmanager
from typing import Generator

from config import DATABASE_PATH

# Configure logging
logger = logging.getLogger(__name__)

# Create connection pool
connection_pool = {}


@contextmanager
def get_db_connection(
    db_path: str = DATABASE_PATH,
) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections to ensure proper resource handling.

    Args:
        db_path: Path to the SQLite database file.

    Yields:
        sqlite3.Connection: An active database connection.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()

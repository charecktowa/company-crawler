"""
Database schema definitions and data models.
"""

import sqlite3
import logging
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from db.connection import get_db_connection
from config import DATABASE_PATH

# Configure logging
logger = logging.getLogger(__name__)


class ScrapingStatus(Enum):
    """Enum for the status of scraping a company website."""

    NOT_SCRAPED = auto()
    SCRAPED = auto()
    EMPTY = auto()
    ERROR = auto()

    def __str__(self) -> str:
        return self.name


@dataclass
class Company:
    """Data model for a company."""

    ric: str
    company_name: str
    industry_type: str
    web_link: str
    status: ScrapingStatus = ScrapingStatus.NOT_SCRAPED


@dataclass
class ScrapedData:
    """Data model for scraped company data."""

    ric: str
    web_link: Optional[str] = None
    status: ScrapingStatus = ScrapingStatus.NOT_SCRAPED
    scraped_purpose: Optional[str] = None
    generated_purpose: Optional[str] = None
    paragraph: Optional[str] = None
    confidence: Optional[int] = None
    overview: Optional[str] = None
    focus: Optional[str] = None
    inference: Optional[str] = None


def initialize_database(db_path: str = DATABASE_PATH) -> None:
    """
    Initialize the database schema if it doesn't exist.

    Args:
        db_path: Path to the SQLite database file.
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()

            # Create companies table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS companies(
                    ric TEXT PRIMARY KEY NOT NULL UNIQUE,
                    company_name TEXT NOT NULL,
                    industry_type TEXT NOT NULL,
                    web_link TEXT,
                    status TEXT DEFAULT "NOT_SCRAPED"
                );
            """
            )

            # Create scraped_data table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS scraped_data(
                    ric TEXT PRIMARY KEY NOT NULL UNIQUE,
                    web_link TEXT,
                    status TEXT DEFAULT "NOT_SCRAPED",
                    scraped_purpose TEXT,
                    generated_purpose TEXT,
                    paragraph TEXT,
                    confidence INTEGER,
                    overview TEXT,
                    focus TEXT,
                    inference TEXT,
                    
                    FOREIGN KEY (ric) REFERENCES companies(ric),
                    FOREIGN KEY (web_link) REFERENCES companies(web_link),
                    FOREIGN KEY (status) REFERENCES companies(status)
                );
            """
            )

            conn.commit()
            logger.info("Database initialized successfully")

    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}")
        raise

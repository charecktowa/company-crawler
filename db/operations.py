"""
Database CRUD operations for companies and scraped data.
"""

import logging
from typing import List, Optional, Tuple, Dict, Any

from db.connection import get_db_connection
from db.models import Company, ScrapedData, ScrapingStatus
from config import DATABASE_PATH, BATCH_SIZE

# Configure logging
logger = logging.getLogger(__name__)


def insert_companies(companies: List[Tuple], db_path: str = DATABASE_PATH) -> int:
    """
    Insert multiple companies into the database.

    Args:
        companies: List of tuples with company data (ric, company_name, industry_type, web_link)
        db_path: Path to the SQLite database file

    Returns:
        int: Number of companies inserted
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.executemany(
                "INSERT INTO companies(ric, company_name, industry_type, web_link) VALUES (?, ?, ?, ?)",
                companies,
            )
            conn.commit()
            return cursor.rowcount
    except Exception as e:
        logger.error(f"Error inserting companies: {e}")
        raise


def get_pending_urls(
    limit: int = BATCH_SIZE, db_path: str = DATABASE_PATH
) -> List[str]:
    """
    Get a batch of URLs that haven't been scraped yet.

    Args:
        limit: Maximum number of URLs to retrieve
        db_path: Path to the SQLite database file

    Returns:
        List[str]: List of URLs to scrape
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT web_link FROM companies WHERE status = 'NOT_SCRAPED' LIMIT ?",
                (limit,),
            )
            results = cursor.fetchall()
            return [row["web_link"] for row in results if row["web_link"]]
    except Exception as e:
        logger.error(f"Error getting pending URLs: {e}")
        return []


def update_company_status(
    url: str, status: ScrapingStatus, db_path: str = DATABASE_PATH
) -> bool:
    """
    Update the scraping status of a company.

    Args:
        url: The URL of the company website
        status: The new scraping status
        db_path: Path to the SQLite database file

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE companies SET status = ? WHERE web_link = ?", (str(status), url)
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error updating company status: {e}")
        return False


def save_scraped_data(
    url: str,
    about_url: str,
    status: ScrapingStatus,
    purpose_data: Optional[Dict[str, Any]] = None,
    db_path: str = DATABASE_PATH,
) -> bool:
    """
    Save scraped data for a company.

    Args:
        url: The original URL of the company website
        about_url: The URL of the about page
        status: The scraping status
        purpose_data: Dict containing parsed purpose data
        db_path: Path to the SQLite database file

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()

            # First, update the company status
            update_company_status(url, status, db_path)

            # Get the RIC for this company
            cursor.execute("SELECT ric FROM companies WHERE web_link = ?", (url,))
            result = cursor.fetchone()
            if not result:
                logger.error(f"No company found for URL: {url}")
                return False

            ric = result["ric"]

            # Prepare purpose data if available
            purpose = None
            paragraph = None
            confidence = None
            overview = None
            focus = None
            inference = None

            if purpose_data:
                purpose = purpose_data.get("purpose")
                paragraph = purpose_data.get("paragraph")
                confidence = purpose_data.get("confidence")
                overview = purpose_data.get("overview")
                focus = purpose_data.get("focus")
                inference = purpose_data.get("inference")

            # Insert or update scraped data
            cursor.execute(
                """
                INSERT INTO scraped_data 
                (ric, web_link, status, scraped_purpose, paragraph, confidence, overview, focus, inference) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ric) DO UPDATE SET
                    web_link = excluded.web_link,
                    status = excluded.status,
                    scraped_purpose = excluded.scraped_purpose,
                    paragraph = excluded.paragraph,
                    confidence = excluded.confidence,
                    overview = excluded.overview,
                    focus = excluded.focus,
                    inference = excluded.inference
            """,
                (
                    ric,
                    about_url,
                    str(status),
                    purpose,
                    paragraph,
                    confidence,
                    overview,
                    focus,
                    inference,
                ),
            )

            conn.commit()
            return True

    except Exception as e:
        logger.error(f"Error saving scraped data: {e}")
        return False


def get_company_status(
    url: str, db_path: str = DATABASE_PATH
) -> Optional[ScrapingStatus]:
    """
    Get the scraping status of a company.

    Args:
        url: The URL of the company website
        db_path: Path to the SQLite database file

    Returns:
        Optional[ScrapingStatus]: The scraping status, or None if not found
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM companies WHERE web_link = ?", (url,))
            result = cursor.fetchone()
            if result:
                return ScrapingStatus[result["status"]]
            return None
    except Exception as e:
        logger.error(f"Error getting company status: {e}")
        return None


def count_companies_by_status(
    db_path: str = DATABASE_PATH,
) -> Dict[ScrapingStatus, int]:
    """
    Count companies by their scraping status.

    Args:
        db_path: Path to the SQLite database file

    Returns:
        Dict[ScrapingStatus, int]: Dictionary mapping status to count
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT status, COUNT(*) as count FROM companies GROUP BY status"
            )
            results = cursor.fetchall()
            return {ScrapingStatus[row["status"]]: row["count"] for row in results}
    except Exception as e:
        logger.error(f"Error counting companies by status: {e}")
        return {}

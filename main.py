"""
Main entry point for the company purpose scraper.
"""

import argparse
import logging
import os
import sys
import time
from typing import Optional

from db.models import initialize_database
from db.operations import insert_companies, count_companies_by_status
from scraper.worker import run_parallel_workers
from utils.data_loader import load_company_data
from utils.logging import setup_logging
from config import DATABASE_PATH, NUM_WORKERS

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


def load_data(xlsx_path: str) -> bool:
    """
    Load company data from Excel file and insert into database.

    Args:
        xlsx_path: Path to the Excel file

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Load company data from Excel
        company_data = load_company_data(xlsx_path)

        # Insert companies into database
        num_inserted = insert_companies(company_data)

        logger.info(f"Inserted {num_inserted} companies into database")
        return True

    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return False


def run_scraper(
    num_workers: int = NUM_WORKERS,
    max_batches: Optional[int] = None,
    resume: bool = True,
) -> None:
    """
    Run the scraper with the specified number of workers.

    Args:
        num_workers: Number of parallel workers
        max_batches: Maximum number of batches per worker
        resume: Whether to resume scraping or start fresh
    """
    try:
        logger.info(f"Starting scraper with {num_workers} workers")

        # Display initial status
        status_counts = count_companies_by_status()
        logger.info(f"Initial status: {status_counts}")

        # Run workers
        start_time = time.time()
        run_parallel_workers(num_workers, max_batches)
        end_time = time.time()

        # Display final status
        status_counts = count_companies_by_status()
        logger.info(f"Final status: {status_counts}")

        # Print statistics
        elapsed_time = end_time - start_time
        logger.info(f"Scraping completed in {elapsed_time:.2f} seconds")

    except Exception as e:
        logger.error(f"Error running scraper: {e}")


def main() -> int:
    """
    Main entry point.

    Returns:
        int: Exit code (0 for success, non-zero for error)
    """
    parser = argparse.ArgumentParser(description="Company Purpose Scraper")

    parser.add_argument(
        "--xlsx", type=str, help="Path to Excel file with company data", default=None
    )

    parser.add_argument(
        "--num-workers",
        type=int,
        help="Number of parallel workers",
        default=NUM_WORKERS,
    )

    parser.add_argument(
        "--max-batches",
        type=int,
        help="Maximum number of batches per worker",
        default=None,
    )

    parser.add_argument(
        "--resume", action="store_true", help="Resume scraping from previous state"
    )

    parser.add_argument(
        "--db-path",
        type=str,
        help="Path to the SQLite database file",
        default=DATABASE_PATH,
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Update logging level if debug is enabled
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Initialize database
        logger.info(f"Using database at {args.db_path}")
        os.environ["DATABASE_PATH"] = args.db_path
        initialize_database(args.db_path)

        # Load data if Excel file is provided
        if args.xlsx:
            if not load_data(args.xlsx):
                logger.error("Failed to load data from Excel file")
                return 1

        # Run scraper
        run_scraper(args.num_workers, args.max_batches, args.resume)

        return 0

    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

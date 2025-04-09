"""
Worker implementation for parallel processing of company websites.
"""

import logging
import time
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from db.models import ScrapingStatus
from db.operations import (
    get_pending_urls,
    update_company_status,
    save_scraped_data,
    get_company_status,
)
from scraper.url_finder import URLFinder
from scraper.content_parser import ContentParser
from llm.client import LLMClient
from config import NUM_WORKERS

# Configure logging
logger = logging.getLogger(__name__)


class ScraperWorker:
    """Worker for scraping company websites in parallel."""

    def __init__(self):
        """Initialize the worker."""
        self.url_finder = URLFinder()
        self.content_parser = ContentParser()
        self.llm_client = LLMClient()

    def process_url(self, url: str) -> Dict[str, Any]:
        """
        Process a single URL.

        Args:
            url: URL to process

        Returns:
            Dict[str, Any]: Processing result
        """
        logger.info(f"Processing URL: {url}")
        result = {
            "url": url,
            "status": ScrapingStatus.ERROR,
            "about_url": None,
            "purpose_data": None,
        }

        try:
            # Skip if already processed
            current_status = get_company_status(url)
            if current_status in [
                ScrapingStatus.SCRAPED,
                ScrapingStatus.ERROR,
                ScrapingStatus.EMPTY,
            ]:
                logger.info(
                    f"URL already processed with status {current_status}: {url}"
                )
                result["status"] = current_status
                return result

            # Find about page
            about_url = self.url_finder.find_about_page(url)

            if not about_url:
                logger.warning(f"No about page found for {url}")
                result["status"] = ScrapingStatus.EMPTY
                return result

            # Parse about page
            parse_result = self.content_parser.fetch_and_parse(about_url)

            if not parse_result["success"]:
                logger.error(f"Error parsing {about_url}: {parse_result['error']}")
                result["status"] = ScrapingStatus.ERROR
                return result

            result["about_url"] = about_url

            # Use LLM to extract purpose if text was found
            if parse_result["text"]:
                purpose_data = self.llm_client.extract_purpose(
                    url=about_url, text=parse_result["text"]
                )

                if purpose_data:
                    result["purpose_data"] = purpose_data
                    result["status"] = ScrapingStatus.SCRAPED
                else:
                    logger.warning(f"No purpose extracted for {about_url}")
                    result["status"] = (
                        ScrapingStatus.SCRAPED
                    )  # We still scraped, even if no purpose was found

            return result

        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            return result

    def save_result(self, result: Dict[str, Any]) -> None:
        """
        Save processing result to database.

        Args:
            result: Processing result
        """
        url = result["url"]
        about_url = result["about_url"] or ""
        status = result["status"]
        purpose_data = result["purpose_data"]

        save_scraped_data(url, about_url, status, purpose_data)

    def process_batch(self, urls: List[str]) -> None:
        """
        Process a batch of URLs.

        Args:
            urls: List of URLs to process
        """
        for url in urls:
            result = self.process_url(url)
            self.save_result(result)

    def run(self, max_batches: Optional[int] = None) -> None:
        """
        Run the worker to process URL batches.

        Args:
            max_batches: Maximum number of batches to process, or None for unlimited
        """
        batch_count = 0

        while max_batches is None or batch_count < max_batches:
            urls = get_pending_urls()

            if not urls:
                logger.info("No more URLs to process")
                break

            logger.info(f"Processing batch {batch_count + 1} with {len(urls)} URLs")
            self.process_batch(urls)

            batch_count += 1


def run_parallel_workers(
    num_workers: int = NUM_WORKERS, max_batches_per_worker: Optional[int] = None
) -> None:
    """
    Run multiple scraper workers in parallel.

    Args:
        num_workers: Number of workers to run in parallel
        max_batches_per_worker: Maximum number of batches per worker, or None for unlimited
    """
    logger.info(f"Starting {num_workers} parallel workers")

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        workers = [ScraperWorker() for _ in range(num_workers)]
        futures = [
            executor.submit(worker.run, max_batches_per_worker) for worker in workers
        ]

        for future in futures:
            future.result()

    logger.info("All workers completed")

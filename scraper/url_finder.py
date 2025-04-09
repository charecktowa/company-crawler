"""
URL finder for about pages.
"""

import logging
import random
import time
from urllib.parse import urljoin, urlparse
from typing import List, Optional, Set, Tuple

import requests
from bs4 import BeautifulSoup

from config import (
    USER_AGENTS,
    ABOUT_PAGE_KEYWORDS,
    REQUEST_TIMEOUT,
    REQUEST_DELAY,
    MAX_DEPTH,
    MAX_RETRIES,
)

# Configure logging
logger = logging.getLogger(__name__)


class URLFinder:
    """Finds about pages on company websites."""

    def __init__(self, max_depth: int = MAX_DEPTH):
        """
        Initialize the URL finder.

        Args:
            max_depth: Maximum depth for crawling
        """
        self.max_depth = max_depth
        self.visited_urls: Set[str] = set()
        self.domain_last_request = {}

    def _get_random_user_agent(self) -> str:
        """Get a random user agent from the list."""
        return random.choice(USER_AGENTS)

    def _request_with_rate_limiting(self, url: str) -> Optional[requests.Response]:
        """
        Make an HTTP request with rate limiting.

        Args:
            url: URL to request

        Returns:
            Optional[requests.Response]: Response object or None if error
        """
        # Parse domain for rate limiting
        domain = urlparse(url).netloc

        # Respect rate limits per domain
        current_time = time.time()
        if domain in self.domain_last_request:
            time_since_last_request = current_time - self.domain_last_request[domain]
            if time_since_last_request < REQUEST_DELAY:
                time.sleep(REQUEST_DELAY - time_since_last_request)

        # Make the request with retries
        headers = {"User-Agent": self._get_random_user_agent()}
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                self.domain_last_request[domain] = time.time()
                return response
            except requests.RequestException as e:
                logger.warning(
                    f"Request attempt {attempt+1}/{MAX_RETRIES} failed for {url}: {e}"
                )
                if attempt < MAX_RETRIES - 1:
                    time.sleep(1 * (attempt + 1))  # Exponential backoff
                else:
                    logger.error(f"All request attempts failed for {url}")
                    return None

    def _is_about_page(self, url: str) -> bool:
        """
        Check if a URL is likely an about page.

        Args:
            url: URL to check

        Returns:
            bool: True if the URL is likely an about page
        """
        path = urlparse(url).path.lower()
        return any(keyword in path for keyword in ABOUT_PAGE_KEYWORDS)

    def _extract_links(self, url: str, html: str) -> List[str]:
        """
        Extract links from HTML.

        Args:
            url: Base URL for resolving relative links
            html: HTML content

        Returns:
            List[str]: List of absolute URLs
        """
        links = []
        base_domain = urlparse(url).netloc

        try:
            soup = BeautifulSoup(html, "html.parser")
            for a_tag in soup.find_all("a", href=True):
                href = a_tag.get("href", "").strip()
                if not href or href.startswith(("javascript:", "mailto:", "tel:")):
                    continue

                absolute_url = urljoin(url, href)
                parsed_url = urlparse(absolute_url)

                # Skip fragment identifiers and queries for the same page
                if not parsed_url.path and (parsed_url.fragment or parsed_url.query):
                    continue

                # Only include links to the same domain
                if parsed_url.netloc == base_domain:
                    # Normalize URL by removing fragments
                    normalized_url = parsed_url._replace(fragment="").geturl()
                    links.append(normalized_url)

        except Exception as e:
            logger.error(f"Error extracting links from {url}: {e}")

        return links

    def _prioritize_about_links(self, links: List[str]) -> List[str]:
        """
        Prioritize links that are likely about pages.

        Args:
            links: List of URLs

        Returns:
            List[str]: Prioritized list of URLs
        """
        about_links = []
        other_links = []

        for link in links:
            if self._is_about_page(link):
                about_links.append(link)
            else:
                other_links.append(link)

        # Sort about links by simplicity (shorter paths first)
        about_links.sort(key=lambda u: len(urlparse(u).path.split("/")))

        return about_links + other_links

    def find_about_page(self, url: str) -> Optional[str]:
        """
        Find an about page on a company website.

        Args:
            url: Base URL of the company website

        Returns:
            Optional[str]: URL of the about page, or None if not found
        """
        # Normalize URL by removing trailing slash
        url = url.rstrip("/")

        # Reset visited URLs for this search
        self.visited_urls = set()

        # Queue for BFS traversal (URL, depth)
        queue: List[Tuple[str, int]] = [(url, 0)]

        while queue:
            current_url, depth = queue.pop(0)

            if current_url in self.visited_urls or depth > self.max_depth:
                continue

            logger.debug(f"Checking URL: {current_url} (depth {depth})")
            self.visited_urls.add(current_url)

            # Make the request
            response = self._request_with_rate_limiting(current_url)
            if not response:
                continue

            # Check if this page is an about page
            if self._is_about_page(current_url):
                logger.info(f"Found about page: {current_url}")
                return current_url

            # If we've reached max depth, don't add more links
            if depth >= self.max_depth:
                continue

            # Extract and prioritize links
            links = self._extract_links(current_url, response.text)
            prioritized_links = self._prioritize_about_links(links)

            # Add unvisited links to queue
            for link in prioritized_links:
                if link not in self.visited_urls:
                    queue.append((link, depth + 1))

        logger.warning(f"No about page found for {url}")
        return None

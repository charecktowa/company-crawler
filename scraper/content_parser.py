"""
Content parser for extracting company purpose statements.
"""

import logging
import re
import random
from typing import Dict, Optional, Union

import requests
from bs4 import BeautifulSoup

from config import USER_AGENTS, PURPOSE_PHRASES, REQUEST_TIMEOUT

# Configure logging
logger = logging.getLogger(__name__)


class ContentParser:
    """Parser for extracting company purpose statements from web pages."""

    @staticmethod
    def _get_random_user_agent() -> str:
        """Get a random user agent from the list."""
        return random.choice(USER_AGENTS)

    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Clean text by removing extra whitespace, control characters, etc.

        Args:
            text: Raw text to clean

        Returns:
            str: Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove non-printable characters
        text = re.sub(r"[^\x20-\x7E\u00A0-\u00FF]", " ", text)

        # Convert to lowercase
        text = text.lower()

        return text.strip()

    def _extract_purpose_paragraph(self, text: str) -> Optional[str]:
        """
        Extract a paragraph containing purpose statement.

        Args:
            text: Cleaned text to search

        Returns:
            Optional[str]: Paragraph containing purpose statement, or None if not found
        """
        # Split text into paragraphs
        paragraphs = re.split(r"\n+|\. ", text)

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # Check if paragraph contains a purpose phrase
            if any(phrase in paragraph for phrase in PURPOSE_PHRASES):
                # Ensure paragraph is a complete sentence
                if not paragraph.endswith("."):
                    paragraph += "."
                return paragraph

        return None

    def fetch_and_parse(self, url: str) -> Dict[str, Union[str, None]]:
        """
        Fetch and parse a web page to extract company purpose.

        Args:
            url: URL to fetch and parse

        Returns:
            Dict: Dictionary with extracted content
        """
        result = {
            "url": url,
            "text": None,
            "purpose_paragraph": None,
            "success": False,
            "error": None,
        }

        try:
            # Make the request
            headers = {"User-Agent": self._get_random_user_agent()}
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract text from HTML
            text = soup.get_text(separator=" ")
            cleaned_text = self._clean_text(text)

            # Extract purpose paragraph
            purpose_paragraph = self._extract_purpose_paragraph(cleaned_text)

            result.update(
                {
                    "text": cleaned_text,
                    "purpose_paragraph": purpose_paragraph,
                    "success": True,
                }
            )

        except Exception as e:
            logger.error(f"Error parsing {url}: {e}")
            result["error"] = str(e)

        return result

"""
Configuration settings for the company purpose scraper application.
"""

import os
from typing import List

# Database settings
DATABASE_PATH = os.environ.get("DATABASE_PATH", "./data/database.db")

# Scraper settings
USER_AGENTS: List[str] = [
    # Windows 11 User-Agents
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edg/131.0.2903.86 Safari/537.36",
    # macOS with M1 Chip User-Agents
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_2; rv:134.0) Gecko/20100101 Firefox/134.0",
    # Linux User-Agents
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Vivaldi/7.0.3495.29 Safari/537.36",
]

# HTTP request settings
REQUEST_TIMEOUT = 15  # seconds
REQUEST_DELAY = 0.5  # seconds between requests to the same domain
MAX_DEPTH = 2  # maximum depth for web crawling
MAX_RETRIES = 3  # maximum number of retries for failed requests

# About page detection settings
ABOUT_PAGE_KEYWORDS = [
    "about",
    "who-we-are",
    "acerca",
    "information",
    "sobre",
    "our",
    "informacion",
    "who",
    "quienes",
    "about-us",
    "aboutus",
    "about_us",
    "quienes-somos",
]

# Purpose text detection patterns
PURPOSE_PHRASES = [
    "our purpose",
    "nuestro propósito",
    "our purpose is",
    "nuestro propósito es",
    "company purpose",
    "corporate purpose",
]

# LLM settings
LLM_API_KEY = os.environ.get("LLM_API_KEY", "sk-cd938bc8f65e4b62913978d38a87452f")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com")
LLM_MODEL = os.environ.get("LLM_MODEL", "deepseek-reasoner")
LLM_TEMPERATURE = 1.0
LLM_MAX_TOKENS = 1000
LLM_PROMPT_TEMPLATE_PATH = "prompt.txt"

# Parallel processing settings
NUM_WORKERS = 5  # Number of parallel workers
BATCH_SIZE = 10  # Number of URLs to process in a batch

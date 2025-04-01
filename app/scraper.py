import re
from time import sleep
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from db import get_link_from_db, save_to_db, get_data_status

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
REQUEST_DELAY = 0
HTML_PARSER = "html.parser"

# TODO: if scraped, don't scrape again. If url is empty pass
# TODO: Add logging properly


def load_by_batch_in_memory(batch_size: int = 10):
    data = get_link_from_db()
    for i in range(0, len(data), batch_size):
        yield data[i : i + batch_size]


def is_about_url(url):
    """
    Return True if the path of the URL contains any of these keywords:
    "about", "acerca", "sobre", "our".
    This is a more relaxed check than looking for an exact "/about" path.
    """
    path = urlparse(url).path.lower()

    # We simply check if any of the keywords is contained anywhere in the path
    keywords = ["about", "acerca", "sobre", "our", "information", "informacion"]
    return any(kw in path for kw in keywords)


def find_about_page(base_url: str) -> str:
    try:
        response = requests.get(
            base_url,
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, HTML_PARSER)

        for link in soup.find_all("a", href=True):
            absolute_url = urljoin(base_url, link["href"])
            if is_about_url(absolute_url):
                return absolute_url

    except Exception as e:
        print(f"Error checking homepage: {e}")
        return "ERROR"


def add_internal_links_to_queue(url, start_url, queue, depth):
    """Add internal links to the queue for further crawling"""
    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, HTML_PARSER)
        for link in soup.find_all("a", href=True):
            absolute_url = urljoin(url, link["href"])
            parsed = urlparse(absolute_url)
            if parsed.netloc == urlparse(start_url).netloc:
                queue.append((absolute_url, depth + 1))
    except Exception as e:
        print(f"Error adding links from {url}: {e}")
        return "ERROR"


def check_about_text(url: str) -> bool:
    """Check if the page contains about text"""
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, HTML_PARSER)
        text = soup.get_text().lower()
        if any(
            kw in text for kw in ["about us", "acerca de", "quiénes somos", "sobre"]
        ):
            return True
    except Exception as e:
        print(f"Error checking {url}: {e}")
    return False


def extract_site_info(base_url: str) -> str:
    """Crawl site to find first page containing about text"""
    visited = set()
    queue = [(base_url, 0)]

    while queue:
        url, depth = queue.pop(0)

        if url in visited or depth > 1:
            continue

        visited.add(url)

        if check_about_text(url):
            return url

        if depth < 1:
            add_internal_links_to_queue(url, base_url, queue, depth)

        # sleep(REQUEST_DELAY)

    return "EMPTY"


def check_if_scraped(url: str) -> bool:
    return get_data_status(url) == "SCRAPED"


def scrape(url: str) -> None:
    # Scrape the site
    about_page = find_about_page(url)

    if not about_page:
        # If no direct about page found, try deeper scanning
        about_page = extract_site_info(url)

    if about_page == "EMPTY":
        status = "EMPTY"
    elif about_page == "ERROR":
        status = "ERROR"
    else:
        status = "SCRAPED"

    # Save your result to the database
    save_to_db(url, about_page, status=status)

    print(f"About page for {url} found in: {about_page}")


def scrape_sites(batch_size: int = 10) -> None:
    for chunk in load_by_batch_in_memory(batch_size=batch_size):
        for url in chunk:
            url = url[0]

            if check_if_scraped(url):
                print(f"Already scraped: {url}")
                continue

            scrape(url)


if __name__ == "__main__":
    scrape_sites(batch_size=5)  # Call the scrape function with batch_size

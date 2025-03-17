import re
from time import sleep
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from db import get_link_from_db

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
REQUEST_DELAY = 1  # Seconds between requests


def load_by_batch_in_memory(batch_size: int = 10):
    data = get_link_from_db()
    for i in range(0, len(data), batch_size):
        yield data[i : i + batch_size]


def is_about_url(url):
    """Check if URL path matches common about page patterns"""
    path = urlparse(url).path.lower()
    return re.search(r"/(about|acerca)([-_](us|de))?/?$", path)


def find_about_page(base_url: str) -> str:
    try:
        response = requests.get(base_url, headers={"User-Agent": USER_AGENT})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        for link in soup.find_all("a", href=True):
            absolute_url = urljoin(base_url, link["href"])
            if is_about_url(absolute_url):
                return absolute_url

    except Exception as e:
        print(f"Error checking homepage: {e}")
        return ""


def scrape(link: str) -> None:
    # Scrape the site
    about_page = find_about_page(link)

    if about_page:
        print(f"Found about page: {about_page}")

    else:
        print(f"No about page found for {link}")

        # Here we try to scrape the whole site to find a page
        # "mentioning something like 'Our purpose"


def scrape_sites(batch_size: int = 10) -> None:
    for chunk in load_by_batch_in_memory(batch_size=batch_size):
        for url in chunk:
            url = url[0]
            scrape(url)
            sleep(REQUEST_DELAY)


if __name__ == "__main__":
    scrape_sites(batch_size=5)  # Call the scrape function with batch_size

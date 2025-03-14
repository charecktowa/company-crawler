import re

import requests
from bs4 import BeautifulSoup

# Since we are trying to scrape the company's purpose from their website
# many websites have their purpose statement in their "About Us" page or similar
# so if the website /about_us or similar exist we try to scrape the purpose from there
ABOUT_US_url = ["about", "about_us", "acerca", "acerca_de"]

ABOUT_KEYWORDS = [
    "about",
    "about us",
    "about the company",
    "qui sommes nous",
    "sobre",
    "sobre nosotros",
    "über uns",
    "chi siamo",
    "over ons",
    "historia",
    "empresa",
    "company",
]

# Regex pattern for "purpose" phrases (case-insensitive)
PURPOSE_PATTERN = re.compile(
    r"\b(our purpose|purpose|nuestro propósito|propósito|notre raison d'être|"
    r"objetivo|razón de ser|visión|mission|why we exist|misión|raison d'être)\b",
    flags=re.IGNORECASE,
)


def check_about_exist(url):
    for keyword in ABOUT_US_url:
        if keyword in url:
            return True
    return False


def scrape_purpose(url: str):
    if check_about_exist(url):
        pass
    else:
        # In case it doesn't have an about us page, we will perfom web crawling and search for an about us text
        return "About Us page not found"

import json
import random
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from db import get_data_status, get_link_from_db, save_to_db, update_purpose
from openai import OpenAI

USER_AGENTS: list[str] = [
    # Windows 11 User-Agents
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",  # Chrome on Windows 11
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",  # Firefox on Windows 11
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edg/131.0.2903.86 Safari/537.36",  # Edge on Windows 11
    # macOS with M1 Chip User-Agents
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",  # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",  # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_2; rv:134.0) Gecko/20100101 Firefox/134.0",  # Firefox on macOS
    # Linux User-Agents
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",  # Chrome on Linux
    "Mozilla/5.0 (X11; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0",  # Firefox on Linux
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0",  # Firefox on Ubuntu
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Vivaldi/7.0.3495.29 Safari/537.36",  # Vivaldi on Linux
]


def load_by_batch_in_memory(batch_size: int = 10):
    data = get_link_from_db()
    for i in range(0, len(data), batch_size):
        yield data[i : i + batch_size]


def check_if_scraped(url: str) -> bool:
    return get_data_status(url) == "SCRAPED"


def get_all_urls(url: str, user_agent: str) -> list:
    """Fetch all links from the given URL and return them as a list"""
    try:
        response = requests.get(url, headers={"User-Agent": user_agent})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        return [link["href"] for link in soup.find_all("a") if "href" in link.attrs]
    except Exception as e:
        print(f"Error fetching links from {url}: {e}")
        return []


def is_about_url(url):
    """Check if URL path contains about-related keywords"""
    path = urlparse(url).path.lower()

    # TODO: Sort by language and add more keywords
    keywords = [
        "about",
        "who-we-are",
        "acerca",
        "information",
        "sobre",
        "our",
        "informacion",
        "who",
        "quienes",
    ]
    return any(kw in path for kw in keywords)


def find_about_page(links: list[str]) -> list[str]:
    """Find links containing about-like pages using is_about_url"""
    about_links = set()
    for link in links:
        if is_about_url(link):
            about_links.add(link)
    return list(about_links)


def prioritize_about_pages(url: str, about_links: list[str]) -> list[str]:
    """Convert to full URLs, group by base path, and select the best URL from each group"""
    # Convert to full URLs and group by base path
    full_urls = [urljoin(url, link) for link in about_links]
    groups = {}
    for u in full_urls:
        parsed = urlparse(u)
        base_url = parsed._replace(fragment="", query="").geturl()
        groups.setdefault(base_url, []).append(u)

    # Select best URL from each group (prioritize no fragment/query)
    selected_urls = []
    for base_url, urls in groups.items():
        urls_sorted = sorted(
            urls, key=lambda x: (bool(urlparse(x).fragment or urlparse(x).query), x)
        )
        selected_urls.append(urls_sorted[0])

    # Sort by path depth and simplicity
    selected_urls.sort(
        key=lambda u: (
            len(urlparse(u).path.strip("/").split("/")),  # Fewer path components first
            bool(
                urlparse(u).fragment or urlparse(u).query
            ),  # Prefer no fragments/queries
        )
    )

    return selected_urls


def process_text(text: str) -> str:
    """Preprocess text for better chatbot input"""
    # Remove extra whitespaces, remove weird characters, remove newlines and tabs (we are going to send the text to chatgpt)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\x00-\x7F]+", " ", text)
    text = text.replace("\n", " ").replace("\t", " ")
    text = text.lower()
    return text.strip()


def get_text_from_url(urls: list[str]) -> str | tuple[str, str]:
    texts = []
    for u in urls:
        response = requests.get(u, headers={"User-Agent": random.choice(USER_AGENTS)})
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text().strip()
        text = process_text(text)

        # Check if the text contains a purpose statement
        phrases = [
            "Our purpose",
            "Nuestro propósito",
            "Our purpose is",
            "Nuestro propósito es",
        ]

        if any(phrase.lower() in text.lower() for phrase in phrases):
            return u, text

        texts.append(text)
    return " ".join(texts)


def scrape(url: str, user_agent: str) -> tuple[str, str] | str | None:
    try:
        url = url.rstrip("/")
        urls = get_all_urls(url, user_agent)
        about_pages = find_about_page(urls)

        if not about_pages:
            return None

        selected_url = prioritize_about_pages(url, about_pages)

        result = get_text_from_url(selected_url)

        if isinstance(result, tuple):
            return result

        return about_pages[0], result
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return "ERROR"


# Configure the DeepSeek client
client = OpenAI(
    api_key="sk-cd938bc8f65e4b62913978d38a87452f",  # Consider using os.getenv for production
    base_url="https://api.deepseek.com",
)


def load_prompt_template(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def send_to_llm(url: str, text: str) -> str | None:
    prompt_template = load_prompt_template("prompt.txt")
    prompt = prompt_template.format(url=url, text=text[:600])

    try:
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            temperature=1.0,
            messages=[
                {
                    "role": "system",
                    "content": "You are a cautious assistant extracting company purposes.",
                },
                {"role": "user", "content": prompt},
            ],
            stream=False,
        )

        result = response.choices[0].message.content
        return result
    except Exception as e:
        print(f"Error sending to LLM: {e}")
        return None


def scrape_sites(batch_size: int = 10) -> None:
    for chunk in load_by_batch_in_memory(batch_size):
        user_agent = random.choice(USER_AGENTS)
        for url_tuple in chunk:
            url = url_tuple[0]

            if check_if_scraped(url):
                print(f"Already scraped: {url}")
                continue

            if not url or url in ["ERROR", "EMPTY", "NULL"]:
                print(f"Invalid URL: {url}")
                continue

            result = scrape(url, user_agent)

            if result is None:
                save_to_db(url, "", "EMPTY")
            elif result == "ERROR":
                save_to_db(url, "", "ERROR")
            else:
                about_url, text = result
                save_to_db(url, about_url, "SCRAPED")

                deepseek_result = send_to_llm(url, text)

                text = json.loads(
                    deepseek_result.strip("```json").strip().lstrip("#").strip()
                )

                # Split it for saving into variables and then into the database
                purpose = text["purpose"]
                paragraph = text["paragraph"]
                confidence = text["confidence"]
                overview = text["overview"]
                focus = text["focus"]
                inference = text["inference"]

                update_purpose(
                    url,
                    purpose,
                    paragraph,
                    confidence,
                    overview,
                    focus,
                    inference,
                )

            break

    print("End")


if __name__ == "__main__":
    # For not loading all at once (I think it is useless)
    scrape_sites(1)

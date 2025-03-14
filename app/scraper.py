from bs4 import BeautifulSoup
import requests


def scrape_title(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.title.string
    return title


if __name__ == "__main__":
    url = "https://example.com"
    print(f"Title of the page: {scrape_title(url)}")

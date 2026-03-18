from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://quotes.toscrape.com/"
DEFAULT_TIMEOUT = 10
HEADERS = {
    "User-Agent": "COMP3011-Coursework-Search-Tool/1.0"
}


def fetch_page(url: str = BASE_URL) -> Optional[str]:
    """Fetch one page and return its HTML, or None if the request fails."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as exc:
        print(f"Error fetching page: {url}")
        print(f"Reason: {exc}")
        return None


def parse_html(html: str) -> BeautifulSoup:
    """Parse raw HTML into a BeautifulSoup object."""
    return BeautifulSoup(html, "html.parser")


def extract_quote_texts(soup: BeautifulSoup) -> list[str]:
    """Extract the visible quote text from a Quotes to Scrape page."""
    quotes: list[str] = []

    for quote_tag in soup.select("div.quote span.text"):
        text = quote_tag.get_text(strip=True)
        if text:
            quotes.append(text)

    return quotes


def extract_page_title(soup: BeautifulSoup) -> str:
    """Extract the page title, or an empty string if missing."""
    if soup.title is None:
        return ""

    return soup.title.get_text(strip=True)


def find_next_page_url(soup: BeautifulSoup, current_url: str = BASE_URL) -> Optional[str]:
    """Return the absolute URL of the next page, if one exists."""
    next_link = soup.select_one("li.next a")

    if next_link is None:
        return None

    href = next_link.get("href")
    if not href:
        return None

    return urljoin(current_url, href)


def scrape_single_page(url: str = BASE_URL) -> Optional[dict]:
    """Fetch and parse one page, returning the key data needed by the crawler."""
    html = fetch_page(url)
    if html is None:
        return None

    soup = parse_html(html)

    return {
        "url": url,
        "title": extract_page_title(soup),
        "quotes": extract_quote_texts(soup),
        "next_page_url": find_next_page_url(soup, url),
    }
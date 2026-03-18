import re
import time
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from indexer import InvertedIndex

BASE_URL = "https://quotes.toscrape.com/"
DEFAULT_TIMEOUT = 10
POLITENESS_DELAY = 6
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


def tokenize_text(text: str) -> list[str]:
    """Convert text into lowercase tokens ready for indexing."""
    return re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)?", text.lower())


def build_page_tokens(quote_texts: list[str]) -> list[str]:
    """Combine all quote text from one page into a single token list."""
    tokens: list[str] = []

    for quote in quote_texts:
        tokens.extend(tokenize_text(quote))

    return tokens


def add_page_to_index(
    index: InvertedIndex,
    doc_id: str,
    url: str,
    title: str,
    quote_texts: list[str],
) -> None:
    """Add one crawled page into the existing InvertedIndex."""
    tokens = build_page_tokens(quote_texts)
    index.index_tokens(doc_id=doc_id, url=url, tokens=tokens, title=title)


def crawl_all_pages(
    start_url: str = BASE_URL,
    politeness_delay: int = POLITENESS_DELAY,
) -> InvertedIndex:
    """Crawl all quote pages starting from the given URL and build an InvertedIndex."""
    index = InvertedIndex()
    visited_urls: set[str] = set()
    current_url: Optional[str] = start_url
    page_number = 1
    last_request_time: Optional[float] = None

    while current_url is not None:
        if current_url in visited_urls:
            print(f"Skipping duplicate URL: {current_url}")
            break

        if last_request_time is not None:
            elapsed = time.monotonic() - last_request_time
            if elapsed < politeness_delay:
                time.sleep(politeness_delay - elapsed)

        html = fetch_page(current_url)
        last_request_time = time.monotonic()

        if html is None:
            print("Stopping crawl because a page could not be fetched.")
            break

        visited_urls.add(current_url)

        soup = parse_html(html)
        quote_texts = extract_quote_texts(soup)
        title = extract_page_title(soup)
        doc_id = f"page_{page_number}"

        add_page_to_index(
            index=index,
            doc_id=doc_id,
            url=current_url,
            title=title,
            quote_texts=quote_texts,
        )

        current_url = find_next_page_url(soup, current_url)
        page_number += 1

    return index
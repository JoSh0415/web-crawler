import re
import time
from collections import deque
from typing import Optional
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.indexer import InvertedIndex

BASE_URL = "https://quotes.toscrape.com/"
DEFAULT_TIMEOUT = 20
POLITENESS_DELAY = 6
MAX_FETCH_ATTEMPTS_PER_URL = 3

HEADERS = {
    "User-Agent": "COMP3011-Coursework-Search-Tool/1.0"
}


def build_session() -> requests.Session:
    """Create a session with retry behaviour for transient failures."""
    session = requests.Session()

    retry_strategy = Retry(
        total=3,
        connect=3,
        read=3,
        status=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET"]),
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    session.headers.update(HEADERS)
    return session


def fetch_page(
    url: str = BASE_URL,
    session: Optional[requests.Session] = None,
) -> Optional[str]:
    """Fetch one page and return its HTML, or None if the request fails."""
    requester = session if session is not None else requests

    print(f"Fetching: {url}")

    try:
        response = requester.get(url, timeout=DEFAULT_TIMEOUT)
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

    return normalise_url(urljoin(current_url, href))


def normalise_url(url: str) -> str:
    """Normalise URLs and collapse obvious first-page aliases."""
    parsed = urlsplit(url)

    path = parsed.path or "/"

    # Collapse repeated slashes
    path = re.sub(r"/+", "/", path)

    # Homepage first-page alias: /page/1/ -> /
    if path == "/page/1/" or path == "/page/1":
        path = "/"

    # Tag first-page alias:
    # /tag/<slug>/page/1/ -> /tag/<slug>/
    tag_page_one_match = re.fullmatch(r"/tag/([^/]+)/page/1/?", path)
    if tag_page_one_match:
        slug = tag_page_one_match.group(1)
        path = f"/tag/{slug}/"

    # Ensure non-root paths end with a single trailing slash for consistency
    if path != "/" and not path.endswith("/"):
        path = f"{path}/"

    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))

def is_internal_page_url(url: str) -> bool:
    """Return True if the URL is an internal page on quotes.toscrape.com."""
    parsed = urlsplit(url)
    base = urlsplit(BASE_URL)

    if parsed.scheme not in {"http", "https"}:
        return False

    if parsed.netloc != base.netloc:
        return False

    lower_path = parsed.path.lower()

    if lower_path.endswith((
        ".jpg", ".jpeg", ".png", ".gif", ".svg",
        ".css", ".js", ".ico", ".pdf", ".zip"
    )):
        return False

    return True


def extract_internal_links(soup: BeautifulSoup, current_url: str = BASE_URL) -> list[str]:
    """Extract all unique internal links from a page."""
    links: list[str] = []
    seen: set[str] = set()

    for tag in soup.find_all("a", href=True):
        href = tag.get("href", "").strip()

        if not href:
            continue

        if href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
            continue

        absolute_url = normalise_url(urljoin(current_url, href))

        if is_internal_page_url(absolute_url) and absolute_url not in seen:
            seen.add(absolute_url)
            links.append(absolute_url)

    return links


def extract_visible_text(soup: BeautifulSoup) -> str:
    """Extract visible page text for indexing."""
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    container = soup.body if soup.body is not None else soup
    text = container.get_text(separator=" ", strip=True)

    return " ".join(text.split())


def scrape_single_page(
    url: str = BASE_URL,
    session: Optional[requests.Session] = None,
) -> Optional[dict]:
    """Fetch and parse one page, returning the key data needed by the crawler."""
    html = fetch_page(url, session=session)
    if html is None:
        return None

    soup = parse_html(html)

    return {
        "url": normalise_url(url),
        "title": extract_page_title(soup),
        "quotes": extract_quote_texts(soup),
        "text": extract_visible_text(soup),
        "next_page_url": find_next_page_url(soup, url),
        "links": extract_internal_links(soup, url),
    }


def tokenize_text(text: str) -> list[str]:
    """Convert text into lowercase tokens ready for indexing."""
    return re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)?", text.lower())


def add_page_to_index(
    index: InvertedIndex,
    doc_id: str,
    url: str,
    title: str,
    quote_texts: list[str],
    page_text: Optional[str] = None,
) -> None:
    """
    Add one crawled page into the existing InvertedIndex.

    If page_text is provided, the full visible page text is indexed.
    Otherwise, the function falls back to the quote text only.
    """
    if page_text is None:
        page_text = " ".join(quote_texts)

    combined_text = f"{title} {page_text}".strip()
    tokens = tokenize_text(combined_text)
    index.index_tokens(doc_id=doc_id, url=url, tokens=tokens, title=title)


def crawl_all_pages(
    start_url: str = BASE_URL,
    politeness_delay: int = POLITENESS_DELAY,
) -> InvertedIndex:
    """
    Crawl all unique internal pages starting from the given URL
    and build an InvertedIndex.
    """
    index = InvertedIndex()
    start_url = normalise_url(start_url)

    visited_urls: set[str] = set()
    queued_urls: set[str] = {start_url}
    url_queue = deque([start_url])
    failed_attempts: dict[str, int] = {}

    page_number = 1
    last_request_time: Optional[float] = None
    session = build_session()

    print(f"Starting crawl from: {start_url}")

    try:
        while url_queue:
            current_url = url_queue.popleft()
            queued_urls.discard(current_url)

            if current_url in visited_urls:
                continue

            print()
            print(f"Crawling page {page_number}: {current_url}")
            print(f"Visited so far: {len(visited_urls)} | Still queued: {len(url_queue)}")

            if last_request_time is not None:
                elapsed = time.monotonic() - last_request_time
                if elapsed < politeness_delay:
                    wait_time = politeness_delay - elapsed
                    print(f"Waiting {wait_time:.2f}s to respect politeness delay...")
                    time.sleep(wait_time)

            page_data = scrape_single_page(current_url, session=session)
            last_request_time = time.monotonic()

            if page_data is None:
                failed_attempts[current_url] = failed_attempts.get(current_url, 0) + 1
                attempt_number = failed_attempts[current_url]

                if attempt_number < MAX_FETCH_ATTEMPTS_PER_URL:
                    print(
                        f"Re-queueing {current_url} "
                        f"(attempt {attempt_number + 1}/{MAX_FETCH_ATTEMPTS_PER_URL})"
                    )
                    if current_url not in queued_urls:
                        url_queue.append(current_url)
                        queued_urls.add(current_url)
                else:
                    print(f"Giving up on URL after {attempt_number} failed attempts: {current_url}")
                    visited_urls.add(current_url)

                continue

            visited_urls.add(current_url)

            title = page_data["title"]
            quote_texts = page_data["quotes"]
            page_text = page_data["text"]

            doc_id = f"page_{page_number}"
            add_page_to_index(
                index=index,
                doc_id=doc_id,
                url=current_url,
                title=title,
                quote_texts=quote_texts,
                page_text=page_text,
            )

            print(f"Indexed {doc_id}: '{title}'")
            print(f"Quotes found on page: {len(quote_texts)}")

            new_links_count = 0
            for link in page_data["links"]:
                if link not in visited_urls and link not in queued_urls:
                    url_queue.append(link)
                    queued_urls.add(link)
                    new_links_count += 1

            print(f"New internal links queued: {new_links_count}")

            page_number += 1
    finally:
        session.close()

    print()
    print("Crawl complete.")
    print(f"Total pages indexed: {len(index.documents)}")
    print(f"Total unique URLs visited: {len(visited_urls)}")

    return index
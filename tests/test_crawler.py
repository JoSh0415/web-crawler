from src.crawler import (
    parse_html,
    extract_quote_texts,
    extract_page_title,
    find_next_page_url,
    scrape_single_page,
    tokenize_text,
    build_page_tokens,
    add_page_to_index,
    crawl_all_pages,
)
from src.indexer import InvertedIndex


SAMPLE_HTML = """
<html>
    <head>
        <title>Quotes to Scrape</title>
    </head>
    <body>
        <div class="quote">
            <span class="text">“The world as we have created it is a process of our thinking.”</span>
        </div>
        <div class="quote">
            <span class="text">“It is our choices, Harry, that show what we truly are.”</span>
        </div>
        <ul class="pager">
            <li class="next">
                <a href="/page/2/">Next →</a>
            </li>
        </ul>
    </body>
</html>
"""


SAMPLE_HTML_NO_NEXT = """
<html>
    <head>
        <title>Quotes to Scrape</title>
    </head>
    <body>
        <div class="quote">
            <span class="text">“One final quote.”</span>
        </div>
    </body>
</html>
"""


CRAWL_PAGE_1 = """
<html>
    <head>
        <title>Page 1</title>
    </head>
    <body>
        <div class="quote">
            <span class="text">“Good friends matter.”</span>
        </div>
        <ul class="pager">
            <li class="next">
                <a href="/page/2/">Next →</a>
            </li>
        </ul>
    </body>
</html>
"""


CRAWL_PAGE_2 = """
<html>
    <head>
        <title>Page 2</title>
    </head>
    <body>
        <div class="quote">
            <span class="text">“Indifference is dangerous.”</span>
        </div>
    </body>
</html>
"""


def test_parse_html_returns_beautifulsoup_object():
    soup = parse_html(SAMPLE_HTML)

    assert soup.title is not None
    assert soup.title.get_text(strip=True) == "Quotes to Scrape"


def test_extract_quote_texts_returns_all_quotes():
    soup = parse_html(SAMPLE_HTML)

    quotes = extract_quote_texts(soup)

    assert len(quotes) == 2
    assert quotes[0] == "“The world as we have created it is a process of our thinking.”"
    assert quotes[1] == "“It is our choices, Harry, that show what we truly are.”"


def test_extract_page_title_returns_title_text():
    soup = parse_html(SAMPLE_HTML)

    title = extract_page_title(soup)

    assert title == "Quotes to Scrape"


def test_find_next_page_url_returns_absolute_url():
    soup = parse_html(SAMPLE_HTML)

    next_url = find_next_page_url(soup, "https://quotes.toscrape.com/")

    assert next_url == "https://quotes.toscrape.com/page/2/"


def test_find_next_page_url_returns_none_when_missing():
    soup = parse_html(SAMPLE_HTML_NO_NEXT)

    next_url = find_next_page_url(soup, "https://quotes.toscrape.com/")

    assert next_url is None


def test_scrape_single_page_returns_none_when_fetch_fails(monkeypatch):
    from src import crawler

    def fake_fetch_page(url: str):
        return None

    monkeypatch.setattr(crawler, "fetch_page", fake_fetch_page)

    result = crawler.scrape_single_page()

    assert result is None


def test_scrape_single_page_returns_expected_data(monkeypatch):
    from src import crawler

    def fake_fetch_page(url: str):
        return SAMPLE_HTML

    monkeypatch.setattr(crawler, "fetch_page", fake_fetch_page)

    result = crawler.scrape_single_page("https://quotes.toscrape.com/")

    assert result is not None
    assert result["url"] == "https://quotes.toscrape.com/"
    assert result["title"] == "Quotes to Scrape"
    assert len(result["quotes"]) == 2
    assert result["next_page_url"] == "https://quotes.toscrape.com/page/2/"


def test_tokenize_text_lowercases_and_removes_punctuation():
    tokens = tokenize_text("Hello, World! It's good.")

    assert tokens == ["hello", "world", "it's", "good"]


def test_build_page_tokens_combines_multiple_quotes():
    quote_texts = ["Good friends matter.", "Indifference is dangerous."]

    tokens = build_page_tokens(quote_texts)

    assert tokens == ["good", "friends", "matter", "indifference", "is", "dangerous"]


def test_add_page_to_index_adds_document_and_terms():
    index = InvertedIndex()

    add_page_to_index(
        index=index,
        doc_id="page_1",
        url="https://quotes.toscrape.com/",
        title="Page 1",
        quote_texts=["Good friends matter.", "Good ideas spread."],
    )

    assert "page_1" in index.documents
    assert index.documents["page_1"].title == "Page 1"
    assert index.get_postings("good")["page_1"].frequency == 2
    assert index.get_postings("friends")["page_1"].positions == [1]


def test_crawl_all_pages_builds_index_across_multiple_pages(monkeypatch):
    from src import crawler

    def fake_fetch_page(url: str):
        if url == "https://quotes.toscrape.com/":
            return CRAWL_PAGE_1
        if url == "https://quotes.toscrape.com/page/2/":
            return CRAWL_PAGE_2
        return None

    monkeypatch.setattr(crawler, "fetch_page", fake_fetch_page)
    monkeypatch.setattr(crawler.time, "sleep", lambda _: None)

    index = crawler.crawl_all_pages(politeness_delay=0)

    assert "page_1" in index.documents
    assert "page_2" in index.documents
    assert index.documents["page_1"].title == "Page 1"
    assert index.documents["page_2"].title == "Page 2"
    assert index.find_documents(["good", "friends"]) == ["page_1"]
    assert index.find_documents(["indifference"]) == ["page_2"]


def test_crawl_all_pages_returns_partial_index_when_fetch_fails(monkeypatch):
    from src import crawler

    calls = {"count": 0}

    def fake_fetch_page(url: str):
        calls["count"] += 1
        if calls["count"] == 1:
            return CRAWL_PAGE_1
        return None

    monkeypatch.setattr(crawler, "fetch_page", fake_fetch_page)
    monkeypatch.setattr(crawler.time, "sleep", lambda _: None)

    index = crawler.crawl_all_pages(politeness_delay=0)

    assert "page_1" in index.documents
    assert "page_2" not in index.documents
from src.crawler import (
    parse_html,
    extract_quote_texts,
    extract_page_title,
    find_next_page_url,
    scrape_single_page,
)


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
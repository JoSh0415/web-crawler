# COMP3011 Coursework 2 - Search Engine Tool

This project is a Python command-line search tool built for **COMP3011 Web Services and Web Data**. It crawls the **Quotes to Scrape** website, builds an inverted index of word occurrences, saves and loads that index from disk, and lets the user search for pages containing particular terms.

The tool was designed to meet the coursework brief requirements for:
- web crawling
- inverted index construction
- file-based index storage and retrieval
- query processing through a command-line shell

## Quick Start

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m src.main
```

Then, from the interactive shell:

```bash
build
load
print nonsense
find indifference
find "good friends"
find indiffernce
```

## Project Purpose

The purpose of this project is to demonstrate how a simple search engine works in practice.

The tool:
1. crawls all unique internal pages on the target website
2. extracts the visible text from each page
3. tokenises and indexes the words found on each page
4. stores word statistics such as frequency and positions
5. saves the completed index to disk
6. allows the user to load the index and search it later

The target website is:

`https://quotes.toscrape.com/`

## Features

- Crawls all unique internal pages of `https://quotes.toscrape.com/`
- Respects the required **6-second politeness window** between successive requests
- Normalises obvious first-page aliases so equivalent first pages are not indexed twice
- Builds an **inverted index** storing:
  - document IDs
  - page URLs
  - page titles
  - term frequency per page
  - term positions per page
- Saves the compiled index to a JSON file and loads it later from disk
- Uses **TF-IDF ranked retrieval** for `find <query>` results
- Supports **exact phrase queries** using stored positional information
- Supports **query suggestions** for misspelled search terms
- Handles invalid or missing index files with clearer error messages
- Includes automated tests for crawler, indexer, search logic, and CLI command flow
- Includes coverage reporting and a GitHub Actions CI workflow

## Repository Structure

```text
web-crawler/
├── src/
│   ├── crawler.py
│   ├── indexer.py
│   ├── search.py
│   └── main.py
├── tests/
│   ├── test_crawler.py
│   ├── test_indexer.py
│   └── test_search.py
├── scripts/
│   └── benchmark.py
├── .github/
│   └── workflows/
│       └── tests.yml
├── data/
│   └── index.json
├── .coveragerc
├── pytest.ini
├── requirements.txt
└── README.md
```

## Architecture Overview

The project is divided into four main modules.

### `src/crawler.py`
This module is responsible for:
- fetching pages from the target website
- parsing HTML using Beautiful Soup
- extracting visible page text and quote text
- extracting the page title
- extracting internal links from each page
- normalising URLs to avoid obvious duplicate first-page aliases
- crawling all unique internal pages while respecting the politeness delay
- retrying transient request failures
- tokenising page text before it is sent to the indexer

### `src/indexer.py`
This module defines the core data structures:
- Document
- Posting
- InvertedIndex

It is responsible for:
- storing page metadata
- storing term frequency and term positions
- adding token occurrences to the inverted index
- converting the index to and from a JSON-compatible structure
- saving and loading the compiled index file

### `src/search.py`
This module is responsible for:
- normalising terms and queries
- retrieving postings for terms
- formatting inverted index entries for the `print` command
- handling ranked retrieval for `find <query>` using TF-IDF scoring
- supporting exact phrase queries using positional adjacency
- generating suggestions for misspelled search terms
- formatting search output for the `find` command

### `src/main.py`
This is the command-line shell. 
It connects the crawler, indexer, and search layers together and provides the required user commands:
- `build`
- `load`
- `print <word>`
- `find <query>`

## Design Rationale

I used an inverted index because it is the standard data structure for efficient term-based retrieval.

For each term, the index stores the documents where that term appears, along with:
- the term frequency in each document
- the token positions in each document

This design was chosen because it:
- directly supports the coursework requirement to store word statistics such as frequency and positions
- makes `print <word>` straightforward
- makes single-word and multi-word search efficient
- supports exact phrase matching by checking positional adjacency
- supports ranked retrieval because term frequency information is already available

I chose a **page-based** index rather than indexing unique quotes as standalone records. This keeps the implementation aligned with the coursework brief, which is framed around crawling and indexing pages.

I also separated the code into crawler, indexer, search, and shell modules so that:
- each file has a clear responsibility
- the code is easier to test and debug
- the architecture is easier to explain in the video demonstration

As an extension beyond the baseline requirements, I added:
- **TF-IDF ranking** so `find` results are ordered by relevance rather than document ID
- **exact phrase queries** such as `find "good friends"` using stored term positions
- **query suggestions** for misspelled search terms such as `find indiffernce`

## Installation and Setup

1. Clone the repository
```bash
git clone <your-repository-url>
cd <repository-name>
```

2. Create and activate a virtual environment

On macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows:
```cmd
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

## Dependencies

The project uses the following main dependencies:
- requests – for HTTP requests
- beautifulsoup4 – for HTML parsing
- pytest – for automated testing
- pytest-cov - for test coverage

Install them using:
```bash
pip install -r requirements.txt
```

## How to Run the Tool

From the repository root, run:
```bash
python -m src.main
```
This starts the interactive shell.

## Command Usage

### `build`
Crawls the target website, builds the inverted index, and saves it to `data/index.json`.
```shell
> build
```
Notes:
- this command takes time because the crawler waits at least 6 seconds between successive requests
- after build, the index is also kept in memory for immediate searching
- the crawler indexes all unique internal pages on the site, including main quote pages, tag pages, and author pages

### `load`
Loads the saved index from `data/index.json`.
```shell
> load
```
This only works after an index has already been built and saved.

### `print <word>`
Prints the inverted index entry for a single word.
```shell
> print nonsense
```
Example output:
```text
Index entry for 'nonsense':
  [page_2] frequency=1, positions=[378]
  [page_7] frequency=1, positions=[258]
```

### `find <query>`
Searches the index and returns matching pages.

Single-word example:
```shell
> find indifference
```

Multi-word example:
```shell
> find good friends
```

Normal multi-word queries use AND logic, so only pages containing all query words are returned.

Exact phrase example:
```shell
> find "good friends"
```

Quoted phrase queries return only pages where the words appear adjacently in that order.

Misspelling suggestion example:
```shell
> find indiffernce
```

If no results are found and one or more terms look misspelled, the tool suggests the closest indexed terms.

### `help`
Shows the list of available commands.
```shell
> help
```

### `exit` / `quit`
Exits the shell.
```shell
> exit
```

## Testing

The project includes automated tests for:
- crawler behaviour
- indexer data structures and serialisation
- search and retrieval logic
- CLI command flow and user-facing error handling

The test suite is configured to:
- collect coverage for the `src/` package
- enforce a minimum coverage threshold
- generate terminal, XML, and HTML coverage reports

Run the full test suite with:

```bash
python -m pytest
```

This generates:

- terminal coverage output

- `coverage.xml`

- an HTML coverage report in `htmlcov/`

To inspect the HTML coverage report locally, `open htmlcov/index.html` in a browser.

You can also run individual test files:

```bash
python -m pytest tests/test_crawler.py
python -m pytest tests/test_indexer.py
python -m pytest tests/test_search.py
```

On GitHub, tests and coverage also run automatically on pushes and pull requests using GitHub Actions.

## Testing Strategy

The project was tested incrementally as each component was developed, and the final test suite includes both happy-path and failure-path behaviour.

### `tests/test_crawler.py`
Covers:
- HTML parsing
- quote extraction
- page title extraction
- next-page handling
- tokenisation
- internal link extraction
- URL normalisation
- adding page data into the index
- crawling multiple linked pages using mocked responses
- retry / failure handling behaviour
- session cleanup on unexpected crawler errors

### `tests/test_indexer.py`
Covers:
- document storage
- posting frequency and positions
- indexing token lists
- case-insensitive lookups
- multi-word document matching
- JSON serialisation and deserialisation
- save/load round-trip behaviour
- invalid JSON / malformed index-file validation
- storage integrity checks such as frequency-position consistency

### `tests/test_search.py`
Covers:
- term and query normalisation
- postings lookup
- formatting index entries
- TF-IDF-ranked retrieval
- exact phrase query matching
- misspelling suggestions
- single-word and multi-word search
- unknown-word handling
- empty query handling
- CLI command parsing and routing
- shell-level error handling for missing index / failed load / interrupted input

## Performance and Complexity

The crawler, indexer, and search logic were designed to use data structures that keep lookup and retrieval efficient.

### Complexity overview

Let:
- `P` = number of pages crawled
- `T` = total number of indexed token occurrences across all pages
- `m` = number of terms in a query
- `df(t)` = document frequency of term `t`
- `r` = number of matched result documents

**Build / crawl**
- The crawler processes pages incrementally and indexes tokens as pages are fetched.
- Ignoring network latency, HTML parsing and indexing are approximately linear in the amount of text processed, so the indexing work is roughly proportional to `T`.
- In practice, total build time is dominated by network latency and the required 6-second politeness delay between requests.

**`print <word>`**
- Dictionary lookup for a term is approximately `O(1)` on average.
- Formatting output is proportional to the number of postings for that word, so the overall cost is approximately `O(df(term))`.

**`find <query>`**
- Normal multi-word queries use AND semantics.
- Candidate documents are found by intersecting the posting sets for each query term.
- A practical approximation is `O(df(t1) + df(t2) + ... + df(tm))` for the set construction/intersection work, followed by ranking work over the matched results.
- Ranking the matched documents adds approximately `O(r * m)` scoring work plus sorting cost.

**Exact phrase queries**
- Exact phrase queries first use AND matching to find candidate documents, then use stored positional information to check adjacency.
- This is more precise than normal AND search but adds extra positional checking work per candidate document.

**Suggestions**
- Query suggestions are only attempted when a search returns no results.
- Suggestion generation compares unknown terms against the indexed vocabulary, so it is a fallback convenience feature rather than part of the normal fast path.

### Design trade-offs

I chose a page-based inverted index using dictionaries because it makes:
- term lookup simple,
- storage format easy to serialise to JSON,
- and query processing straightforward to explain in the video.

I also stored term positions, not just frequencies, because this supports exact phrase matching rather than only single-word or unordered multi-word search.

## Benchmark Results

Benchmarks were run against `data/index.json`.

### Index Statistics

| Metric | Value |
|---|---:|
| Documents | 202 |
| Vocabulary size | 4652 |
| Total postings | 20259 |
| Total indexed occurrences | 33475 |

### Load Benchmark

Measured over 5 runs.

| Mean (ms) | Median (ms) | Min (ms) | Max (ms) | P95 (ms) |
|---:|---:|---:|---:|---:|
| 36.952 | 36.953 | 36.277 | 38.255 | 38.255 |

### `print` Benchmark

Measured over 200 runs per term.

| Term | Postings | Mean (ms) | Median (ms) | P95 (ms) |
|---|---:|---:|---:|---:|
| `nonsense` | 5 | 0.004 | 0.004 | 0.004 |
| `good` | 30 | 0.017 | 0.017 | 0.018 |
| `indifference` | 9 | 0.008 | 0.008 | 0.008 |

### `find` Benchmark

Measured over 200 runs per query.

| Query | Results | Mean (ms) | Median (ms) | P95 (ms) |
|---|---:|---:|---:|---:|
| `indifference` | 9 | 0.044 | 0.042 | 0.044 |
| `good friends` | 26 | 0.194 | 0.193 | 0.198 |
| `"good friends"` | 6 | 0.102 | 0.101 | 0.105 |
| `indiffernce` | 0 | 8.840 | 8.825 | 8.928 |

Build timing against the live site was not routinely benchmarked because the crawler intentionally respects the required 6-second politeness delay, so real build time is dominated by network latency and politeness rather than local retrieval performance. For that reason, the benchmarks reported here focus on loading the compiled index and executing `print` / `find` operations locally.

## Example Workflow

A typical use of the tool looks like this:
```shell
> build
> load
> print nonsense
> find indifference
> find good friends
```

## Notes and Limitations

- The tool is designed specifically for the coursework target website: `https://quotes.toscrape.com/`
- Search is case-insensitive
- Query processing currently uses simple AND-style matching
- The current implementation does not include ranking such as TF-IDF
- The index is saved as a single JSON file for simplicity
- The crawler indexes all unique internal pages on `quotes.toscrape.com`, not just the main paginated quote pages
- Obvious first-page aliases such as `/page/1/` and `/tag/<slug>/page/1/` are normalised so equivalent first pages are not indexed twice

## External Libraries and Resources

This project uses:
- Requests documentation: for HTTP requests and session handling
- Beautiful Soup 4 documentation: for HTML parsing
- urllib3 Retry / requests HTTPAdapter behaviour: for transient request retry handling
- Pytest documentation: for automated testing

The target practice website was:
- `https://quotes.toscrape.com/`

## Submission Notes

For the coursework submission, the GitHub repository should be submitted together with:
- the video demonstration link
- the compiled index file generated by the tool

## Author

Created for COMP3011 Coursework 2 by Josh Deane.
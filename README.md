# COMP3011 Coursework 2 - Search Engine Tool

This project is a Python command-line search tool built for **COMP3011 Web Services and Web Data**. It crawls the **Quotes to Scrape** website, builds an inverted index of word occurrences, saves and loads that index from disk, and lets the user search for pages containing particular terms.

The tool was designed to meet the coursework brief requirements for:
- web crawling
- inverted index construction
- file-based index storage and retrieval
- query processing through a command-line shell

## Project Purpose

The purpose of this project is to demonstrate how a simple search engine works in practice.

The tool:
1. crawls all pages of the target website
2. extracts the visible quote text from each page
3. tokenises and indexes the words found on each page
4. stores word statistics such as frequency and positions
5. saves the completed index to disk
6. allows the user to load the index and search it later

The target website is:

`https://quotes.toscrape.com/`

## Features

- Crawls all pages of the target website
- Respects the required **6-second politeness window** between successive requests
- Builds an **inverted index** storing:
  - document IDs
  - page URLs
  - page titles
  - term frequency per page
  - term positions per page
- Saves the compiled index to a JSON file
- Loads the saved index from disk
- Supports the required shell commands:
  - `build`
  - `load`
  - `print <word>`
  - `find <query>`
- Case-insensitive searching
- Single-word and multi-word query support
- Unit tests for crawler, indexer, and search functionality

## Repository Structure

```text
repository-name/
├── src/
│   ├── crawler.py
│   ├── indexer.py
│   ├── search.py
│   └── main.py
├── tests/
│   ├── test_crawler.py
│   ├── test_indexer.py
│   └── test_search.py
├── data/
│   └── index.json
├── requirements.txt
└── README.md
```

## Architecture Overview

The project is divided into four main modules.

### `src/crawler.py`
This module is responsible for:
- fetching pages from the target website
- parsing HTML using Beautiful Soup
- extracting visible quote text
- extracting the page title
- locating the next-page link
- crawling through all pages while respecting the politeness delay
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
- formatting inverted index entries for the print command
- finding matching documents for single-word and multi-word queries
- formatting search output for the find command

### `src/main.py`
This is the command-line shell. 
It connects the crawler, indexer, and search layers together and provides the required user commands:
- `build`
- `load`
- `print <word>`
- `find <query>`

## Design Rationale

I used an inverted index structure because it is a natural and efficient way to support term lookups in a search tool.

For each word, the index stores the pages where that word appears, along with:
- how many times it appears in that page
- the positions where it appears in that page

This design was chosen because it:
- matches the coursework requirement to store word statistics such as frequency and position
- makes `print <word>` straightforward
- makes `find <query>` efficient for both single-word and multi-word lookups
- supports future extensions such as phrase search or ranking improvements

I also separated the code into crawler, indexer, search, and shell modules so each file has a clear responsibility. This made the code easier to test, easier to debug, and easier to explain in the video demonstration.

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
Searches the index and returns pages containing the query terms.

Single-word example:
```shell
> find indifference
```

Multi-word example:
```shell
> find good friends
```
Multi-word queries use AND logic, so only pages containing all query words are returned.

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

To run all tests:
```bash
pytest
```

To run specific test files:
```bash
pytest tests/test_crawler.py
pytest tests/test_indexer.py
pytest tests/test_search.py
```

## Testing Strategy

The project was tested incrementally as each component was developed.

### `test_crawler.py`
Covers:
- HTML parsing
- quote text extraction
- page title extraction
- next-page URL detection
- tokenisation
- adding page data into the index
- crawling multiple pages using mocked responses
- partial crawl failure handling

### `test_indexer.py`
Covers:
- document storage
- posting frequency and positions
- indexing token lists
- case-insensitive lookups
- multi-word document matching
- JSON serialisation and deserialisation
- save/load round-trip behaviour

### `test_search.py`
Covers:
- term and query normalisation
- postings lookup
- formatting index entries
- single-word search
- multi-word search using AND logic
- unknown-word handling
- empty query handling

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

## External Libraries and Resources

This project uses:
- Python Requests library
- Beautiful Soup 4
- Pytest

The target practice website was:
- `https://quotes.toscrape.com/`

## Submission Notes

For the coursework submission, the GitHub repository should be submitted together with:
- the video demonstration link
- the compiled index file generated by the tool

## Author

Created for COMP3011 Coursework 2 by Josh Deane.
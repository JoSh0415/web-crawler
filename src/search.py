from typing import List

from src.indexer import Document, InvertedIndex, Posting


def normalise_term(term: str) -> str:
    """Return a stripped, lowercase version of one term."""
    return term.strip().lower()


def normalise_query(query: str) -> List[str]:
    """Split a raw query string into cleaned lowercase terms."""
    return [part.strip().lower() for part in query.split() if part.strip()]


def get_postings_for_term(index: InvertedIndex, term: str) -> dict[str, Posting]:
    """Return the postings dictionary for one term."""
    normalised = normalise_term(term)
    if not normalised:
        return {}

    return index.get_postings(normalised)


def format_index_entry(index: InvertedIndex, term: str) -> str:
    """Return a readable string for one inverted index entry."""
    normalised = normalise_term(term)

    if not normalised:
        return "Please enter a word."

    postings = get_postings_for_term(index, normalised)

    if not postings:
        return f"No index entry found for '{normalised}'."

    lines = [f"Index entry for '{normalised}':"]

    for doc_id in sorted(postings.keys()):
        posting = postings[doc_id]
        lines.append(
            f"  [{doc_id}] frequency={posting.frequency}, positions={posting.positions}"
        )

    return "\n".join(lines)


def print_index_entry(index: InvertedIndex, term: str) -> None:
    """Print the inverted index entry for one word."""
    print(format_index_entry(index, term))


def find_matching_doc_ids(index: InvertedIndex, query: str) -> List[str]:
    """Return matching document IDs for a query."""
    terms = normalise_query(query)

    if not terms:
        return []

    return index.find_documents(terms)


def find_matching_documents(index: InvertedIndex, query: str) -> List[Document]:
    """Return matching Document objects for a query."""
    doc_ids = find_matching_doc_ids(index, query)

    return [index.documents[doc_id] for doc_id in doc_ids if doc_id in index.documents]


def format_search_results(index: InvertedIndex, query: str) -> str:
    """Return a readable string for search results."""
    terms = normalise_query(query)

    if not terms:
        return "Please enter one or more search words."

    documents = find_matching_documents(index, query)

    if not documents:
        return f"No documents found for query: {' '.join(terms)}"

    lines = [f"Documents matching query: {' '.join(terms)}"]

    for document in documents:
        lines.append(f"  [{document.doc_id}] {document.title} - {document.url}")

    return "\n".join(lines)


def print_search_results(index: InvertedIndex, query: str) -> None:
    """Print search results for a query."""
    print(format_search_results(index, query))
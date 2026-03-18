import math
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


def get_document_frequency(index: InvertedIndex, term: str) -> int:
    """Return the number of documents that contain the term."""
    return len(get_postings_for_term(index, term))


def get_inverse_document_frequency(index: InvertedIndex, term: str) -> float:
    """
    Compute a smoothed inverse document frequency score.

    Formula:
        idf = log((N + 1) / (df + 1)) + 1

    where:
    - N is the total number of indexed documents
    - df is the number of documents containing the term
    """
    total_documents = len(index.documents)
    document_frequency = get_document_frequency(index, term)

    if total_documents == 0 or document_frequency == 0:
        return 0.0

    return math.log((total_documents + 1) / (document_frequency + 1)) + 1.0


def get_tf_idf_score(index: InvertedIndex, doc_id: str, query_terms: List[str]) -> float:
    """
    Score one document for a query using a simple TF-IDF approach.

    Term frequency weight:
        tf_weight = 1 + log(tf)

    Query terms are summed to produce a final score.
    """
    score = 0.0

    for term in query_terms:
        postings = get_postings_for_term(index, term)
        posting = postings.get(doc_id)

        if posting is None or posting.frequency <= 0:
            continue

        tf_weight = 1.0 + math.log(posting.frequency)
        idf = get_inverse_document_frequency(index, term)
        score += tf_weight * idf

    return score


def natural_doc_id_key(doc_id: str) -> tuple[int, str]:
    """
    Return a key that sorts page_2 before page_10.

    This is used only as a tie-break when ranked scores are equal.
    """
    if doc_id.startswith("page_"):
        suffix = doc_id.removeprefix("page_")
        if suffix.isdigit():
            return (0, f"{int(suffix):010d}")

    return (1, doc_id)


def rank_matching_doc_ids(index: InvertedIndex, query: str) -> List[str]:
    """
    Return matching document IDs ranked by TF-IDF score.

    Query semantics remain AND-based:
    all returned documents must contain every query term.
    """
    terms = normalise_query(query)

    if not terms:
        return []

    matching_doc_ids = index.find_documents(terms)

    ranked_doc_ids = sorted(
        matching_doc_ids,
        key=lambda doc_id: (
            -get_tf_idf_score(index, doc_id, terms),
            natural_doc_id_key(doc_id),
        ),
    )

    return ranked_doc_ids


def find_matching_doc_ids(index: InvertedIndex, query: str) -> List[str]:
    """Return matching document IDs for a query, ranked by relevance."""
    return rank_matching_doc_ids(index, query)


def find_matching_documents(index: InvertedIndex, query: str) -> List[Document]:
    """Return matching Document objects for a query."""
    doc_ids = find_matching_doc_ids(index, query)
    return [index.documents[doc_id] for doc_id in doc_ids if doc_id in index.documents]


def format_search_results(index: InvertedIndex, query: str) -> str:
    """Return a readable string for ranked search results."""
    terms = normalise_query(query)

    if not terms:
        return "Please enter one or more search words."

    ranked_doc_ids = find_matching_doc_ids(index, query)

    if not ranked_doc_ids:
        return f"No documents found for query: {' '.join(terms)}"

    lines = [f"Documents matching query: {' '.join(terms)}"]

    for doc_id in ranked_doc_ids:
        document = index.documents[doc_id]
        score = get_tf_idf_score(index, doc_id, terms)
        lines.append(
            f"  [{document.doc_id}] score={score:.3f} "
            f"{document.title} - {document.url}"
        )

    return "\n".join(lines)


def print_search_results(index: InvertedIndex, query: str) -> None:
    """Print search results for a query."""
    print(format_search_results(index, query))
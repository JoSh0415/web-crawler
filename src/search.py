import math
from typing import List

from src.indexer import Document, InvertedIndex, Posting


def normalise_term(term: str) -> str:
    """Return a stripped, lowercase version of one term."""
    return term.strip().lower()


def normalise_query(query: str) -> List[str]:
    """Split a raw query string into cleaned lowercase terms."""
    return [part.strip().lower() for part in query.split() if part.strip()]


def is_exact_phrase_query(query: str) -> bool:
    """Return True if the user entered a query wrapped in double quotes."""
    stripped = query.strip()
    return len(stripped) >= 2 and stripped.startswith('"') and stripped.endswith('"')


def get_query_terms(query: str) -> List[str]:
    """
    Return the cleaned terms for a query.

    For exact phrase queries like:
        "good friends"
    the surrounding double quotes are removed before tokenisation.
    """
    stripped = query.strip()

    if is_exact_phrase_query(stripped):
        stripped = stripped[1:-1]

    return normalise_query(stripped)


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
    """Return a key that sorts page_2 before page_10."""
    if doc_id.startswith("page_"):
        suffix = doc_id.removeprefix("page_")
        if suffix.isdigit():
            return (0, f"{int(suffix):010d}")

    return (1, doc_id)


def document_contains_exact_phrase(index: InvertedIndex, doc_id: str, query_terms: List[str]) -> bool:
    """
    Return True if the document contains the exact phrase.

    Example:
    - query_terms = ["good", "friends"]
    - this returns True only if 'good' is immediately followed by 'friends'
      somewhere in the document.
    """
    if not query_terms:
        return False

    if len(query_terms) == 1:
        return doc_id in get_postings_for_term(index, query_terms[0])

    postings_for_first_term = get_postings_for_term(index, query_terms[0])
    first_posting = postings_for_first_term.get(doc_id)

    if first_posting is None:
        return False

    candidate_starts = set(first_posting.positions)

    for offset, term in enumerate(query_terms[1:], start=1):
        posting = get_postings_for_term(index, term).get(doc_id)
        if posting is None:
            return False

        shifted_positions = {position - offset for position in posting.positions}
        candidate_starts = candidate_starts.intersection(shifted_positions)

        if not candidate_starts:
            return False

    return True


def get_exact_phrase_matches(index: InvertedIndex, query_terms: List[str]) -> List[str]:
    """
    Return document IDs that contain the exact phrase.

    The function first narrows candidates using AND matching,
    then checks positional adjacency using stored term positions.
    """
    if not query_terms:
        return []

    candidate_doc_ids = index.find_documents(query_terms)

    exact_matches = [
        doc_id
        for doc_id in candidate_doc_ids
        if document_contains_exact_phrase(index, doc_id, query_terms)
    ]

    return exact_matches


def rank_doc_ids(index: InvertedIndex, doc_ids: List[str], query_terms: List[str]) -> List[str]:
    """Return document IDs ranked by TF-IDF score, with natural tie-breaking."""
    return sorted(
        doc_ids,
        key=lambda doc_id: (
            -get_tf_idf_score(index, doc_id, query_terms),
            natural_doc_id_key(doc_id),
        ),
    )


def find_matching_doc_ids(index: InvertedIndex, query: str) -> List[str]:
    """
    Return matching document IDs for a query.

    Supported modes:
    - normal query: AND search
      example: good friends
    - exact phrase query: adjacency search using positions
      example: "good friends"
    """
    terms = get_query_terms(query)

    if not terms:
        return []

    if is_exact_phrase_query(query):
        matches = get_exact_phrase_matches(index, terms)
    else:
        matches = index.find_documents(terms)

    return rank_doc_ids(index, matches, terms)


def find_matching_documents(index: InvertedIndex, query: str) -> List[Document]:
    """Return matching Document objects for a query."""
    doc_ids = find_matching_doc_ids(index, query)
    return [index.documents[doc_id] for doc_id in doc_ids if doc_id in index.documents]


def format_search_results(index: InvertedIndex, query: str) -> str:
    """Return a readable string for search results."""
    terms = get_query_terms(query)

    if not terms:
        return "Please enter one or more search words."

    ranked_doc_ids = find_matching_doc_ids(index, query)

    if not ranked_doc_ids:
        if is_exact_phrase_query(query):
            return f'No documents found for exact phrase: {" ".join(terms)}'
        return f"No documents found for query: {' '.join(terms)}"

    if is_exact_phrase_query(query):
        lines = [f'Documents matching exact phrase: {" ".join(terms)}']
    else:
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
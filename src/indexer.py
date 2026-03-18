"""Indexer data structures for the coursework search tool.

This file defines the inverted index design and helper methods.
It does not crawl the website or save/load files.
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Document:
    """Stores basic information about one page/document."""
    doc_id: str
    url: str
    title: str = ""


@dataclass
class Posting:
    """Stores statistics for one term in one document."""
    frequency: int = 0
    positions: List[int] = field(default_factory=list)

    def add_occurrence(self, position: int) -> None:
        """Record one appearance of the term in this document."""
        self.frequency += 1
        self.positions.append(position)


class InvertedIndex:
    """A simple inverted index.

    Structure:
    - documents maps doc_id -> Document
    - index maps term -> {doc_id -> Posting}
    """

    def __init__(self) -> None:
        self.documents: Dict[str, Document] = {}
        self.index: Dict[str, Dict[str, Posting]] = {}

    def add_document(self, doc_id: str, url: str, title: str = "") -> None:
        """Add or update document metadata."""
        self.documents[doc_id] = Document(doc_id=doc_id, url=url, title=title)

    def add_term_occurrence(self, term: str, doc_id: str, position: int) -> None:
        """Add one occurrence of a term in a document."""
        term = term.lower()

        if term not in self.index:
            self.index[term] = {}

        if doc_id not in self.index[term]:
            self.index[term][doc_id] = Posting()

        self.index[term][doc_id].add_occurrence(position)

    def index_tokens(self, doc_id: str, url: str, tokens: List[str], title: str = "") -> None:
        """Index a list of already-prepared tokens for one document."""
        self.add_document(doc_id, url, title)

        for position, token in enumerate(tokens):
            self.add_term_occurrence(token, doc_id, position)

    def get_postings(self, term: str) -> Dict[str, Posting]:
        """Return all postings for one term."""
        return self.index.get(term.lower(), {})

    def find_documents(self, query_terms: List[str]) -> List[str]:
        """Return document IDs containing all query terms."""
        if not query_terms:
            return []

        normalised_terms = [term.lower() for term in query_terms]

        matching_docs = set(self.index.get(normalised_terms[0], {}).keys())

        for term in normalised_terms[1:]:
            term_docs = set(self.index.get(term, {}).keys())
            matching_docs = matching_docs.intersection(term_docs)

        return sorted(matching_docs)
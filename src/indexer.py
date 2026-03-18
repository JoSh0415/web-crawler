from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Union
import json


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

    def to_dict(self) -> dict:
        """Convert the whole index into plain dictionaries for JSON saving."""
        return {
            "documents": {
                doc_id: {
                    "doc_id": doc.doc_id,
                    "url": doc.url,
                    "title": doc.title,
                }
                for doc_id, doc in self.documents.items()
            },
            "index": {
                term: {
                    doc_id: {
                        "frequency": posting.frequency,
                        "positions": posting.positions,
                    }
                    for doc_id, posting in postings.items()
                }
                for term, postings in self.index.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "InvertedIndex":
        """Rebuild an InvertedIndex from saved dictionary data."""
        new_index = cls()

        for doc_id, doc_data in data.get("documents", {}).items():
            new_index.documents[doc_id] = Document(
                doc_id=doc_data["doc_id"],
                url=doc_data["url"],
                title=doc_data.get("title", ""),
            )

        for term, postings in data.get("index", {}).items():
            new_index.index[term] = {}
            for doc_id, posting_data in postings.items():
                new_index.index[term][doc_id] = Posting(
                    frequency=posting_data["frequency"],
                    positions=posting_data["positions"],
                )

        return new_index


def save_index(index: InvertedIndex, filename: Union[str, Path]) -> None:
    """Save the index to a JSON file."""
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(index.to_dict(), file, indent=2, ensure_ascii=False)


def load_index(filename: Union[str, Path]) -> InvertedIndex:
    """Load an index from a JSON file."""
    path = Path(filename)

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return InvertedIndex.from_dict(data)
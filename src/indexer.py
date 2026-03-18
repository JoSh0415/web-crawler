from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Union
import json
import os
import tempfile


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
        validate_index_data(data)

        new_index = cls()

        documents_data = data["documents"]
        for doc_id, doc_data in documents_data.items():
            new_index.documents[doc_id] = Document(
                doc_id=doc_data["doc_id"],
                url=doc_data["url"],
                title=doc_data.get("title", ""),
            )

        index_data = data["index"]
        for term, postings in index_data.items():
            new_index.index[term] = {}
            for doc_id, posting_data in postings.items():
                new_index.index[term][doc_id] = Posting(
                    frequency=posting_data["frequency"],
                    positions=posting_data["positions"],
                )

        return new_index


def validate_index_data(data: Any) -> None:
    """Validate the shape of loaded JSON before rebuilding the index."""
    if not isinstance(data, dict):
        raise ValueError("Index file must contain a top-level JSON object.")

    if "documents" not in data or "index" not in data:
        raise ValueError("Index file must contain 'documents' and 'index' sections.")

    if not isinstance(data["documents"], dict):
        raise ValueError("'documents' must be a JSON object mapping doc IDs to metadata.")

    if not isinstance(data["index"], dict):
        raise ValueError("'index' must be a JSON object mapping terms to postings.")

    for doc_id, doc_data in data["documents"].items():
        if not isinstance(doc_id, str):
            raise ValueError("Document IDs in 'documents' must be strings.")

        if not isinstance(doc_data, dict):
            raise ValueError(f"Document entry for '{doc_id}' must be an object.")

        if "doc_id" not in doc_data or "url" not in doc_data:
            raise ValueError(
                f"Document entry for '{doc_id}' must include 'doc_id' and 'url'."
            )

        if not isinstance(doc_data["doc_id"], str):
            raise ValueError(f"'doc_id' for document '{doc_id}' must be a string.")

        if not isinstance(doc_data["url"], str):
            raise ValueError(f"'url' for document '{doc_id}' must be a string.")

        if "title" in doc_data and not isinstance(doc_data["title"], str):
            raise ValueError(f"'title' for document '{doc_id}' must be a string.")

    for term, postings in data["index"].items():
        if not isinstance(term, str):
            raise ValueError("Terms in 'index' must be strings.")

        if not isinstance(postings, dict):
            raise ValueError(f"Postings for term '{term}' must be an object.")

        for doc_id, posting_data in postings.items():
            if not isinstance(doc_id, str):
                raise ValueError(f"Posting doc ID for term '{term}' must be a string.")

            if not isinstance(posting_data, dict):
                raise ValueError(
                    f"Posting entry for term '{term}' and document '{doc_id}' must be an object."
                )

            if "frequency" not in posting_data or "positions" not in posting_data:
                raise ValueError(
                    f"Posting entry for term '{term}' and document '{doc_id}' must include "
                    "'frequency' and 'positions'."
                )

            frequency = posting_data["frequency"]
            positions = posting_data["positions"]

            if not isinstance(frequency, int) or frequency < 0:
                raise ValueError(
                    f"'frequency' for term '{term}' and document '{doc_id}' must be a "
                    "non-negative integer."
                )

            if not isinstance(positions, list) or not all(isinstance(pos, int) for pos in positions):
                raise ValueError(
                    f"'positions' for term '{term}' and document '{doc_id}' must be a list of integers."
                )

            if frequency != len(positions):
                raise ValueError(
                    f"'frequency' for term '{term}' and document '{doc_id}' must match the number of positions."
                )


def save_index(index: InvertedIndex, filename: Union[str, Path]) -> None:
    """Save the index to a JSON file atomically."""
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_path_str = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    temp_path = Path(temp_path_str)

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(index.to_dict(), file, indent=2, ensure_ascii=False)
            file.flush()
            os.fsync(file.fileno())

        temp_path.replace(path)
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise


def load_index(filename: Union[str, Path]) -> InvertedIndex:
    """Load an index from a JSON file with validation and clearer errors."""
    path = Path(filename)

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Index file not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"Index file is not valid JSON: {exc}") from exc

    return InvertedIndex.from_dict(data)
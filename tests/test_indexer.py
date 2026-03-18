from src.indexer import InvertedIndex

def test_add_document_stores_metadata():
    """Adding a document should store its ID, URL, and title."""
    index = InvertedIndex()

    index.add_document("page_1", "https://example.com/page1", "Example Page")

    assert "page_1" in index.documents
    assert index.documents["page_1"].url == "https://example.com/page1"
    assert index.documents["page_1"].title == "Example Page"


def test_add_term_occurrence_updates_frequency_and_positions():
    """Adding the same term twice in one document should update its stats."""
    index = InvertedIndex()

    index.add_term_occurrence("good", "page_1", 2)
    index.add_term_occurrence("good", "page_1", 5)

    posting = index.index["good"]["page_1"]
    assert posting.frequency == 2
    assert posting.positions == [2, 5]


def test_index_tokens_adds_document_and_indexes_words():
    """Indexing tokens should add the document and store word positions."""
    index = InvertedIndex()

    tokens = ["good", "friends", "are", "good"]
    index.index_tokens("page_1", "https://example.com/page1", tokens, "Page 1")

    assert "page_1" in index.documents
    assert index.index["good"]["page_1"].frequency == 2
    assert index.index["good"]["page_1"].positions == [0, 3]
    assert index.index["friends"]["page_1"].positions == [1]


def test_get_postings_returns_postings_for_a_word():
    """Getting postings for a word should return the documents that contain it."""
    index = InvertedIndex()

    index.index_tokens("page_1", "https://example.com/page1", ["good", "day"])
    index.index_tokens("page_2", "https://example.com/page2", ["good", "friends"])

    postings = index.get_postings("good")

    assert set(postings.keys()) == {"page_1", "page_2"}
    assert postings["page_1"].frequency == 1
    assert postings["page_2"].frequency == 1


def test_find_documents_returns_docs_containing_all_query_terms():
    """A multi-word query should return only documents containing every word."""
    index = InvertedIndex()

    index.index_tokens("page_1", "https://example.com/page1", ["good", "friends", "matter"])
    index.index_tokens("page_2", "https://example.com/page2", ["good", "ideas"])
    index.index_tokens("page_3", "https://example.com/page3", ["friends", "first"])

    result = index.find_documents(["good", "friends"])

    assert result == ["page_1"]


def test_case_insensitive_lookups_work_for_terms_and_queries():
    """Lookups should treat uppercase and lowercase words as the same term."""
    index = InvertedIndex()

    index.index_tokens("page_1", "https://example.com/page1", ["Good", "Friends"])

    postings = index.get_postings("GOOD")
    result = index.find_documents(["good", "FRIENDS"])

    assert "page_1" in postings
    assert result == ["page_1"]


def test_empty_query_returns_empty_list():
    """An empty query should return no matching documents."""
    index = InvertedIndex()

    result = index.find_documents([])

    assert result == []
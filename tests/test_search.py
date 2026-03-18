from src.indexer import InvertedIndex
from src.search import (
    normalise_term,
    normalise_query,
    get_postings_for_term,
    format_index_entry,
    find_matching_doc_ids,
    find_matching_documents,
    format_search_results,
)


def build_sample_index() -> InvertedIndex:
    index = InvertedIndex()
    index.index_tokens(
        "page_1",
        "https://example.com/page1",
        ["good", "friends", "matter"],
        "Page 1",
    )
    index.index_tokens(
        "page_2",
        "https://example.com/page2",
        ["good", "ideas"],
        "Page 2",
    )
    index.index_tokens(
        "page_3",
        "https://example.com/page3",
        ["indifference", "is", "dangerous"],
        "Page 3",
    )
    return index


def test_normalise_term_strips_and_lowercases():
    assert normalise_term(" Good ") == "good"


def test_normalise_query_splits_and_lowercases():
    assert normalise_query(" Good   Friends ") == ["good", "friends"]


def test_get_postings_for_term_returns_matching_postings():
    index = build_sample_index()

    postings = get_postings_for_term(index, "GOOD")

    assert set(postings.keys()) == {"page_1", "page_2"}


def test_get_postings_for_term_returns_empty_dict_for_unknown_word():
    index = build_sample_index()

    postings = get_postings_for_term(index, "spaceship")

    assert postings == {}


def test_format_index_entry_returns_readable_output_for_known_word():
    index = build_sample_index()

    result = format_index_entry(index, "good")

    assert "Index entry for 'good':" in result
    assert "[page_1] frequency=1" in result
    assert "[page_2] frequency=1" in result


def test_format_index_entry_handles_unknown_word():
    index = build_sample_index()

    result = format_index_entry(index, "spaceship")

    assert result == "No index entry found for 'spaceship'."


def test_format_index_entry_handles_empty_word():
    index = build_sample_index()

    result = format_index_entry(index, "   ")

    assert result == "Please enter a word."


def test_find_matching_doc_ids_returns_single_word_matches():
    index = build_sample_index()

    result = find_matching_doc_ids(index, "good")

    assert result == ["page_1", "page_2"]


def test_find_matching_doc_ids_returns_multi_word_and_matches():
    index = build_sample_index()

    result = find_matching_doc_ids(index, "good friends")

    assert result == ["page_1"]


def test_find_matching_doc_ids_returns_empty_for_unknown_word():
    index = build_sample_index()

    result = find_matching_doc_ids(index, "spaceship")

    assert result == []


def test_find_matching_doc_ids_returns_empty_for_empty_query():
    index = build_sample_index()

    result = find_matching_doc_ids(index, "   ")

    assert result == []


def test_find_matching_documents_returns_document_objects():
    index = build_sample_index()

    documents = find_matching_documents(index, "indifference")

    assert len(documents) == 1
    assert documents[0].doc_id == "page_3"
    assert documents[0].title == "Page 3"


def test_format_search_results_returns_readable_matches():
    index = build_sample_index()

    result = format_search_results(index, "good friends")

    assert "Documents matching query: good friends" in result
    assert "[page_1] Page 1 - https://example.com/page1" in result


def test_format_search_results_handles_unknown_query():
    index = build_sample_index()

    result = format_search_results(index, "spaceship")

    assert result == "No documents found for query: spaceship"


def test_format_search_results_handles_empty_query():
    index = build_sample_index()

    result = format_search_results(index, "   ")

    assert result == "Please enter one or more search words."
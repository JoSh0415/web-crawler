from src.indexer import InvertedIndex
from src.search import (
    normalise_term,
    normalise_query,
    is_exact_phrase_query,
    get_query_terms,
    get_postings_for_term,
    format_index_entry,
    document_contains_exact_phrase,
    get_term_suggestion,
    get_query_suggestion,
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
    assert "[page_1] score=" in result
    assert "Page 1 - https://example.com/page1" in result


def test_format_search_results_handles_unknown_query():
    index = build_sample_index()

    result = format_search_results(index, "spaceship")

    assert result == "No documents found for query: spaceship"


def test_format_search_results_handles_empty_query():
    index = build_sample_index()

    result = format_search_results(index, "   ")

    assert result == "Please enter one or more search words."


def build_ranked_index() -> InvertedIndex:
    index = InvertedIndex()
    index.index_tokens(
        "page_1",
        "https://example.com/page1",
        ["good", "friends", "good", "good"],
        "Page 1",
    )
    index.index_tokens(
        "page_2",
        "https://example.com/page2",
        ["good", "friends"],
        "Page 2",
    )
    index.index_tokens(
        "page_10",
        "https://example.com/page10",
        ["good"],
        "Page 10",
    )
    return index


def test_find_matching_doc_ids_ranks_higher_scoring_documents_first():
    index = build_ranked_index()

    result = find_matching_doc_ids(index, "good friends")

    assert result == ["page_1", "page_2"]


def test_find_matching_doc_ids_uses_natural_doc_order_for_ties():
    index = InvertedIndex()
    index.index_tokens("page_2", "https://example.com/page2", ["good"], "Page 2")
    index.index_tokens("page_10", "https://example.com/page10", ["good"], "Page 10")

    result = find_matching_doc_ids(index, "good")

    assert result == ["page_2", "page_10"]


def test_format_search_results_includes_rank_scores():
    index = build_ranked_index()

    result = format_search_results(index, "good friends")

    assert "Documents matching query: good friends" in result
    assert "[page_1] score=" in result
    assert "[page_2] score=" in result


def build_phrase_index() -> InvertedIndex:
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
        ["friends", "are", "good"],
        "Page 2",
    )
    index.index_tokens(
        "page_3",
        "https://example.com/page3",
        ["good", "old", "friends"],
        "Page 3",
    )
    index.index_tokens(
        "page_4",
        "https://example.com/page4",
        ["good", "friends", "matter", "good", "friends"],
        "Page 4",
    )
    return index


def test_is_exact_phrase_query_detects_wrapped_double_quotes():
    assert is_exact_phrase_query('"good friends"') is True
    assert is_exact_phrase_query("good friends") is False


def test_get_query_terms_removes_outer_quotes_for_phrase_queries():
    assert get_query_terms('"Good Friends"') == ["good", "friends"]


def test_document_contains_exact_phrase_returns_true_for_adjacent_terms():
    index = build_phrase_index()

    assert document_contains_exact_phrase(index, "page_1", ["good", "friends"]) is True
    assert document_contains_exact_phrase(index, "page_4", ["good", "friends"]) is True


def test_document_contains_exact_phrase_returns_false_for_non_adjacent_terms():
    index = build_phrase_index()

    assert document_contains_exact_phrase(index, "page_2", ["good", "friends"]) is False
    assert document_contains_exact_phrase(index, "page_3", ["good", "friends"]) is False


def test_find_matching_doc_ids_supports_exact_phrase_queries():
    index = build_phrase_index()

    result = find_matching_doc_ids(index, '"good friends"')

    assert result == ["page_4", "page_1"]


def test_format_search_results_labels_exact_phrase_queries():
    index = build_phrase_index()

    result = format_search_results(index, '"good friends"')

    assert "Documents matching exact phrase: good friends" in result
    assert "[page_1] score=" in result
    assert "[page_4] score=" in result


def test_format_search_results_handles_missing_exact_phrase():
    index = build_phrase_index()

    result = format_search_results(index, '"friends good"')

    assert result == "No documents found for exact phrase: friends good"


def test_get_term_suggestion_returns_close_match_for_unknown_word():
    index = build_sample_index()

    suggestion = get_term_suggestion(index, "indiffernce")

    assert suggestion == "indifference"


def test_get_term_suggestion_returns_none_for_known_word():
    index = build_sample_index()

    suggestion = get_term_suggestion(index, "good")

    assert suggestion is None


def test_get_query_suggestion_corrects_only_unknown_terms():
    index = build_sample_index()

    suggestion = get_query_suggestion(index, ["good", "freinds"])

    assert suggestion == ["good", "friends"]


def test_format_search_results_suggests_single_word_correction():
    index = build_sample_index()

    result = format_search_results(index, "indiffernce")

    assert result == (
        "No documents found for query: indiffernce\n"
        "Did you mean: indifference?"
    )


def test_format_search_results_suggests_multi_word_correction():
    index = build_sample_index()

    result = format_search_results(index, "good freinds")

    assert result == (
        "No documents found for query: good freinds\n"
        "Did you mean: good friends?"
    )


def test_format_search_results_suggests_exact_phrase_correction():
    index = build_sample_index()

    result = format_search_results(index, '"indiffernce is"')

    assert result == (
        "No documents found for exact phrase: indiffernce is\n"
        "Did you mean exact phrase: indifference is?"
    )


def test_format_search_results_does_not_suggest_when_terms_are_known_but_do_not_match_together():
    index = build_sample_index()

    result = format_search_results(index, "good indifference")

    assert result == "No documents found for query: good indifference"
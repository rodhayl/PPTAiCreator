"""Integration test for the local corpus search tool."""

from pathlib import Path

from src.tools.local_corpus_search import LocalCorpusSearch


def test_search_finds_documents(sample_corpus, monkeypatch):
    monkeypatch.setenv("MODE", "offline")
    # Override corpus directory
    search = LocalCorpusSearch(corpus_dir=Path(sample_corpus))
    results = search.search("renewable energy", k=1)
    assert results
    res = results[0]
    assert "renewable" in res.snippet.lower()
    assert res.score >= 0
    assert res.keyword_score >= 0
    assert res.semantic_score >= 0

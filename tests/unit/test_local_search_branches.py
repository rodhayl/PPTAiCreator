"""Branch coverage tests for hybrid local search helpers."""

from pathlib import Path

from src.tools.local_corpus_search import LocalCorpusSearch


def _make_corpus(tmp_path: Path) -> Path:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "a.md").write_text("title: A\n---\nalpha beta gamma", encoding="utf-8")
    return corpus


def test_normalize_and_snippet_helpers(tmp_path):
    search = LocalCorpusSearch(corpus_dir=_make_corpus(tmp_path), semantic_weight=0.0)

    assert search._normalize([]) == []
    assert search._normalize([0.0, 0.0]) == [0.0, 0.0]
    assert search._normalize([2.0, 2.0]) == [1.0, 1.0]

    snippet = search._snippet("alpha beta gamma", ["beta"], max_len=20)
    assert "beta" in snippet
    assert search._snippet("", ["x"]) == ""


def test_semantic_methods_fallbacks(tmp_path):
    search = LocalCorpusSearch(corpus_dir=_make_corpus(tmp_path), semantic_weight=1.0)

    # Force fallback branches
    search._semantic_available = False
    assert search._semantic_scores("alpha") == [0.0] * len(search._documents)

    search._semantic_available = True
    search._embed_model = None
    assert search._semantic_scores("alpha") == [0.0] * len(search._documents)

    search._faiss_index = None
    assert search._semantic_scores_faiss("alpha") == [0.0] * len(search._documents)

    search._chroma_collection = None
    assert search._semantic_scores_chroma("alpha") == [0.0] * len(search._documents)

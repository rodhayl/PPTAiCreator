"""Integration test for fact checking tool."""

from pathlib import Path

from src.tools.fact_check import FactCheckTool, extract_claims
from src.tools.local_corpus_search import LocalCorpusSearch


def test_fact_check_returns_evidence(sample_corpus, monkeypatch):
    search = LocalCorpusSearch(corpus_dir=Path(sample_corpus))
    fc = FactCheckTool(corpus_search=search)
    claims = extract_claims("Renewable energy reduces emissions.")
    evidences = fc.check(claims)
    assert evidences
    evidence = evidences[0]
    assert evidence.confidence >= 0.0

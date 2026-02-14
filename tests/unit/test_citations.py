"""Unit tests for the citation manager."""

from src.tools.citations import CitationManager
from src.schemas import Claim, Evidence


def test_citation_deduplication_and_order():
    cm = CitationManager()
    claim = Claim(text="Test claim")
    ev1 = Evidence(
        claim=claim,
        source="file:///doc1",
        snippet="text",
        published_at="2020-01-01",
        confidence=1.0,
    )
    ev2 = Evidence(
        claim=claim,
        source="file:///doc2",
        snippet="text",
        published_at="2020-01-01",
        confidence=1.0,
    )
    cm.register_evidence([ev1, ev2])
    # Second registration should not duplicate
    cm.register_evidence([ev1])
    refs = cm.build_references_slide()
    assert len(refs) == 2
    assert refs[0].startswith("[1]")
    assert refs[1].startswith("[2]")

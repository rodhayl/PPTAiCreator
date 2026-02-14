"""Fact checking tool built on top of the local corpus search.

This tool extracts factual claims from text and attempts to find supporting
evidence in the local corpus using `LocalCorpusSearch`.  A simple scoring
function assigns a confidence value to each claim based on how many hits
contain the claim terms.  Claims with low confidence can be flagged for
revision.
"""

from __future__ import annotations

import re
from typing import List

from ..schemas import Claim, Evidence
from .local_corpus_search import LocalCorpusSearch


def extract_claims(text: str) -> List[Claim]:
    """Extract simple factual claims from a block of text.

    This naive implementation splits sentences on periods and questions marks.
    It returns non‑empty trimmed strings as `Claim` objects.
    """
    sentences = re.split(r"[\.!?]", text)
    claims = []
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:
            claims.append(Claim(text=sentence))
    return claims


class FactCheckTool:
    """Performs claim extraction and evidence lookup in the local corpus."""

    def __init__(self, corpus_search: LocalCorpusSearch | None = None):
        self.search = corpus_search or LocalCorpusSearch()

    def check(self, claims: List[Claim], top_k: int = 3) -> List[Evidence]:
        """For each claim, retrieve supporting evidence and assign a confidence score."""
        evidences: List[Evidence] = []
        for claim in claims:
            results = self.search.search(claim.text, k=top_k)
            if not results:
                # No evidence found; assign low confidence
                evidences.append(
                    Evidence(
                        claim=claim,
                        source="",
                        snippet="",
                        published_at="",
                        confidence=0.0,
                    )
                )
                continue
            # Use the number of results to derive a confidence score (cap at 1.0)
            confidence = min(len(results) / top_k, 1.0)
            # Use the first result as evidence
            res = results[0]
            evidences.append(
                Evidence(
                    claim=claim,
                    source=res.source,
                    snippet=res.snippet,
                    published_at=res.published_at,
                    confidence=confidence,
                )
            )
        return evidences

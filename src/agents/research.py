"""Research and fact‑checking agent.

This agent extracts factual claims from the user input (and later could
include generated content) and searches the local corpus for supporting
evidence.  It records the claims and evidences on the pipeline state.
"""

from __future__ import annotations


from ..state import PipelineState
from ..tools.fact_check import FactCheckTool, extract_claims
from ..tools.citations import CitationManager


def run_research(state: PipelineState) -> PipelineState:
    if not state.user_input:
        state.errors.append("No user input provided for research")
        state.research_completed = False
        return state
    # Extract claims from the user input
    claims = extract_claims(state.user_input)
    state.claims = claims
    fact_checker = FactCheckTool()
    evidences = fact_checker.check(claims)
    state.evidences = evidences
    # Register citations (filter out evidences with empty sources)
    citation_manager = CitationManager()
    valid_evidences = [ev for ev in evidences if ev.source]
    citation_manager.register_evidence(valid_evidences)
    # Create citation markers for each valid evidence; store markers in state.citations
    state.citations = [
        citation_manager.get_citation_marker(ev) for ev in valid_evidences
    ]
    # Also store the reference entries (for later slide) in state for design agent
    state.references = citation_manager.build_references_slide()  # type: ignore
    state.research_completed = True
    return state

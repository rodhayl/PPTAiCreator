"""Internal Python API exposing the presentation pipeline.

This module defines functions used by integration and end‑to‑end tests to
exercise the pipeline without going through the GUI.  These functions
wrap the underlying pipeline builder defined in `graph.build_graph` and
return structured results for assertions in tests.
"""

from __future__ import annotations

from typing import Dict, Optional

from .state import PipelineState
from .graph.build_graph import run_pipeline


def run_e2e(user_input: str) -> Dict[str, Optional[str]]:
    """Run the full pipeline for the given user input and return key results.

    Returns a dictionary with keys:
        'pptx_path': path to the generated PPTX file
        'qa_report': string representation of QA report
    """
    state: PipelineState = run_pipeline(user_input)
    qa_str = None
    if state.qa_report:
        qa_str = (
            f"content:{state.qa_report.content_score}, "
            f"design:{state.qa_report.design_score}, "
            f"coherence:{state.qa_report.coherence_score}"
        )
    return {
        "pptx_path": state.pptx_path,
        "qa_report": qa_str,
    }

"""Wrapper functions that adapt agents for use in the orchestration graph."""

from __future__ import annotations

from ..state import PipelineState
from ..agents.brainstorm import run_brainstorm
from ..agents.research import run_research
from ..agents.content import run_content
from ..agents.design import run_design
from ..agents.qa import run_qa


def brainstorm_node(state: PipelineState) -> PipelineState:
    return run_brainstorm(state)


def research_node(state: PipelineState) -> PipelineState:
    return run_research(state)


def content_node(state: PipelineState) -> PipelineState:
    return run_content(state)


def design_node(state: PipelineState) -> PipelineState:
    return run_design(state)


def qa_node(state: PipelineState) -> PipelineState:
    return run_qa(state)

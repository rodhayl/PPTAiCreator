"""Shared state definitions for the LangGraph pipeline.

The pipeline operates on a dictionary-like state object that is passed from
node to node.  Each field corresponds to a piece of intermediate data.  For
simplicity, we use a Pydantic BaseModel here to validate that keys exist and
have the correct type.  The state is permissive and allows unknown keys so
that agents can attach arbitrary additional data.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict

from .schemas import PresentationOutline, SlideContent, Claim, Evidence, QAReport


class PipelineState(BaseModel):
    model_config = ConfigDict(extra="allow")
    """Container for passing data between LangGraph nodes.

    The model allows extra fields so agents can add custom data (e.g., logs).
    """

    user_input: Optional[str] = None
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: Optional[str] = None
    workflow_status: str = "pending"
    current_phase: str = "input"
    phase_version: int = 1
    approval_required: bool = False
    approval_status: str = "not_required"
    approval_notes: Optional[str] = None
    waiting_for_phase: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    outline: Optional[PresentationOutline] = None
    claims: List[Claim] = Field(default_factory=list)
    evidences: List[Evidence] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)
    content: List[SlideContent] = Field(default_factory=list)
    qa_report: Optional[QAReport] = None
    pptx_path: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    teaching_suggestions: List[str] = Field(default_factory=list)
    audit_flags: List[str] = Field(default_factory=list)
    preview_images: Dict[str, str] = Field(default_factory=dict)
    preview_manifest_path: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    educational_mode: bool = False  # Enable pedagogical enhancements when True
    template_name: Optional[str] = None  # Template to apply to presentation

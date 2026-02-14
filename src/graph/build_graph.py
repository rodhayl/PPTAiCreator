"""Build and execute the presentation generation pipeline.

This module defines a sequential pipeline and a checkpoint manager that can
persist run state to SQLite (offline fallback) or PostgreSQL (multi-user
production mode) through a shared SQL storage abstraction.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, UTC
from typing import Dict, Optional, Set

from ..config import get_config
from ..events import EVENT_STORE
from ..state import PipelineState
from ..storage import SQLCheckpointStore, sqlite_url_from_path
from ..agents.pedagogical_auditor import run_pedagogical_auditor
from ..workers.preview_worker import PreviewWorker
from .nodes import (
    brainstorm_node,
    research_node,
    content_node,
    design_node,
    qa_node,
)

logger = logging.getLogger(__name__)

PHASE_PLAN = [
    ("outline", brainstorm_node),
    ("research", research_node),
    ("content", content_node),
    ("design", design_node),
    ("qa", qa_node),
]


class CheckpointManager:
    """Checkpoint manager backed by SQLite/PostgreSQL via SQLAlchemy."""

    def __init__(
        self, db_path: Optional[str] = None, database_url: Optional[str] = None
    ):
        config = get_config()
        backend = (config.checkpoint_backend or "sqlite").lower()

        if database_url:
            resolved_database_url = database_url
        elif backend == "postgres" and config.postgres_url:
            resolved_database_url = config.postgres_url
        else:
            resolved_database_url = sqlite_url_from_path(db_path or config.db_path)

        self.store = SQLCheckpointStore(resolved_database_url)

    def record_log(self, run_id: int, message: str, level: str = "INFO") -> None:
        self.store.record_log(run_id=run_id, message=message, level=level)

    def start_run(self, state: PipelineState) -> int:
        return self.store.start_run(state)

    def save_state(self, state: PipelineState, execution_time: float = 0.0) -> None:
        self.store.save_state(state, execution_time=execution_time)

    def record_run_complete(
        self, state: "PipelineState", output_path: str, execution_time: float = 0.0
    ) -> int:
        return self.store.record_run_complete(
            state, output_path=output_path, execution_time=execution_time
        )

    def get_run_details(self, run_id: int) -> Optional[Dict]:
        return self.store.get_run_details(run_id)

    def list_runs(self, limit: int = 100) -> list:
        return self.store.list_runs(limit=limit)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _execute_phases(
    state: PipelineState,
    cp: CheckpointManager,
    run_id: int,
    start_index: int,
    gated_phases: Set[str],
    auto_approve: bool,
) -> PipelineState:
    preview_worker = PreviewWorker()

    for phase_name, phase_func in PHASE_PLAN[start_index:]:
        state.current_phase = phase_name
        state.updated_at = _now_iso()
        state.workflow_status = "running"
        cp.save_state(state)
        cp.record_log(run_id, f"Entering phase: {phase_name}")
        EVENT_STORE.publish(
            run_id,
            "phase_started",
            {
                "phase": phase_name,
                "session_id": state.session_id,
                "workflow_status": state.workflow_status,
            },
        )

        state = phase_func(state)
        if phase_name == "design":
            state = preview_worker.generate_previews(state)
            EVENT_STORE.publish(
                run_id,
                "previews_updated",
                {
                    "phase": phase_name,
                    "preview_manifest_path": state.preview_manifest_path,
                    "preview_count": len(state.preview_images or {}),
                },
            )
        if phase_name in {"outline", "research", "design"}:
            state = run_pedagogical_auditor(state, phase=phase_name)
        state.updated_at = _now_iso()
        state.workflow_status = "running"
        cp.save_state(state)
        EVENT_STORE.publish(
            run_id,
            "phase_completed",
            {
                "phase": phase_name,
                "workflow_status": state.workflow_status,
                "teaching_suggestions": state.teaching_suggestions,
                "warnings": state.warnings,
            },
        )

        if (
            phase_name in gated_phases
            and phase_name in {"outline", "research", "design"}
            and not auto_approve
        ):
            state.approval_required = True
            state.approval_status = "pending"
            state.waiting_for_phase = phase_name
            state.workflow_status = "waiting_for_approval"
            cp.save_state(state)
            cp.record_log(run_id, f"Paused for approval after phase: {phase_name}")
            EVENT_STORE.publish(
                run_id,
                "approval_required",
                {
                    "phase": phase_name,
                    "approval_status": state.approval_status,
                    "workflow_status": state.workflow_status,
                },
            )
            return state

    state.approval_required = False
    if state.approval_status == "not_required":
        state.approval_status = "approved"
    state.waiting_for_phase = None
    return state


def run_pipeline(
    user_input: str,
    educational_mode: bool = False,
    template_name: Optional[str] = None,
    session_id: Optional[str] = None,
    approval_phases: Optional[Set[str]] = None,
    auto_approve: bool = True,
) -> PipelineState:
    """Execute the pipeline synchronously and return the final state.

    Args:
        user_input: The presentation topic/brief
        educational_mode: If True, generate with pedagogical enhancements
        template_name: Optional template name to apply to presentation
        session_id: Optional external session identifier
        approval_phases: Optional set of phases requiring human approval
        auto_approve: If False, pipeline pauses on configured approval phases
    """
    start_time = time.time()
    gated_phases = approval_phases or set()

    state = PipelineState(
        user_input=user_input,
        educational_mode=educational_mode,
        template_name=template_name,
    )
    if session_id:
        state.session_id = session_id
    state.created_at = _now_iso()
    state.updated_at = state.created_at
    state.workflow_status = "running"
    state.current_phase = "initializing"

    cp = CheckpointManager()
    run_id = cp.start_run(state)
    cp.record_log(run_id, "Run started")
    EVENT_STORE.publish(
        run_id,
        "run_started",
        {
            "session_id": state.session_id,
            "workflow_status": state.workflow_status,
            "current_phase": state.current_phase,
        },
    )

    state = _execute_phases(
        state=state,
        cp=cp,
        run_id=run_id,
        start_index=0,
        gated_phases=gated_phases,
        auto_approve=auto_approve,
    )

    if state.workflow_status == "waiting_for_approval":
        return state

    # Calculate execution time
    execution_time = time.time() - start_time

    # Write complete run to database
    cp.record_run_complete(state, state.pptx_path or "", execution_time)
    cp.record_log(run_id, "Run completed")
    EVENT_STORE.publish(
        run_id,
        "run_completed",
        {
            "workflow_status": "completed",
            "pptx_path": state.pptx_path,
            "current_phase": state.current_phase,
            "approval_status": state.approval_status,
        },
    )
    return state


def resume_pipeline(
    run_id: int,
    approval_notes: Optional[str] = None,
    auto_approve: bool = True,
    approval_phases: Optional[Set[str]] = None,
) -> PipelineState:
    """Resume a paused pipeline after user approval/modification."""
    cp = CheckpointManager()
    details = cp.get_run_details(run_id)
    if not details or not details.get("state_blob"):
        raise ValueError(f"Run {run_id} could not be resumed")

    state = PipelineState(**details["state_blob"])
    state.run_id = str(run_id)
    state.approval_required = False
    state.approval_status = "approved"
    state.approval_notes = approval_notes
    state.workflow_status = "running"
    state.updated_at = _now_iso()
    cp.save_state(state)
    cp.record_log(run_id, "Run resumed after approval")
    EVENT_STORE.publish(
        run_id,
        "run_resumed",
        {
            "workflow_status": state.workflow_status,
            "approval_status": state.approval_status,
            "approval_notes": approval_notes,
        },
    )

    waiting_phase = state.waiting_for_phase or state.current_phase
    phase_names = [phase_name for phase_name, _ in PHASE_PLAN]
    if waiting_phase in phase_names:
        start_index = phase_names.index(waiting_phase) + 1
    else:
        start_index = 0

    start_time = time.time()
    state = _execute_phases(
        state=state,
        cp=cp,
        run_id=run_id,
        start_index=start_index,
        gated_phases=approval_phases or set(),
        auto_approve=auto_approve,
    )

    if state.workflow_status == "waiting_for_approval":
        return state

    execution_time = time.time() - start_time
    cp.record_run_complete(state, state.pptx_path or "", execution_time)
    cp.record_log(run_id, "Run completed after resume")
    EVENT_STORE.publish(
        run_id,
        "run_completed",
        {
            "workflow_status": "completed",
            "pptx_path": state.pptx_path,
            "current_phase": state.current_phase,
            "approval_status": state.approval_status,
        },
    )
    return state

"""FastAPI server exposing HTTP endpoints for the PPTX agent.

The API allows clients to start a presentation generation run, poll for
status, and download artifacts.  It uses the same pipeline functions as
the internal Python API and writes run metadata to the SQLite database via
the checkpoint manager.
"""

from __future__ import annotations

import json
import threading
import uuid
from pathlib import Path
from typing import Dict, Optional, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from .events import EVENT_STORE, format_sse_event, sleep_seconds
from .graph.build_graph import run_pipeline, resume_pipeline, CheckpointManager

app = FastAPI(title="PPTX Agent API")

# Thread-safe access to run storage
_runs: Dict[int, Dict[str, Optional[str]]] = {}
_runs_lock = threading.RLock()


@app.post("/sessions")
def create_session(payload: Optional[Dict[str, Any]] = None):
    """Create a new logical user session for concurrent multi-user runs."""
    session_id = payload.get("session_id") if payload else None
    if not session_id:
        session_id = str(uuid.uuid4())
    return {"session_id": session_id}


@app.post("/run")
def start_run(payload: Dict[str, Any]):
    """Start a new presentation generation run."""
    user_input = payload.get("user_input")
    if not user_input:
        raise HTTPException(status_code=400, detail="user_input is required")

    session_id = payload.get("session_id")
    educational_mode = bool(payload.get("educational_mode", False))
    template_name = payload.get("template_name")
    auto_approve = bool(payload.get("auto_approve", False))
    approval_phases_raw = payload.get("approval_phases")
    if approval_phases_raw is None:
        approval_phases_raw = ["outline", "research", "design"]
    approval_phases = (
        set(approval_phases_raw) if isinstance(approval_phases_raw, list) else set()
    )

    # Run pipeline (records run lifecycle state internally)
    state = run_pipeline(
        user_input,
        educational_mode=educational_mode,
        template_name=template_name,
        session_id=session_id,
        approval_phases=approval_phases,
        auto_approve=auto_approve,
    )

    qa_str = None
    if state.qa_report:
        qa_str = json.dumps(state.qa_report.model_dump())

    run_id = int(state.run_id) if state.run_id else 0
    if run_id <= 0:
        cp = CheckpointManager()
        runs = cp.list_runs(limit=1)
        run_id = runs[0]["id"] if runs else 1

    # Thread-safe write to run storage
    with _runs_lock:
        _runs[run_id] = {
            "pptx_path": state.pptx_path,
            "qa_report": qa_str,
            "session_id": state.session_id,
            "workflow_status": state.workflow_status,
            "current_phase": state.current_phase,
            "approval_status": state.approval_status,
        }
    EVENT_STORE.publish(
        run_id,
        "run_status_cached",
        {
            "workflow_status": state.workflow_status,
            "current_phase": state.current_phase,
            "approval_status": state.approval_status,
        },
    )
    return {
        "run_id": run_id,
        "session_id": state.session_id,
        "status": state.workflow_status,
    }


@app.get("/status/{run_id}")
def get_status(run_id: int):
    """Get the status and QA report of a run."""
    # Thread-safe read from run storage
    with _runs_lock:
        if run_id not in _runs:
            cp = CheckpointManager()
            details = cp.get_run_details(run_id)
            if not details:
                raise HTTPException(status_code=404, detail="Run not found")
            return details
        return _runs[run_id]


@app.get("/runs/{run_id}")
def get_run_details(run_id: int):
    """Get full persisted run details, including workflow and approval state."""
    cp = CheckpointManager()
    details = cp.get_run_details(run_id)
    if not details:
        raise HTTPException(status_code=404, detail="Run not found")
    return details


@app.post("/runs/{run_id}/approve")
def approve_run(run_id: int, payload: Optional[Dict[str, Any]] = None):
    """Approve and resume a paused run."""
    notes = payload.get("notes") if payload else None
    auto_approve = bool(payload.get("auto_approve", True)) if payload else True
    approval_phases_raw = payload.get("approval_phases") if payload else []
    approval_phases = (
        set(approval_phases_raw) if isinstance(approval_phases_raw, list) else set()
    )

    try:
        state = resume_pipeline(
            run_id=run_id,
            approval_notes=notes,
            auto_approve=auto_approve,
            approval_phases=approval_phases,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    with _runs_lock:
        _runs[run_id] = {
            "pptx_path": state.pptx_path,
            "qa_report": (
                json.dumps(state.qa_report.model_dump()) if state.qa_report else None
            ),
            "session_id": state.session_id,
            "workflow_status": state.workflow_status,
            "current_phase": state.current_phase,
            "approval_status": state.approval_status,
        }

    EVENT_STORE.publish(
        run_id,
        "approval_processed",
        {
            "workflow_status": state.workflow_status,
            "current_phase": state.current_phase,
            "approval_status": state.approval_status,
        },
    )

    return {
        "run_id": run_id,
        "status": state.workflow_status,
        "current_phase": state.current_phase,
        "approval_status": state.approval_status,
    }


@app.get("/runs/{run_id}/events")
def get_run_events(run_id: int, since_ts: Optional[str] = None):
    """List run events for polling clients."""
    cp = CheckpointManager()
    details = cp.get_run_details(run_id)
    if not details:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        "run_id": run_id,
        "events": EVENT_STORE.list_events(run_id, since_ts=since_ts),
    }


@app.get("/runs/{run_id}/events/stream")
def stream_run_events(run_id: int, since_ts: Optional[str] = None, once: bool = False):
    """SSE stream of run events for real-time UI updates."""
    cp = CheckpointManager()
    details = cp.get_run_details(run_id)
    if not details:
        raise HTTPException(status_code=404, detail="Run not found")

    def event_generator():
        if once:
            yield format_sse_event(
                {
                    "run_id": run_id,
                    "type": "heartbeat",
                    "payload": {"once": True},
                }
            )
            return

        last_seen = since_ts
        idle_ticks = 0
        while idle_ticks < 40:
            new_events = EVENT_STORE.list_events(run_id, since_ts=last_seen)
            if new_events:
                idle_ticks = 0
                for event in new_events:
                    last_seen = event.get("ts")
                    yield format_sse_event(event)
            else:
                idle_ticks += 1
                yield format_sse_event(
                    {
                        "run_id": run_id,
                        "type": "heartbeat",
                        "payload": {"idle_ticks": idle_ticks},
                    }
                )
            sleep_seconds(0.25)

        yield format_sse_event(
            {
                "run_id": run_id,
                "type": "stream_closed",
                "payload": {"reason": "idle_timeout"},
            }
        )

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/artifact/{run_id}")
def get_artifact(run_id: int):
    """Download the generated PPTX file for the given run."""
    # Thread-safe read from run storage
    with _runs_lock:
        run = _runs.get(run_id)
        if not run or not run.get("pptx_path"):
            raise HTTPException(status_code=404, detail="Artifact not found")
        pptx_path = Path(run["pptx_path"])

    # Validate path is within artifacts directory (security)
    artifacts_dir = Path("artifacts").resolve()
    try:
        resolved_path = pptx_path.resolve()
        if not resolved_path.is_relative_to(artifacts_dir):
            raise HTTPException(status_code=403, detail="Access denied")
        if not resolved_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        return FileResponse(str(resolved_path), filename=resolved_path.name)
    except (ValueError, OSError):
        raise HTTPException(status_code=404, detail="File not found")

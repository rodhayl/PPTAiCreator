from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class RunRecord(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_uuid: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    status: Mapped[str] = mapped_column(String(32), default="running")
    workflow_phase: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    approval_required: Mapped[bool] = mapped_column(Boolean, default=False)
    approval_status: Mapped[str] = mapped_column(String(32), default="not_required")

    user_input: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    qa_scores: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    outline: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    research: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    qa_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    educational_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    execution_time_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    error_messages: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    state_blob: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preview_manifest: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class LogRecord(Base):
    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(Integer, index=True)
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    level: Mapped[str] = mapped_column(String(16), default="INFO")
    message: Mapped[str] = mapped_column(Text)


class SQLCheckpointStore:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url, future=True)
        Base.metadata.create_all(self.engine)

    def close(self) -> None:
        self.engine.dispose()

    def __del__(self):
        try:
            self.engine.dispose()
        except Exception:
            pass

    @staticmethod
    def _serialize_outline(outline: Any) -> Optional[str]:
        if not outline:
            return None
        try:
            if hasattr(outline, "model_dump"):
                return json.dumps(outline.model_dump())
            return json.dumps(outline)
        except Exception:
            return None

    @staticmethod
    def _serialize_content(content: Any) -> Optional[str]:
        if not content:
            return None
        try:
            serialized = []
            for item in content:
                if hasattr(item, "model_dump"):
                    serialized.append(item.model_dump())
                else:
                    serialized.append(item)
            return json.dumps(serialized)
        except Exception:
            return None

    @staticmethod
    def _serialize_research(state: Any) -> Optional[str]:
        try:
            claims = [
                c.model_dump() if hasattr(c, "model_dump") else c
                for c in (state.claims or [])
            ]
            evidences = [
                e.model_dump() if hasattr(e, "model_dump") else e
                for e in (state.evidences or [])
            ]
            return json.dumps(
                {
                    "claims": claims,
                    "evidences": evidences,
                    "citations": state.citations or [],
                    "references": state.references or [],
                }
            )
        except Exception:
            return None

    def start_run(self, state: Any) -> int:
        run_uuid = str(uuid.uuid4())
        state.run_id = state.run_id or run_uuid
        with Session(self.engine) as session:
            row = RunRecord(
                run_uuid=run_uuid,
                session_id=state.session_id,
                status=state.workflow_status,
                workflow_phase=state.current_phase,
                approval_required=state.approval_required,
                approval_status=state.approval_status,
                user_input=state.user_input,
                educational_mode=bool(state.educational_mode),
                state_blob=json.dumps(state.model_dump(mode="json")),
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            state.run_id = str(row.id)
            return row.id

    def save_state(self, state: Any, execution_time: float = 0.0) -> None:
        if not state.run_id:
            return
        run_id = int(state.run_id)
        now = datetime.now(UTC)

        qa_report = state.qa_report
        qa_scores = {
            "content": qa_report.content_score if qa_report else 0.0,
            "design": qa_report.design_score if qa_report else 0.0,
            "coherence": qa_report.coherence_score if qa_report else 0.0,
        }

        with Session(self.engine) as session:
            row = session.get(RunRecord, run_id)
            if not row:
                return

            row.updated_at = now
            row.session_id = state.session_id
            row.status = state.workflow_status
            row.workflow_phase = state.current_phase
            row.approval_required = bool(state.approval_required)
            row.approval_status = state.approval_status
            row.user_input = state.user_input
            row.output_path = state.pptx_path
            row.qa_scores = json.dumps(qa_scores)
            row.outline = self._serialize_outline(state.outline)
            row.content = self._serialize_content(state.content)
            row.research = self._serialize_research(state)
            row.qa_feedback = qa_report.feedback if qa_report else None
            row.model_info = json.dumps(
                {
                    "educational_mode": state.educational_mode,
                    "current_phase": state.current_phase,
                    "updated_at": now.isoformat(),
                }
            )
            row.educational_mode = bool(state.educational_mode)
            row.execution_time_seconds = execution_time
            row.error_messages = json.dumps(state.errors or [])
            row.preview_manifest = state.preview_manifest_path
            row.state_blob = json.dumps(state.model_dump(mode="json"))
            session.commit()

    def record_log(self, run_id: int, message: str, level: str = "INFO") -> None:
        with Session(self.engine) as session:
            session.add(LogRecord(run_id=run_id, level=level, message=message))
            session.commit()

    def record_run_complete(
        self, state: Any, output_path: str, execution_time: float = 0.0
    ) -> int:
        if not state.run_id:
            self.start_run(state)
        state.workflow_status = "completed"
        state.current_phase = "completed"
        state.pptx_path = output_path or state.pptx_path
        self.save_state(state, execution_time=execution_time)
        return int(state.run_id)

    def get_run_details(self, run_id: int) -> Optional[Dict[str, Any]]:
        with Session(self.engine) as session:
            row = session.get(RunRecord, run_id)
            if not row:
                return None
            return {
                "id": row.id,
                "run_uuid": row.run_uuid,
                "session_id": row.session_id,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                "input": row.user_input,
                "status": row.status,
                "workflow_phase": row.workflow_phase,
                "approval_required": row.approval_required,
                "approval_status": row.approval_status,
                "output_path": row.output_path,
                "outline": json.loads(row.outline) if row.outline else None,
                "content": json.loads(row.content) if row.content else None,
                "research": json.loads(row.research) if row.research else None,
                "qa_scores": json.loads(row.qa_scores) if row.qa_scores else None,
                "qa_feedback": row.qa_feedback,
                "educational_mode": row.educational_mode,
                "execution_time_seconds": row.execution_time_seconds,
                "model_info": json.loads(row.model_info) if row.model_info else None,
                "error_messages": (
                    json.loads(row.error_messages) if row.error_messages else []
                ),
                "preview_manifest": row.preview_manifest,
                "state_blob": json.loads(row.state_blob) if row.state_blob else None,
            }

    def list_runs(self, limit: int = 100) -> list[Dict[str, Any]]:
        with Session(self.engine) as session:
            query = select(RunRecord).order_by(RunRecord.created_at.desc()).limit(limit)
            rows = session.execute(query).scalars().all()
            return [
                {
                    "id": row.id,
                    "run_uuid": row.run_uuid,
                    "session_id": row.session_id,
                    "created_at": (
                        row.created_at.isoformat() if row.created_at else None
                    ),
                    "input": row.user_input,
                    "output_path": row.output_path,
                    "status": row.status,
                    "workflow_phase": row.workflow_phase,
                    "qa_scores": json.loads(row.qa_scores) if row.qa_scores else None,
                    "execution_time_seconds": row.execution_time_seconds,
                    "educational_mode": row.educational_mode,
                    "approval_status": row.approval_status,
                }
                for row in rows
            ]


class NoopEventBus:
    def publish(self, channel: str, payload: Dict[str, Any]) -> None:
        return


class RedisEventBus:
    def __init__(self, redis_url: str):
        try:
            import redis
        except Exception as exc:
            raise RuntimeError("redis package is required for RedisEventBus") from exc

        self._client = redis.from_url(redis_url, decode_responses=True)

    def publish(self, channel: str, payload: Dict[str, Any]) -> None:
        self._client.publish(channel, json.dumps(payload))


def sqlite_url_from_path(db_path: str) -> str:
    path = Path(db_path).resolve()
    return f"sqlite:///{path.as_posix()}"

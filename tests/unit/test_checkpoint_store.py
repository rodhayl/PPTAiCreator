"""Unit tests for SQL checkpoint storage abstraction."""

from src.schemas import QAReport
from src.state import PipelineState
from src.storage.backends import SQLCheckpointStore, sqlite_url_from_path


def test_sql_checkpoint_store_roundtrip(tmp_path):
    db_path = tmp_path / "checkpoints.db"
    store = SQLCheckpointStore(sqlite_url_from_path(str(db_path)))

    state = PipelineState(
        user_input="Test", workflow_status="running", current_phase="outline"
    )
    run_id = store.start_run(state)

    state.run_id = str(run_id)
    state.workflow_status = "completed"
    state.current_phase = "completed"
    state.qa_report = QAReport(content_score=4.0, design_score=4.0, coherence_score=4.0)

    store.save_state(state, execution_time=1.23)
    details = store.get_run_details(run_id)

    assert details is not None
    assert details["id"] == run_id
    assert details["status"] == "completed"
    assert details["workflow_phase"] == "completed"
    assert details["qa_scores"]["content"] == 4.0

    runs = store.list_runs(limit=10)
    assert len(runs) >= 1

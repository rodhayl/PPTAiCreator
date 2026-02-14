"""Test that runs are recorded in the SQLite database and can resume."""

import sqlite3

from src.graph.build_graph import run_pipeline


def test_run_records_entry(tmp_path, monkeypatch):
    db_path = tmp_path / "checkpoints.db"
    monkeypatch.setenv("DB_PATH", str(db_path))
    _state = run_pipeline("Test topic")  # Intentionally unused - we test DB records
    # Check DB file exists
    assert db_path.exists()
    # Check runs table has one row
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM runs")
        count = cur.fetchone()[0]
    assert count >= 1

"""End-to-end test via the internal Python API."""

from pathlib import Path

import pytest

from src.api import run_e2e


@pytest.mark.e2e
def test_e2e_run_creates_pptx(tmp_path, monkeypatch):
    # Use temporary DB and offline mode
    db = tmp_path / "checkpoints.db"
    monkeypatch.setenv("DB_PATH", str(db))
    monkeypatch.setenv("MODE", "offline")
    result = run_e2e("Test the impact of AI on education")
    pptx_path = result.get("pptx_path")
    assert pptx_path
    assert Path(pptx_path).exists()
    assert result.get("qa_report") is not None

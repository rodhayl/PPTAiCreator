"""Visual regression checks for generated slide previews."""

import hashlib
from pathlib import Path

from src.schemas import SlideContent
from src.state import PipelineState
from src.workers.preview_worker import PreviewWorker


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_preview_visual_regression_baseline(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    state = PipelineState(
        user_input="Visual regression topic",
        run_id="vr-001",
        content=[
            SlideContent(
                title="Intro", bullets=["Point one", "Point two", "Point three"]
            ),
        ],
    )

    worker = PreviewWorker(width=1280, height=720)
    state = worker.generate_previews(state)

    if not state.preview_images:
        assert any("Pillow" in warning for warning in state.warnings)
        return

    first_file = Path(next(iter(state.preview_images.values())))
    assert first_file.exists()
    digest_first = _sha256(first_file)

    state2 = PipelineState(
        user_input="Visual regression topic",
        run_id="vr-002",
        content=[
            SlideContent(
                title="Intro", bullets=["Point one", "Point two", "Point three"]
            ),
        ],
    )
    state2 = worker.generate_previews(state2)
    second_file = Path(next(iter(state2.preview_images.values())))
    digest_second = _sha256(second_file)

    assert digest_first == digest_second, "Preview render output changed unexpectedly"

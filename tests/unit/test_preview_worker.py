"""Unit tests for preview worker artifact generation."""

from pathlib import Path

from src.schemas import SlideContent
from src.state import PipelineState
from src.workers.preview_worker import PreviewWorker


def test_preview_worker_generates_manifest(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    try:
        import PIL  # noqa: F401

        pillow_available = True
    except Exception:
        pillow_available = False

    state = PipelineState(
        user_input="Topic",
        run_id="123",
        content=[
            SlideContent(title="Slide A", bullets=["A1", "A2"]),
            SlideContent(title="Slide B", bullets=["B1"]),
        ],
    )

    worker = PreviewWorker(width=1280, height=720)
    state = worker.generate_previews(state)

    if pillow_available:
        assert state.preview_manifest_path is not None
        manifest = Path(state.preview_manifest_path)
        assert manifest.exists()
        assert len(state.preview_images) == 2
    else:
        assert state.preview_manifest_path is None
        assert len(state.preview_images) == 0
        assert any("Pillow" in warning for warning in state.warnings)


def test_preview_worker_safe_font_fallback(monkeypatch):
    try:
        from PIL import ImageFont
    except Exception:
        return

    worker = PreviewWorker()
    sentinel = object()

    monkeypatch.setattr(
        ImageFont,
        "truetype",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("no font")),
    )
    monkeypatch.setattr(ImageFont, "load_default", lambda: sentinel)

    assert worker._safe_font(12) is sentinel


def test_preview_worker_render_handles_empty_and_wrapped_bullets(tmp_path):
    try:
        import PIL  # noqa: F401
    except Exception:
        return

    worker = PreviewWorker(width=640, height=360)
    output_file = Path(tmp_path) / "slide.png"
    long_bullet = " ".join(["verylongword"] * 80)

    worker._render_slide("Title", ["", long_bullet], output_file)
    assert output_file.exists()

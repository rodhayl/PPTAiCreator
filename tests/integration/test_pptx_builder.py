"""Integration test for PPTX builder."""

from src.tools.pptx_builder import build_presentation
from src.schemas import SlideContent


def test_build_presentation(tmp_path):
    """Test basic presentation building with enhanced features."""
    slides = [
        SlideContent(
            title="Slide 1", bullets=["Point 1", "Point 2"], speaker_notes="Notes"
        ),
        SlideContent(title="Slide 2", bullets=["Point A"]),
    ]
    references = ["[1] Example (2020) — file:///doc1"]
    output = tmp_path / "test.pptx"
    build_presentation(slides, references, output)
    assert output.exists()
    # Load with python-pptx and check slides count
    # Now includes: 1 title + 2 content + 1 references = 4 slides
    from pptx import Presentation

    prs = Presentation(str(output))
    assert len(prs.slides) == 4  # Updated to reflect title slide addition

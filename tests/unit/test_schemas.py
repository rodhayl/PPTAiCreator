"""Unit tests for the Pydantic schemas."""

import pytest

from src.schemas import SlideContent, QAReport


def test_slide_content_requires_title():
    with pytest.raises(Exception):
        SlideContent(title="", bullets=[])

    slide = SlideContent(title="Test", bullets=["One"])
    assert slide.title == "Test"
    assert slide.bullets == ["One"]


def test_qa_report_score_range():
    with pytest.raises(Exception):
        QAReport(content_score=0, design_score=5, coherence_score=5)
    with pytest.raises(Exception):
        QAReport(content_score=6, design_score=5, coherence_score=5)
    report = QAReport(content_score=3, design_score=4, coherence_score=5)
    assert report.content_score == 3

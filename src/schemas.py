"""Pydantic schemas for structured data used throughout the system.

The agents communicate via structured JSON data that is validated by these
schemas.  They are intentionally simple to encourage clear and predictable
outputs from language models.  When models fail to produce valid JSON, the
repair mechanisms in the model registry handle recovery.
"""

from __future__ import annotations

from typing import List, Optional, Literal

from pydantic import BaseModel, Field, field_validator
from typing import Union


class FormattedBullet(BaseModel):
    """A bullet point with optional formatting.

    Attributes:
        text: The text content of the bullet
        level: Nesting level (0, 1, 2) for hierarchical bullets
        bold: Whether the bullet should be bold
        italic: Whether the bullet should be italic
        emphasis: Highlight key terms with emphasis styling
    """

    text: str
    level: int = 0
    bold: bool = False
    italic: bool = False
    emphasis: bool = False


class LearningObjective(BaseModel):
    """A pedagogical learning objective following SMART criteria.

    Attributes:
        objective: Clear statement of what learners will be able to do
        bloom_level: Cognitive level from Bloom's taxonomy
        assessment: How achievement of this objective will be measured
    """

    objective: str
    bloom_level: Literal[
        "remember", "understand", "apply", "analyze", "evaluate", "create"
    ] = "understand"
    assessment: Optional[str] = None


class SlideContent(BaseModel):
    """Structured representation of a single slide.

    Attributes:
        title: The title of the slide.
        bullets: A list of bullet points (strings or FormattedBullet objects).
        speaker_notes: Optional longer text to display as speaker notes.
        image_description: Optional description of an image to include.
        citations: A list of citation identifiers corresponding to entries
            in the final references slide.
        engagement_hook: Optional opening hook to capture attention (pedagogical)
        active_learning_prompt: Optional activity or discussion prompt (pedagogical)
        formative_check: Optional quick assessment question (pedagogical)
        bloom_level: Cognitive level of content on this slide (pedagogical)
        time_estimate: Optional estimated minutes for presenting this slide
    """

    title: str
    bullets: List[Union[str, FormattedBullet]] = Field(default_factory=list)
    speaker_notes: Optional[str] = None
    image_description: Optional[str] = None
    citations: List[str] = Field(default_factory=list)

    # Pedagogical fields (optional, for educational presentations)
    engagement_hook: Optional[str] = None
    active_learning_prompt: Optional[str] = None
    formative_check: Optional[str] = None
    bloom_level: Optional[
        Literal["remember", "understand", "apply", "analyze", "evaluate", "create"]
    ] = None
    time_estimate: Optional[float] = None  # Minutes

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Slide title must not be empty")
        return v


class PresentationOutline(BaseModel):
    """High level outline for a presentation.

    Attributes:
        topic: The main topic of the presentation.
        audience: The intended audience description.
        sections: A list of section headings.  Each section corresponds to
            one or more slides generated later.
        learning_objectives: Optional list of SMART learning objectives (pedagogical)
        prerequisite_knowledge: Optional list of prior knowledge needed (pedagogical)
        educational_level: Optional target education level (pedagogical)
    """

    topic: str
    audience: str
    sections: List[str]

    # Pedagogical fields (optional, for educational presentations)
    learning_objectives: Optional[List[LearningObjective]] = Field(default_factory=list)
    prerequisite_knowledge: Optional[List[str]] = Field(default_factory=list)
    educational_level: Optional[str] = None

    @field_validator("sections")
    @classmethod
    def sections_not_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("Outline must contain at least one section")
        return v


class Claim(BaseModel):
    """A factual claim extracted from the user prompt or generated content."""

    text: str


class Evidence(BaseModel):
    """Evidence supporting a claim.

    Attributes:
        claim: The claim being supported.
        source: A citation identifier (e.g. file path or URL).
        snippet: A short excerpt from the source showing evidence.
        published_at: Publication date in ISO 8601 format.
        confidence: A float between 0 and 1 representing the confidence in
            this evidence supporting the claim.
    """

    claim: Claim
    source: str
    snippet: str
    published_at: str
    confidence: float

    @field_validator("confidence")
    @classmethod
    def confidence_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        return v


class QAReport(BaseModel):
    """Quality assurance report with scores and feedback.

    Attributes:
        content_score: Score between 1 and 5 assessing the factual and
            structural quality of the content.
        design_score: Score between 1 and 5 assessing visual layout and
            cohesion of the slides.
        coherence_score: Score between 1 and 5 assessing narrative flow.
        feedback: Optional freeform feedback text.
        pedagogical_score: Optional score for educational effectiveness (pedagogical)
        engagement_score: Optional score for learner motivation (pedagogical)
        clarity_score: Optional score for audience-appropriate language (pedagogical)
    """

    content_score: float
    design_score: float
    coherence_score: float
    feedback: Optional[str] = None

    # Pedagogical fields (optional, for educational presentations)
    pedagogical_score: Optional[float] = None
    engagement_score: Optional[float] = None
    clarity_score: Optional[float] = None

    @field_validator("content_score", "design_score", "coherence_score")
    @classmethod
    def score_range(cls, v: float) -> float:
        if not 1.0 <= v <= 5.0:
            raise ValueError("QA scores must be between 1 and 5")
        return v

    @field_validator("pedagogical_score", "engagement_score", "clarity_score")
    @classmethod
    def optional_score_range(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not 1.0 <= v <= 5.0:
            raise ValueError("Pedagogical scores must be between 1 and 5")
        return v

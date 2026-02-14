"""Enhanced Quality assurance agent with pedagogical evaluation.

This agent evaluates presentation quality with additional pedagogical criteria
for educational presentations, including learning effectiveness, engagement,
and clarity for target audience.
"""

from __future__ import annotations

from ..state import PipelineState
from ..schemas import QAReport
from ..models.ai_interface import get_ai_interface
from ..utils import parse_json_with_repair


def run_qa(state: PipelineState) -> PipelineState:
    """Evaluate presentation quality and generate improvement feedback.

    This agent reviews the generated slides and provides scores for content,
    design, and coherence. When educational_mode is enabled, it also evaluates
    pedagogical effectiveness, engagement, and clarity for learners.
    """
    # Input validation - check if content exists
    if not state.content:
        state.errors.append("No slide content available for quality assurance")
        return state

    # Use centralized AI interface
    ai = get_ai_interface()

    # Build context about the presentation
    num_slides = len(state.content) if state.content else 0
    slide_titles = [slide.title for slide in state.content] if state.content else []

    if state.educational_mode:
        prompt = _get_educational_prompt(state, num_slides, slide_titles)
    else:
        prompt = _get_standard_prompt(state, num_slides, slide_titles)

    try:
        response = ai.generate(prompt, agent="qa")
    except Exception:
        response = None
    # Parse JSON from response with repair logic
    result = parse_json_with_repair(response.content) if response else {}

    try:
        report = QAReport(**result)
        # Ensure scores are within valid range
        report.content_score = max(1.0, min(5.0, report.content_score))
        report.design_score = max(1.0, min(5.0, report.design_score))
        report.coherence_score = max(1.0, min(5.0, report.coherence_score))

        if report.pedagogical_score:
            report.pedagogical_score = max(1.0, min(5.0, report.pedagogical_score))
        if report.engagement_score:
            report.engagement_score = max(1.0, min(5.0, report.engagement_score))
        if report.clarity_score:
            report.clarity_score = max(1.0, min(5.0, report.clarity_score))
    except Exception as e:
        # Deterministic fallback when model output cannot be parsed
        content_score = 3.0
        design_score = 3.0
        coherence_score = 3.0

        if state.content:
            slide_count = len(state.content)
            avg_bullets = sum(
                len(slide.bullets or []) for slide in state.content
            ) / max(1, slide_count)
            if slide_count >= 3 and avg_bullets >= 2:
                content_score = 3.5
                design_score = 3.3
                coherence_score = 3.4

        report = QAReport(
            content_score=content_score,
            design_score=design_score,
            coherence_score=coherence_score,
            feedback=f"Deterministic QA fallback used because model response parsing failed: {str(e)}",
        )
    state.qa_report = report
    return state


def _get_standard_prompt(
    state: PipelineState, num_slides: int, slide_titles: list
) -> str:
    """Get standard QA prompt for business/professional presentations."""
    return f"""You are a professional presentation quality assurance reviewer. Evaluate the generated presentation and provide objective scores and feedback.

**Presentation Overview:**
- Topic: {state.outline.topic if state.outline else "Unknown"}
- Audience: {state.outline.audience if state.outline else "Unknown"}
- Number of slides: {num_slides}
- Slide titles: {', '.join(slide_titles) if slide_titles else "None"}

**Evaluation Criteria:**

1. **Content Score (1-5):**
   - Are the slides informative and substantive?
   - Do bullets provide specific, actionable information?
   - Is the content appropriate for the target audience?
   - Are claims supported by citations where needed?

2. **Design Score (1-5):**
   - Are slide titles clear and concise?
   - Are bullets well-formatted and easy to read?
   - Is there good visual hierarchy?
   - Are speaker notes helpful and detailed?

3. **Coherence Score (1-5):**
   - Do slides follow a logical progression?
   - Does each slide build on the previous ones?
   - Is there a clear narrative arc?
   - Does the presentation tell a complete story?

**Scoring Guide:**
- 5.0: Excellent, publication-ready
- 4.0: Good, minor improvements needed
- 3.0: Acceptable, some revisions recommended
- 2.0: Below standards, significant revisions needed
- 1.0: Poor, complete redesign required

**Output Format (JSON):**
{{
  "content_score": 4.5,
  "design_score": 4.0,
  "coherence_score": 4.5,
  "feedback": "Specific, actionable feedback for improvement. Highlight both strengths and areas for enhancement."
}}

**Example:**
{{
  "content_score": 4.0,
  "design_score": 4.5,
  "coherence_score": 3.5,
  "feedback": "Strong technical content with good evidence support. Slide design is clean and professional. Consider adding a stronger transition between sections 2 and 3 to improve narrative flow. The conclusion could be more impactful with a call-to-action."
}}

Provide your quality assessment as valid JSON:"""


def _get_educational_prompt(
    state: PipelineState, num_slides: int, slide_titles: list
) -> str:
    """Get enhanced QA prompt for educational presentations with pedagogical evaluation."""
    objectives_str = "None"
    if state.outline and state.outline.learning_objectives:
        objectives_str = "; ".join(
            [obj.objective for obj in state.outline.learning_objectives[:3]]
        )

    # Check if slides have pedagogical elements
    pedagogical_features = _analyze_pedagogical_features(state)

    return f"""You are an instructional design expert evaluating the pedagogical quality of an educational presentation.

**Presentation Overview:**
- Topic: {state.outline.topic if state.outline else "Unknown"}
- Audience: {state.outline.audience if state.outline else "Unknown"}
- Educational Level: {state.outline.educational_level if state.outline else "Not specified"}
- Learning Objectives: {objectives_str}
- Number of slides: {num_slides}
- Slide titles: {', '.join(slide_titles) if slide_titles else "None"}

**Pedagogical Features Present:**
- Engagement hooks: {pedagogical_features['hooks']} slides
- Active learning prompts: {pedagogical_features['active']} slides
- Formative checks: {pedagogical_features['formative']} slides
- Bloom's levels specified: {pedagogical_features['bloom']} slides

**Evaluation Criteria:**

1. **Content Score (1-5):**
   - Is content accurate and grade-appropriate?
   - Are concepts explained clearly with examples?
   - Do bullets build understanding progressively?

2. **Design Score (1-5):**
   - Are slides visually clear for learners?
   - Is cognitive load appropriate (not overwhelming)?
   - Are speaker notes helpful for instruction?

3. **Coherence Score (1-5):**
   - Does content scaffold from simple to complex?
   - Do slides connect to learning objectives?
   - Is there a clear instructional arc?

4. **Pedagogical Score (1-5):** [NEW for educational mode]
   - Are instructional design principles applied?
   - Is content scaffolded appropriately?
   - Do slides support the learning objectives?
   - Are concepts introduced with concrete examples first?

5. **Engagement Score (1-5):** [NEW for educational mode]
   - Are there attention-grabbing hooks?
   - Are active learning elements included?
   - Will this motivate and interest learners?
   - Are connections made to real-world relevance?

6. **Clarity Score (1-5):** [NEW for educational mode]
   - Is language appropriate for the grade level?
   - Are explanations clear and understandable?
   - Are analogies and examples relatable?
   - Will target learners comprehend this content?

**Pedagogical Best Practices Checklist:**
✓ Learning objectives guide content
✓ Prior knowledge activated (hooks, connections)
✓ Scaffolding from concrete to abstract
✓ Active learning opportunities
✓ Formative assessment checks
✓ Differentiation guidance in notes
✓ Real-world applications shown

**Scoring Guide:**
- 5.0: Exemplary - follows best practices, highly effective
- 4.0: Proficient - good pedagogy, minor improvements
- 3.0: Developing - meets basics, needs refinement
- 2.0: Below expectations - significant pedagogical issues
- 1.0: Inadequate - does not support learning

**Output Format (JSON):**
{{
  "content_score": 4.5,
  "design_score": 4.0,
  "coherence_score": 4.5,
  "pedagogical_score": 4.0,
  "engagement_score": 4.5,
  "clarity_score": 4.0,
  "feedback": "Detailed pedagogical feedback addressing instructional design, engagement, and clarity. Include specific suggestions for improvement aligned with learning objectives."
}}

**Example:**
{{
  "content_score": 4.0,
  "design_score": 4.5,
  "coherence_score": 4.0,
  "pedagogical_score": 3.5,
  "engagement_score": 4.0,
  "clarity_score": 4.0,
  "feedback": "Strong foundational content with clear explanations and good examples. Slides are well-designed and visually appropriate for 9th graders. Good use of engagement hooks (4/5 slides have them). However, scaffolding could be improved - slides 2-3 jump too quickly to abstract concepts. Recommendation: Add more concrete examples before introducing the chemical equation. Formative checks are present (3/5 slides) - good! Consider adding more active learning prompts. Speaker notes provide helpful differentiation strategies. Overall, this is a pedagogically sound presentation that will support student learning with minor refinements."
}}

Provide your comprehensive educational quality assessment as valid JSON:"""


def _analyze_pedagogical_features(state: PipelineState) -> dict:
    """Analyze how many slides have pedagogical features."""
    if not state.content:
        return {"hooks": 0, "active": 0, "formative": 0, "bloom": 0}

    hooks = sum(
        1
        for slide in state.content
        if hasattr(slide, "engagement_hook") and slide.engagement_hook
    )
    active = sum(
        1
        for slide in state.content
        if hasattr(slide, "active_learning_prompt") and slide.active_learning_prompt
    )
    formative = sum(
        1
        for slide in state.content
        if hasattr(slide, "formative_check") and slide.formative_check
    )
    bloom = sum(
        1
        for slide in state.content
        if hasattr(slide, "bloom_level") and slide.bloom_level
    )

    return {"hooks": hooks, "active": active, "formative": formative, "bloom": bloom}

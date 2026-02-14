"""Enhanced Content generation agent with pedagogical support.

This agent generates slide content with scaffolding, engagement hooks,
active learning prompts, and formative assessments for educational presentations.
"""

from __future__ import annotations

from typing import List

from ..state import PipelineState
from ..schemas import SlideContent
from ..models.ai_interface import get_ai_interface
from ..utils import parse_json_with_repair


def run_content(state: PipelineState) -> PipelineState:
    """Generate slide content for each section in the outline.

    This agent creates detailed, well-structured slide content.
    When educational_mode is enabled, it includes pedagogical elements like
    engagement hooks, active learning prompts, and formative checks.
    """
    if not state.outline:
        state.errors.append("No outline available for content generation")
        return state

    slides: List[SlideContent] = []
    # Use centralized AI interface
    ai = get_ai_interface()

    for idx, section in enumerate(state.outline.sections, 1):
        if state.educational_mode:
            prompt = _get_educational_prompt(state, section, idx)
        else:
            prompt = _get_standard_prompt(state, section, idx)

        try:
            response = ai.generate(prompt, agent="content")
        except Exception:
            response = None
        # Parse JSON from response with repair logic
        result = parse_json_with_repair(response.content) if response else {}

        try:
            slide = SlideContent(**result)
        except Exception:
            # Fallback slide content
            topic = (
                state.outline.topic
                if state.outline
                else state.user_input or "the topic"
            )
            base_bullets = [
                f"Define {section.lower()} in the context of {topic}.",
                f"Explain key drivers and practical implications of {section.lower()}.",
                f"Summarize actionable takeaways related to {topic}.",
            ]

            if state.educational_mode:
                slide = SlideContent(
                    title=f"{section}: {topic}",
                    bullets=base_bullets,
                    speaker_notes=f"Guide learners through {section.lower()} with concrete examples tied to {topic}.",
                    citations=list(state.citations) if state.citations else [],
                    engagement_hook=f"Why does {section.lower()} matter in real life?",
                    active_learning_prompt=f"Pair activity: identify one real-world example of {section.lower()}.",
                    formative_check=f"Quick check: What is one key idea from {section.lower()}?",
                )
            else:
                slide = SlideContent(
                    title=f"{section}: {topic}",
                    bullets=base_bullets,
                    speaker_notes=f"Discuss why {section.lower()} is important for understanding {topic}.",
                    citations=list(state.citations) if state.citations else [],
                )
        slides.append(slide)

    state.content = slides
    return state


def _get_standard_prompt(state: PipelineState, section: str, idx: int) -> str:
    """Get standard prompt for business/professional slide content."""
    citations_str = ", ".join(state.citations) if state.citations else "none"

    return f"""You are a professional slide content writer. Create engaging, informative content for a presentation slide.

**Presentation Context:**
- Topic: {state.outline.topic}
- Audience: {state.outline.audience}
- Section {idx}/{len(state.outline.sections)}: {section}

**Available Citations:** {citations_str}

**Instructions:**
1. Create a clear, concise slide title (max 10 words)
2. Write 3-5 bullet points that:
   - Are concise (max 15 words each)
   - Use action verbs and specific details
   - Build on each other logically
   - Are audience-appropriate
3. Write speaker notes (2-3 sentences) with additional context
4. Include relevant citation markers [1], [2], etc. if applicable

**Output Format (JSON):**
{{
  "title": "Slide Title",
  "bullets": [
    "First key point with specific details",
    "Second key point building on the first",
    "Third key point with impact or conclusion"
  ],
  "speaker_notes": "Additional context and talking points for the presenter.",
  "citations": ["[1]", "[2]"]
}}

**Example:**
{{
  "title": "Economic Benefits of Solar Energy",
  "bullets": [
    "Reduces electricity costs by 50-70% for businesses [1]",
    "Creates local green jobs in installation and maintenance",
    "Provides energy price stability over 25+ year lifespan [2]"
  ],
  "speaker_notes": "Emphasize the long-term ROI and job creation aspects. Note that these benefits are supported by multiple case studies from similar cities.",
  "citations": ["[1]", "[2]"]
}}

Generate the slide content as valid JSON:"""


def _get_educational_prompt(state: PipelineState, section: str, idx: int) -> str:
    """Get enhanced prompt for educational slide content with pedagogical elements."""
    citations_str = ", ".join(state.citations) if state.citations else "none"

    # Determine appropriate Bloom's level for this slide
    bloom_level = _suggest_bloom_level(idx, len(state.outline.sections))

    # Get relevant learning objectives
    objectives_str = "None"
    if state.outline.learning_objectives:
        relevant_objs = [
            f"{obj.objective} ({obj.bloom_level})"
            for obj in state.outline.learning_objectives[:2]
        ]
        objectives_str = "; ".join(relevant_objs)

    return f"""You are an instructional design expert. Create pedagogically sound slide content that engages learners and supports understanding.

**Presentation Context:**
- Topic: {state.outline.topic}
- Audience: {state.outline.audience}
- Educational Level: {state.outline.educational_level or "Not specified"}
- Section {idx}/{len(state.outline.sections)}: {section}
- Learning Objectives: {objectives_str}

**Available Citations:** {citations_str}

**Pedagogical Requirements:**
1. START with an **engagement hook** (question, surprising fact, real-world connection)
2. Present content using **scaffolding** (concrete examples → abstract concepts)
3. Include 3-5 bullet points that:
   - Start with concrete, relatable examples
   - Build complexity gradually
   - Use analogies or comparisons
   - Connect to prior knowledge
   - Target {bloom_level} cognitive level
4. Add an **active learning prompt** (think-pair-share, quick activity, reflection)
5. Include a **formative check** (quick question to gauge understanding)
6. Write **speaker notes** with:
   - Pedagogical guidance (how to present this)
   - Differentiation strategies (support for struggling/advanced learners)
   - Transition to next slide

**Bloom's Taxonomy Target:** {bloom_level}
- **remember**: Recall facts
- **understand**: Explain concepts
- **apply**: Use in new situations
- **analyze**: Find patterns, compare
- **evaluate**: Judge quality, critique
- **create**: Design, produce new ideas

**Output Format (JSON):**
{{
  "title": "Clear, student-focused slide title",
  "engagement_hook": "Opening hook to capture attention (question/fact/connection)",
  "bullets": [
    "Concrete example or relatable starting point",
    "Building on previous point with more detail",
    "Abstract concept explained with analogy",
    "Application or implication",
    "Connection to learning objective"
  ],
  "active_learning_prompt": "Activity: [pair discussion/quick write/demo/etc.]",
  "formative_check": "Check: Quick question to assess understanding",
  "speaker_notes": "Pedagogical guidance: Start with hook to activate prior knowledge about [concept]. After bullets, allow 60 seconds for active learning. Use formative check before moving on. For struggling learners: [strategy]. For advanced learners: [extension].",
  "bloom_level": "{bloom_level}",
  "citations": ["[1]"]
}}

**Example (Understanding Level):**
{{
  "title": "How Photosynthesis Works",
  "engagement_hook": "Question: If plants don't eat food, how do they grow so big?",
  "bullets": [
    "Plants are like solar-powered factories - they capture sunlight with chlorophyll",
    "Carbon dioxide from air + water from roots → glucose (sugar) + oxygen",
    "The chemical equation: 6CO₂ + 6H₂O + light → C₆H₁₂O₆ + 6O₂",
    "Chloroplasts act as tiny solar panels inside leaf cells",
    "This process is the foundation of all life on Earth [1]"
  ],
  "active_learning_prompt": "Think-Pair-Share: Turn to a partner and explain why plants need BOTH sunlight AND water for photosynthesis.",
  "formative_check": "Quick Poll: Which gas do plants release during photosynthesis? A) Carbon dioxide  B) Oxygen  C) Nitrogen",
  "speaker_notes": "Start with engaging hook to make students curious. Use the solar panel analogy to make chloroplasts relatable. After presenting bullets, give 90 seconds for pair discussion - listen for accurate explanations. Use the formative check (answer: B) before proceeding. For struggling learners: Draw the process visually on board. For advanced: Ask how this connects to cellular respiration.",
  "bloom_level": "understand",
  "citations": ["[1]"]
}}

Generate the pedagogically sound slide content as valid JSON:"""


def _suggest_bloom_level(slide_index: int, total_slides: int) -> str:
    """Suggest appropriate Bloom's level based on slide position (scaffolding).

    Early slides: remember, understand
    Middle slides: apply, analyze
    Later slides: evaluate, create
    """
    progress = slide_index / total_slides

    if progress <= 0.33:
        return "understand"  # Foundation building
    elif progress <= 0.66:
        return "apply"  # Practice and application
    else:
        return "analyze"  # Deeper thinking and synthesis

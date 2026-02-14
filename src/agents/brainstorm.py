"""Enhanced Brainstorm agent with pedagogical support.

This agent generates presentation outlines with optional learning objectives,
prerequisite knowledge, and Bloom's taxonomy alignment for educational presentations.
"""

from __future__ import annotations


from ..schemas import PresentationOutline, LearningObjective
from ..state import PipelineState
from ..models.ai_interface import get_ai_interface
from ..utils import parse_json_with_repair


def run_brainstorm(state: PipelineState) -> PipelineState:
    """Generate presentation outline from user input.

    This agent analyzes the user's brief and creates a structured outline.
    When educational_mode is enabled, it also generates learning objectives
    and identifies prerequisite knowledge.
    """
    if not state.user_input:
        state.errors.append("No user input provided")
        return state

    # Use centralized AI interface
    ai = get_ai_interface()

    if state.educational_mode:
        # Educational mode: Include learning objectives and pedagogical planning
        prompt = _get_educational_prompt(state)
    else:
        # Standard mode: Business/professional presentations
        prompt = _get_standard_prompt(state)

    try:
        response = ai.generate(prompt, agent="brainstorm")
    except Exception:
        response = None

    # Parse JSON from response with repair logic
    result = parse_json_with_repair(response.content) if response else {}

    try:
        # Parse learning objectives if present
        if "learning_objectives" in result and result["learning_objectives"]:
            objectives = [
                LearningObjective(**obj) for obj in result["learning_objectives"]
            ]
            result["learning_objectives"] = objectives

        outline = PresentationOutline(**result)
    except Exception:
        # Fall back to simple outline
        outline = PresentationOutline(
            topic=state.user_input.strip(),
            audience="General audience",
            sections=["Introduction", "Main Points", "Conclusion"],
        )

    if state.educational_mode:
        if not outline.prerequisite_knowledge:
            outline.prerequisite_knowledge = [
                "Basic familiarity with the topic context",
                "Willingness to engage in guided practice",
            ]

        if not outline.learning_objectives:
            outline.learning_objectives = [
                LearningObjective(
                    objective=f"Students will be able to explain the core ideas of {outline.topic}",
                    bloom_level="understand",
                    assessment="Short written explanation or verbal check",
                ),
                LearningObjective(
                    objective=f"Students will be able to apply concepts from {outline.topic} to a practical example",
                    bloom_level="apply",
                    assessment="Scenario-based practice activity",
                ),
            ]

    state.outline = outline
    return state


def _get_standard_prompt(state: PipelineState) -> str:
    """Get standard prompt for business/professional presentations."""
    return f"""You are a professional presentation outline generator. Your task is to analyze the user's brief and create a well-structured presentation outline.

**User Brief:**
{state.user_input}

**Instructions:**
1. Extract or infer the main topic from the brief
2. Identify the target audience (if not specified, make a reasonable assumption)
3. Generate 3-5 section headings that logically organize the content
4. Each section should build on the previous one to tell a cohesive story

**Output Format (JSON):**
{{
  "topic": "Clear, concise presentation title",
  "audience": "Target audience description",
  "sections": ["Section 1", "Section 2", "Section 3", ...]
}}

**Example:**
Input: "Explain renewable energy benefits to city planners"
Output:
{{
  "topic": "Benefits of Renewable Energy for Urban Development",
  "audience": "Municipal planners and city officials",
  "sections": [
    "Current Energy Challenges in Cities",
    "Types of Renewable Energy Solutions",
    "Economic and Environmental Benefits",
    "Implementation Strategies",
    "Case Studies and Success Stories"
  ]
}}

Generate the outline as valid JSON:"""


def _get_educational_prompt(state: PipelineState) -> str:
    """Get enhanced prompt for educational presentations with learning objectives."""
    return f"""You are an instructional design expert. Create a pedagogically sound presentation outline that follows evidence-based teaching principles.

**User Brief:**
{state.user_input}

**Instructional Design Requirements:**
1. Identify the main topic and target learners (grade level, prior knowledge)
2. Generate 3-5 SMART learning objectives using Bloom's taxonomy
   - Each objective should be Specific, Measurable, Achievable, Relevant, Time-bound
   - Vary cognitive levels: remember, understand, apply, analyze, evaluate, create
3. Identify prerequisite knowledge learners should have
4. Design sections that scaffold from simple to complex (concrete → abstract)
5. Plan formative assessment moments

**Bloom's Taxonomy Levels:**
- **Remember**: Recall facts, terms, concepts
- **Understand**: Explain ideas, compare, classify
- **Apply**: Use knowledge in new situations, implement
- **Analyze**: Break down information, find patterns
- **Evaluate**: Judge value, critique, justify decisions
- **Create**: Produce new work, design, construct

**Output Format (JSON):**
{{
  "topic": "Clear, learner-focused presentation title",
  "audience": "Target learners (e.g., 'High school students, grades 9-10')",
  "educational_level": "Grade level or experience level",
  "prerequisite_knowledge": [
    "Prior concept 1 learners should know",
    "Prior concept 2 learners should know"
  ],
  "learning_objectives": [
    {{
      "objective": "Students will be able to [verb] [concept]",
      "bloom_level": "understand",
      "assessment": "How to measure this objective"
    }},
    {{
      "objective": "Students will be able to [verb] [concept]",
      "bloom_level": "apply",
      "assessment": "How to measure this objective"
    }}
  ],
  "sections": [
    "Hook: Engaging opening that connects to prior knowledge",
    "Core concept introduction (concrete examples first)",
    "Application and practice",
    "Analysis and deeper understanding",
    "Synthesis and conclusion"
  ]
}}

**Example:**
Input: "Teach photosynthesis to 9th grade biology students"
Output:
{{
  "topic": "Photosynthesis: How Plants Convert Light to Energy",
  "audience": "9th grade biology students",
  "educational_level": "High school freshman (age 14-15)",
  "prerequisite_knowledge": [
    "Basic cell structure and organelles",
    "Understanding of chemical reactions",
    "Energy concepts (kinetic and potential energy)"
  ],
  "learning_objectives": [
    {{
      "objective": "Students will be able to explain the process of photosynthesis in their own words",
      "bloom_level": "understand",
      "assessment": "Verbal explanation and diagram labeling"
    }},
    {{
      "objective": "Students will be able to apply photosynthesis knowledge to predict plant growth outcomes",
      "bloom_level": "apply",
      "assessment": "Scenario-based problem solving"
    }},
    {{
      "objective": "Students will be able to analyze the relationship between photosynthesis and cellular respiration",
      "bloom_level": "analyze",
      "assessment": "Comparison table and discussion"
    }}
  ],
  "sections": [
    "Hook: Why Are Plants Green? (Activating prior knowledge)",
    "The Photosynthesis Equation (Core concept with concrete examples)",
    "Factors Affecting Photosynthesis (Application to real scenarios)",
    "Photosynthesis vs. Cellular Respiration (Analysis and comparison)",
    "Ecological Importance and Review (Synthesis and formative assessment)"
  ]
}}

Generate the pedagogically sound outline as valid JSON:"""

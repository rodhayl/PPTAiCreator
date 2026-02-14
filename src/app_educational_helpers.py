"""Helper functions for displaying educational/pedagogical features in the GUI."""

from __future__ import annotations

import streamlit as st
from .schemas import PresentationOutline, SlideContent, LearningObjective
from .state import PipelineState


def display_educational_toggle() -> bool:
    """Display educational mode toggle with explanation.

    Returns:
        bool: True if educational mode is enabled
    """
    educational_mode = st.checkbox(
        "🎓 Educational Mode",
        value=False,
        help="Generate pedagogically sound presentations with learning objectives, "
        "engagement hooks, active learning prompts, and formative assessments",
    )

    if educational_mode:
        with st.expander("ℹ️ What is Educational Mode?", expanded=False):
            st.markdown("""
            **Educational Mode** enhances your presentation with evidence-based instructional design principles:

            **Learning Features:**
            - 📋 SMART learning objectives aligned with Bloom's Taxonomy
            - 🎯 Prerequisite knowledge identification
            - 🎣 Engagement hooks to activate prior knowledge
            - 🤝 Active learning prompts (think-pair-share, activities)
            - ✓ Formative assessment checks for understanding
            - 📊 Scaffolded content (concrete → abstract)
            - 👥 Differentiation guidance for diverse learners

            **Best for:** Teachers, trainers, instructional designers, educators

            **Not needed for:** Business presentations, reports, pitches
            """)

    return educational_mode


def display_learning_objectives(outline: PresentationOutline):
    """Display learning objectives with Bloom's taxonomy indicators.

    Args:
        outline: The presentation outline with learning objectives
    """
    if not outline.learning_objectives or len(outline.learning_objectives) == 0:
        return

    st.markdown("### 🎯 Learning Objectives")

    # Bloom's level colors
    bloom_colors = {
        "remember": "#FF6B6B",  # Red
        "understand": "#FFB26B",  # Orange
        "apply": "#FFE66D",  # Yellow
        "analyze": "#95E1D3",  # Teal
        "evaluate": "#A8E6CF",  # Green
        "create": "#C7CEEA",  # Purple
    }

    for i, obj in enumerate(outline.learning_objectives, 1):
        bloom_level = obj.bloom_level if hasattr(obj, "bloom_level") else "understand"
        color = bloom_colors.get(bloom_level, "#CCCCCC")

        # Display with colored badge
        col1, col2 = st.columns([1, 9])
        with col1:
            st.markdown(
                f'<div style="background-color: {color}; '
                f"padding: 5px; border-radius: 5px; text-align: center; "
                f'font-weight: bold; font-size: 12px;">'
                f"{bloom_level.upper()}</div>",
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(f"**{i}.** {obj.objective}")
            if hasattr(obj, "assessment") and obj.assessment:
                st.caption(f"📝 Assessment: {obj.assessment}")

        st.markdown("")  # Spacing


def display_prerequisite_knowledge(outline: PresentationOutline):
    """Display prerequisite knowledge requirements.

    Args:
        outline: The presentation outline with prerequisites
    """
    if not outline.prerequisite_knowledge or len(outline.prerequisite_knowledge) == 0:
        return

    st.markdown("### 📚 Prerequisite Knowledge")
    st.markdown("Students should already understand:")

    for prereq in outline.prerequisite_knowledge:
        st.markdown(f"- {prereq}")


def display_pedagogical_slide_badges(slide: SlideContent) -> str:
    """Get badge string for pedagogical elements on a slide.

    Args:
        slide: The slide content

    Returns:
        str: Badge string (e.g., "🎣 Hook | 🤝 Active | ✓ Check")
    """
    badges = []

    if hasattr(slide, "engagement_hook") and slide.engagement_hook:
        badges.append("🎣 Hook")

    if hasattr(slide, "active_learning_prompt") and slide.active_learning_prompt:
        badges.append("🤝 Active")

    if hasattr(slide, "formative_check") and slide.formative_check:
        badges.append("✓ Check")

    if hasattr(slide, "bloom_level") and slide.bloom_level:
        badges.append(f"[{slide.bloom_level.title()}]")

    return " | ".join(badges) if badges else ""


def display_pedagogical_content_preview(state: PipelineState):
    """Display slide content with pedagogical elements highlighted.

    Args:
        state: Pipeline state with generated content
    """
    if not state.content:
        st.warning("No slide content generated yet.")
        return

    st.markdown(f"**Total Slides:** {len(state.content)}")

    for i, slide in enumerate(state.content):
        # Get pedagogical badges
        badges = display_pedagogical_slide_badges(slide)

        # Display slide with badges
        with st.expander(f"📄 Slide {i+1}: {slide.title}", expanded=False):
            # Show badges if present
            if badges:
                st.markdown(f"**Pedagogical Elements:** {badges}")
                st.markdown("---")

            # Engagement hook
            if hasattr(slide, "engagement_hook") and slide.engagement_hook:
                st.markdown("🎣 **Engagement Hook:**")
                st.info(slide.engagement_hook)

            # Main content
            st.markdown("📝 **Content:**")
            for j, bullet in enumerate(slide.bullets, 1):
                st.markdown(f"{j}. {bullet}")

            # Active learning prompt
            if (
                hasattr(slide, "active_learning_prompt")
                and slide.active_learning_prompt
            ):
                st.markdown("🤝 **Active Learning:**")
                st.success(slide.active_learning_prompt)

            # Formative check
            if hasattr(slide, "formative_check") and slide.formative_check:
                st.markdown("✓ **Formative Check:**")
                st.warning(slide.formative_check)

            # Speaker notes
            if slide.speaker_notes:
                with st.expander("💬 Speaker Notes", expanded=False):
                    st.markdown(slide.speaker_notes)

            # Citations
            if slide.citations:
                st.caption(f"📚 Citations: {', '.join(slide.citations)}")


def display_pedagogical_qa_dashboard(state: PipelineState):
    """Display pedagogical QA metrics in a dashboard format.

    Args:
        state: Pipeline state with QA report
    """
    if not state.qa_report:
        st.warning("No QA report generated yet.")
        return

    qa = state.qa_report

    # Standard metrics
    st.markdown("### 📊 Quality Assessment")

    st.markdown("**Standard Metrics:**")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Content", f"{qa.content_score:.1f}/5.0")
    with col2:
        st.metric("Design", f"{qa.design_score:.1f}/5.0")
    with col3:
        st.metric("Coherence", f"{qa.coherence_score:.1f}/5.0")
    with col4:
        avg_standard = (qa.content_score + qa.design_score + qa.coherence_score) / 3
        st.metric("Average", f"{avg_standard:.1f}/5.0")

    # Pedagogical metrics (if present)
    if (
        (hasattr(qa, "pedagogical_score") and qa.pedagogical_score)
        or (hasattr(qa, "engagement_score") and qa.engagement_score)
        or (hasattr(qa, "clarity_score") and qa.clarity_score)
    ):

        st.markdown("**🎓 Pedagogical Metrics:**")
        col1, col2, col3, col4 = st.columns(4)

        pedagogical_scores = []

        with col1:
            if hasattr(qa, "pedagogical_score") and qa.pedagogical_score:
                st.metric("Pedagogy", f"{qa.pedagogical_score:.1f}/5.0")
                pedagogical_scores.append(qa.pedagogical_score)
            else:
                st.metric("Pedagogy", "N/A")

        with col2:
            if hasattr(qa, "engagement_score") and qa.engagement_score:
                st.metric("Engagement", f"{qa.engagement_score:.1f}/5.0")
                pedagogical_scores.append(qa.engagement_score)
            else:
                st.metric("Engagement", "N/A")

        with col3:
            if hasattr(qa, "clarity_score") and qa.clarity_score:
                st.metric("Clarity", f"{qa.clarity_score:.1f}/5.0")
                pedagogical_scores.append(qa.clarity_score)
            else:
                st.metric("Clarity", "N/A")

        with col4:
            if pedagogical_scores:
                avg_pedagogical = sum(pedagogical_scores) / len(pedagogical_scores)
                st.metric("Avg (Ped.)", f"{avg_pedagogical:.1f}/5.0")
            else:
                st.metric("Avg (Ped.)", "N/A")

        # Pedagogical element coverage
        if state.content:
            st.markdown("**✓ Pedagogical Elements Coverage:**")

            hooks = sum(
                1
                for slide in state.content
                if hasattr(slide, "engagement_hook") and slide.engagement_hook
            )
            active = sum(
                1
                for slide in state.content
                if hasattr(slide, "active_learning_prompt")
                and slide.active_learning_prompt
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

            total = len(state.content)

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Hooks", f"{hooks}/{total}", f"{hooks/total*100:.0f}%")
            with col2:
                st.metric(
                    "Active Learning", f"{active}/{total}", f"{active/total*100:.0f}%"
                )
            with col3:
                st.metric(
                    "Formative Checks",
                    f"{formative}/{total}",
                    f"{formative/total*100:.0f}%",
                )
            with col4:
                st.metric(
                    "Bloom's Levels", f"{bloom}/{total}", f"{bloom/total*100:.0f}%"
                )

    # Detailed feedback
    if qa.feedback:
        st.markdown("**💬 Detailed Feedback:**")
        st.markdown(qa.feedback)


def display_educational_outline_editor(state: PipelineState) -> PipelineState:
    """Display outline editor with learning objectives editing.

    Args:
        state: Pipeline state with outline

    Returns:
        PipelineState: Updated state
    """
    if not state.outline:
        st.warning("No outline generated yet.")
        return state

    st.markdown("### 📝 Edit Presentation Outline")

    # Edit basic fields
    new_topic = st.text_input("Topic", value=state.outline.topic)
    new_audience = st.text_input("Audience", value=state.outline.audience)

    if hasattr(state.outline, "educational_level") and state.outline.educational_level:
        new_edu_level = st.text_input(
            "Educational Level", value=state.outline.educational_level
        )
    else:
        new_edu_level = None

    # Edit learning objectives
    if state.outline.learning_objectives and len(state.outline.learning_objectives) > 0:
        st.markdown("**Learning Objectives:**")

        new_objectives = []
        for i, obj in enumerate(state.outline.learning_objectives):
            with st.expander(f"Objective {i+1}", expanded=False):
                new_obj_text = st.text_area(
                    "Objective", value=obj.objective, key=f"obj_{i}"
                )
                new_bloom = st.selectbox(
                    "Bloom's Level",
                    options=[
                        "remember",
                        "understand",
                        "apply",
                        "analyze",
                        "evaluate",
                        "create",
                    ],
                    index=[
                        "remember",
                        "understand",
                        "apply",
                        "analyze",
                        "evaluate",
                        "create",
                    ].index(
                        obj.bloom_level if hasattr(obj, "bloom_level") else "understand"
                    ),
                    key=f"bloom_{i}",
                )
                new_assessment = st.text_input(
                    "Assessment Method",
                    value=(
                        obj.assessment
                        if hasattr(obj, "assessment") and obj.assessment
                        else ""
                    ),
                    key=f"assess_{i}",
                )

                new_objectives.append(
                    LearningObjective(
                        objective=new_obj_text,
                        bloom_level=new_bloom,
                        assessment=new_assessment if new_assessment else None,
                    )
                )

    # Edit sections
    st.markdown("**Sections:**")
    new_sections = []
    for i, section in enumerate(state.outline.sections):
        new_section = st.text_input(f"Section {i+1}", value=section, key=f"section_{i}")
        new_sections.append(new_section)

    # Apply changes button
    if st.button("✅ Apply Changes", type="primary"):
        state.outline.topic = new_topic
        state.outline.audience = new_audience
        if new_edu_level:
            state.outline.educational_level = new_edu_level
        if new_objectives:
            state.outline.learning_objectives = new_objectives
        state.outline.sections = [s for s in new_sections if s.strip()]
        st.success("Outline updated successfully!")
        st.rerun()

    return state

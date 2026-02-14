"""Comprehensive Streamlit GUI for the PPTX Agent.

This app provides complete access to all backend features:
- Provider selection (Ollama, OpenRouter)
- Model and temperature configuration
- Outline preview and editing
- Step-by-step pipeline execution
- Research/citation viewing
- Run history from database
- LangGraph vs standard pipeline selection
- Agent-specific configuration

All processing runs according to ai_config.properties configuration.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import streamlit as st

from src.config import get_config
from src.graph.build_graph import run_pipeline, CheckpointManager
from src.graph.langgraph_impl import run_langgraph_pipeline
from src.models.ai_config import get_ai_config, reload_ai_config
from src.models.ai_interface import get_ai_interface
from src.state import PipelineState
from src.agents.brainstorm import run_brainstorm
from src.agents.research import run_research
from src.agents.content import run_content
from src.agents.design import run_design
from src.agents.qa import run_qa
from src.app_educational_helpers import (
    display_educational_toggle,
    display_learning_objectives,
    display_prerequisite_knowledge,
    display_pedagogical_content_preview,
    display_pedagogical_qa_dashboard,
    display_educational_outline_editor,
)
from src.app_settings_helpers import display_settings_ui


def load_run_history(limit: int = 10) -> list[dict]:
    """Load recent runs from database."""
    config = get_config()
    db_path = config.db_path

    if not Path(db_path).exists():
        return []

    try:
        cp = CheckpointManager(db_path=db_path)
        return cp.list_runs(limit=limit)
    except Exception as e:
        st.error(f"Error loading history: {e}")
        return []


def display_model_configuration():
    """Display current AI model configuration."""
    st.sidebar.markdown("### 🤖 AI Configuration")

    ai_config = get_ai_config()
    provider = ai_config.get_provider()

    # Provider info
    provider_emoji = {"ollama": "🏠", "openrouter": "☁️"}
    st.sidebar.info(
        f"{provider_emoji.get(provider, '🤖')} **Provider:** {provider.upper()}\n\n"
        f"Configure in: `ai_config.properties`"
    )

    # Model details for each agent
    with st.sidebar.expander("📋 Agent Models", expanded=False):
        for agent in ["brainstorm", "content", "qa"]:
            ai = get_ai_interface()
            info = ai.get_model_info(agent)
            st.markdown(
                f"**{agent.title()}**\n"
                f"- Model: `{info['model']}`\n"
                f"- Temp: {info['temperature']}\n"
                f"- Max tokens: {info['max_tokens']}"
            )

    # Reload button
    if st.sidebar.button("🔄 Reload Configuration", help="Reload ai_config.properties"):
        reload_ai_config()
        st.sidebar.success("Configuration reloaded!")


def validate_text_file(uploaded_file) -> tuple[bool, str]:
    """Validate that uploaded file is a text-based file.

    Args:
        uploaded_file: Streamlit uploaded file object

    Returns:
        Tuple of (is_valid, error_message)
    """
    if uploaded_file is None:
        return False, "No file uploaded"

    # Check file extension
    allowed_extensions = {
        ".txt",
        ".md",
        ".markdown",
        ".csv",
        ".json",
        ".xml",
        ".yaml",
        ".yml",
    }
    file_extension = Path(uploaded_file.name).suffix.lower()

    if file_extension not in allowed_extensions:
        return (
            False,
            f"File type '{file_extension}' not allowed. Allowed types: {', '.join(allowed_extensions)}",
        )

    # Check file size (max 10MB)
    if uploaded_file.size and uploaded_file.size > 10 * 1024 * 1024:
        return False, "File too large (max 10MB)"

    # Try to read as text to ensure it's text-based
    try:
        # Read first 1KB to check if it's valid text
        chunk = uploaded_file.read(1024)
        uploaded_file.seek(0)  # Reset file pointer

        # Try to decode as UTF-8
        chunk.decode("utf-8")

        return True, "File is valid"
    except UnicodeDecodeError:
        return False, "File appears to be binary (not a text file)"
    except Exception as e:
        return False, f"Error validating file: {str(e)}"


def display_extra_input_section(phase_name: str, key_prefix: str) -> str:
    """Display a section for users to add extra information or opinions.

    Args:
        phase_name: Name of the phase (e.g., "Brainstorm", "Research")
        key_prefix: Prefix for streamlit keys

    Returns:
        User's extra input text
    """
    st.markdown("#### 💭 Additional Information (Optional)")
    st.markdown(
        f"Add any extra information, opinions, or specific requirements for the **{phase_name}** phase:"
    )

    extra_input = st.text_area(
        label="Your additional input:",
        height=150,
        placeholder=f"Enter any extra information, opinions, or specific requirements for the {phase_name} phase...\n\n"
        f"Example:\n"
        f"- Emphasize practical applications\n"
        f"- Include more historical context\n"
        f"- Target beginners specifically\n"
        f"- Avoid technical jargon",
        key=f"{key_prefix}_extra_input",
        help="This text will be added to the prompt to influence the generation",
    )

    return extra_input


def display_file_upload_section(phase_name: str, key_prefix: str) -> list[str]:
    """Display a file upload section with validation.

    Args:
        phase_name: Name of the phase
        key_prefix: Prefix for streamlit keys

    Returns:
        List of validated file contents
    """
    st.markdown("#### 📁 Upload Reference Files (Optional)")
    st.markdown(
        f"Upload text-based files (txt, md, csv, json, etc.) to provide additional context for the **{phase_name}** phase. "
        f"Max 10MB per file, max 5 files."
    )

    uploaded_files = st.file_uploader(
        label=f"Select files for {phase_name}:",
        type=["txt", "md", "markdown", "csv", "json", "xml", "yaml", "yml"],
        accept_multiple_files=True,
        key=f"{key_prefix}_file_uploader",
        help="Only text-based files are allowed. Binary files (images, PDFs, etc.) will be rejected.",
    )

    validated_contents = []

    if uploaded_files:
        st.markdown("**Uploaded Files:**")

        for uploaded_file in uploaded_files[:5]:  # Limit to 5 files
            # Validate file
            is_valid, message = validate_text_file(uploaded_file)

            if is_valid:
                # Try to read content
                try:
                    content = uploaded_file.read().decode("utf-8")
                    validated_contents.append(content)
                    st.success(f"✅ {uploaded_file.name} ({len(content)} chars)")
                except Exception as e:
                    st.error(f"❌ {uploaded_file.name}: Error reading file - {str(e)}")
            else:
                st.error(f"❌ {uploaded_file.name}: {message}")

        if len(uploaded_files) > 5:
            st.warning(
                f"⚠️ Only first 5 files processed (uploaded {len(uploaded_files)})"
            )

    return validated_contents


def run_agent_with_extras(
    agent_func,
    state: PipelineState,
    extra_input: str = "",
    file_contents: list[str] = None,
    state_field: Optional[str] = None,
) -> PipelineState:
    """Generic wrapper to run any agent with extra input and files.

    Args:
        agent_func: The agent function to call (run_brainstorm, run_research, etc.)
        state: Current pipeline state
        extra_input: User's additional input/opinions
        file_contents: List of uploaded file contents
        state_field: Name of state attribute to store extras (e.g., 'research_extra_input')
                     If None, enhances user_input (for brainstorm)

    Returns:
        Updated pipeline state
    """
    if file_contents is None:
        file_contents = []

    # Skip enhancement if no extras provided
    if not extra_input and not file_contents:
        return agent_func(state)

    # Handle brainstorm (enhances user_input)
    if state_field is None:
        enhanced_input = state.user_input

        if extra_input:
            enhanced_input += f"\n\nAdditional Requirements/Context:\n{extra_input}"

        if file_contents:
            enhanced_input += "\n\nReference Materials:\n"
            for i, content in enumerate(file_contents, 1):
                # Truncate very long content
                display_content = (
                    content[:2000] + "..." if len(content) > 2000 else content
                )
                enhanced_input += f"\n--- File {i} ---\n{display_content}"

        state.user_input = enhanced_input
    else:
        # Handle other agents (store in state attributes)
        if extra_input:
            setattr(state, state_field, extra_input)

        if file_contents:
            # Extract base name (e.g., "content_extra_input" -> "content")
            base_name = state_field.replace("_extra_input", "")
            setattr(state, f"{base_name}_file_contents", file_contents)

    return agent_func(state)


def display_enhanced_phase_runner(
    phase_name: str,
    phase_key: str,
    run_func,
    run_with_extras_func,
    state: PipelineState,
    user_input: str,
    can_run: bool,
    spinner_message_run: str,
    spinner_message_regen: str,
    success_message_run: str,
    success_message_regen: str,
    has_content_check: bool = False,
    content_check: bool = False,
) -> tuple[PipelineState, bool]:
    """Generic enhanced phase runner with extra input and file upload support.

    Args:
        phase_name: Display name of the phase (e.g., "Brainstorm")
        phase_key: Key prefix for UI components (e.g., "brainstorm")
        run_func: Function to run the phase normally
        run_with_extras_func: Function to run with extra input (deprecated - use run_agent_with_extras)
        state: Current pipeline state
        user_input: User's base input
        can_run: Whether the phase can run
        spinner_message_run: Spinner message for normal run
        spinner_message_regen: Spinner message for regenerate
        success_message_run: Success message for normal run
        success_message_regen: Success message for regenerate
        has_content_check: Whether to check for content before enabling extras
        content_check: The content check result

    Returns:
        Tuple of (updated_state, extra_input_entered)
    """
    # Enhanced input section
    with st.expander("💭 Add Extra Information & Files", expanded=False):
        extra_input = display_extra_input_section(phase_name, phase_key)
        file_contents = display_file_upload_section(phase_name, phase_key)

        # Determine if we should enable the buttons
        extras_enabled = can_run if not has_content_check else content_check

        # Map phase_key to state_field for storing extras (None for brainstorm)
        state_field_map = {
            "research": "research_extra_input",
            "content": "content_extra_input",
            "design": "design_extra_input",
            "qa": "qa_extra_input",
        }

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button(
                "▶ Run with Extras",
                key=f"run_{phase_key}_extras",
                disabled=not extras_enabled,
            ):
                with st.spinner(spinner_message_run):
                    if phase_key == "brainstorm":
                        state.user_input = user_input
                    state = run_agent_with_extras(
                        agent_func=run_func,
                        state=state,
                        extra_input=extra_input,
                        file_contents=file_contents,
                        state_field=state_field_map.get(phase_key),
                    )
                    st.session_state["step_state"] = state
                    st.success(success_message_run)
                    st.rerun()
        with col2:
            regen_disabled = get_phase_regenerate_disabled(phase_key, state)
            if st.button(
                "🔄 Regenerate with Extras",
                key=f"regen_{phase_key}_extras",
                disabled=regen_disabled,
            ):
                with st.spinner(spinner_message_regen):
                    state = run_agent_with_extras(
                        agent_func=run_func,
                        state=state,
                        extra_input=extra_input,
                        file_contents=file_contents,
                        state_field=state_field_map.get(phase_key),
                    )
                    st.session_state["step_state"] = state
                    st.success(success_message_regen)
                    st.rerun()

    return state, bool(extra_input or file_contents)


def get_phase_description(phase_key: str) -> str:
    """Get the description for a given phase.

    Args:
        phase_key: The phase identifier (e.g., "brainstorm", "research")

    Returns:
        Description text for the phase
    """
    descriptions = {
        "brainstorm": "Generate presentation outline with topic, audience, and sections.",
        "research": "Extract claims and find supporting evidence from local corpus.",
        "content": "Generate detailed slide content with bullets and speaker notes.",
        "design": "Assemble slides into PowerPoint file with python-pptx.",
        "qa": "Evaluate presentation quality and generate improvement feedback.",
    }
    return descriptions.get(phase_key, "")


def get_phase_regenerate_disabled(phase_key: str, state: PipelineState) -> bool:
    """Check if regenerate button should be disabled for a phase.

    Args:
        phase_key: The phase identifier
        state: Current pipeline state

    Returns:
        True if regenerate should be disabled
    """
    # Research and Content phases need outline to regenerate
    if phase_key in ["research", "content"]:
        return not state.outline
    # Design and QA phases need content to regenerate
    elif phase_key in ["design", "qa"]:
        return not state.content
    # Brainstorm needs outline (when it exists)
    else:
        return not state.outline


def get_phase_spinner_suffix(phase_key: str) -> str:
    """Get spinner message suffix for a phase.

    Args:
        phase_key: The phase identifier

    Returns:
        Suffix text for spinner messages
    """
    if phase_key == "content":
        return " This may take 20-40 seconds."
    return ""


def display_phase_section(
    step_number: int,
    phase_name: str,
    phase_key: str,
    run_func,
    run_with_extras_func,
    state: PipelineState,
    can_run: bool,
    has_content_check: bool = False,
    content_check: bool = False,
) -> PipelineState:
    """Generic section display for any phase to eliminate code duplication.

    Args:
        step_number: The step number (1-5)
        phase_name: Display name of the phase (e.g., "Brainstorm")
        phase_key: Key prefix for the phase (e.g., "brainstorm")
        run_func: Function to run the phase
        run_with_extras_func: Function to run with extras (deprecated)
        state: Current pipeline state
        can_run: Whether the phase can run
        has_content_check: Whether to check for content before enabling extras
        content_check: The content check result

    Returns:
        Updated pipeline state
    """
    # Display section header (non-heading to avoid unstable auto-anchor links)
    st.markdown(f"**Step {step_number}: {phase_name}**")

    # Create 3-column layout for buttons
    col1, col2, col3 = st.columns([3, 1, 1])

    # Column 1: Description
    with col1:
        description = get_phase_description(phase_key)
        st.markdown(description)

    # Column 2: Run button
    with col2:
        button_key = f"run_{phase_key}"
        if st.button(f"▶ Run {phase_name}", key=button_key, disabled=not can_run):
            spinner_suffix = get_phase_spinner_suffix(phase_key)
            with st.spinner(f"Running {phase_name.lower()} agent...{spinner_suffix}"):
                # Note: Using run_func directly (no longer need run_with_extras_func parameter)
                state = run_func(state)
                st.session_state["step_state"] = state
                st.success(f"{phase_name} completed!")
                st.rerun()

    # Column 3: Regenerate button
    with col3:
        regen_key = f"regen_{phase_key}"
        regen_disabled = get_phase_regenerate_disabled(phase_key, state)
        if st.button("🔄 Regenerate", key=regen_key, disabled=regen_disabled):
            spinner_suffix = get_phase_spinner_suffix(phase_key)
            with st.spinner(f"Regenerating...{spinner_suffix}"):
                state = run_func(state)
                st.session_state["step_state"] = state
                st.success(f"{phase_name} regenerated!")
                st.rerun()

    # Use enhanced phase runner for extras
    spinner_suffix = get_phase_spinner_suffix(phase_key)
    state, _ = display_enhanced_phase_runner(
        phase_name=phase_name,
        phase_key=phase_key,
        run_func=run_func,
        run_with_extras_func=run_func,  # Use run_func directly
        state=state,
        user_input="",
        can_run=can_run,
        spinner_message_run=f"Running {phase_name.lower()} with your additions...{spinner_suffix}",
        spinner_message_regen=f"Regenerating with your additions...{spinner_suffix}",
        success_message_run=f"{phase_name} completed with extras!",
        success_message_regen=f"{phase_name} regenerated with extras!",
        has_content_check=has_content_check,
        content_check=content_check,
    )

    return state


def display_outline_editor(state: PipelineState) -> PipelineState:
    """Display and allow editing of the outline."""
    st.subheader("📝 Presentation Outline")

    if not state.outline:
        st.warning("No outline generated yet.")
        return state

    st.markdown("#### Edit Outline (optional)")

    # Editable topic
    new_topic = st.text_input(
        "Topic", value=state.outline.topic, help="Edit the presentation topic"
    )

    # Editable audience
    new_audience = st.text_input(
        "Target Audience", value=state.outline.audience, help="Edit the target audience"
    )

    # Editable sections
    st.markdown("**Sections:**")
    new_sections = []
    for i, section in enumerate(state.outline.sections):
        new_section = st.text_input(
            f"Section {i+1}",
            value=section,
            key=f"section_{i}",
            help=f"Edit section {i+1}",
        )
        new_sections.append(new_section)

    # Add section button
    if st.button("➕ Add Section"):
        new_sections.append("New Section")

    # Apply changes
    if st.button("✅ Apply Changes", type="primary"):
        state.outline.topic = new_topic
        state.outline.audience = new_audience
        state.outline.sections = [s for s in new_sections if s.strip()]
        st.success("Outline updated!")
        st.rerun()

    return state


def display_research_results(state: PipelineState):
    """Display research findings and citations."""
    st.subheader("🔬 Research & Citations")

    if not hasattr(state, "claims") or not state.claims:
        st.info("No claims extracted (research agent skipped or no claims found)")
        return

    st.markdown(f"**Claims Extracted:** {len(state.claims)}")
    st.markdown(
        f"**Evidence Found:** {len(state.evidences) if hasattr(state, 'evidences') else 0}"
    )
    st.markdown(
        f"**Citations Generated:** {len(state.citations) if hasattr(state, 'citations') else 0}"
    )

    # Show claims
    with st.expander("📄 Claims", expanded=False):
        for i, claim in enumerate(state.claims, 1):
            st.markdown(f"{i}. {claim.text}")

    # Show evidence
    if hasattr(state, "evidences") and state.evidences:
        with st.expander("✅ Evidence", expanded=False):
            for i, ev in enumerate(state.evidences, 1):
                st.markdown(
                    f"**Evidence {i}** (confidence: {ev.confidence:.2f})\n\n"
                    f"Source: `{ev.source}`\n\n"
                    f"Snippet: {ev.snippet}"
                )

    # Show references
    if hasattr(state, "references") and state.references:
        with st.expander("📚 References", expanded=False):
            for ref in state.references:
                st.markdown(f"- {ref}")


def display_content_preview(state: PipelineState) -> PipelineState:
    """Display generated slides with editing capability."""
    st.subheader("📊 Slide Content")

    if not state.content:
        st.warning("No slide content generated yet.")
        return state

    st.markdown(f"**Total Slides:** {len(state.content)}")

    if state.preview_images:
        with st.expander("🖼 Visual Previews", expanded=False):
            for slide_num, image_path in sorted(
                state.preview_images.items(), key=lambda row: int(row[0])
            ):
                if Path(image_path).exists():
                    st.markdown(f"**Slide {slide_num}**")
                    st.image(image_path, use_container_width=True)

    # Display each slide
    for i, slide in enumerate(state.content):
        with st.expander(f"📄 Slide {i+1}: {slide.title}", expanded=False):
            st.markdown(f"**Title:** {slide.title}")

            st.markdown("**Bullets:**")
            for j, bullet in enumerate(slide.bullets, 1):
                st.markdown(f"{j}. {bullet}")

            if slide.speaker_notes:
                st.markdown(f"**Speaker Notes:** {slide.speaker_notes}")

            if slide.citations:
                st.markdown(f"**Citations:** {', '.join(slide.citations)}")

    return state


def display_qa_report(state: PipelineState):
    """Display QA evaluation with detailed breakdown."""
    st.subheader("📊 Quality Assessment")

    if not state.qa_report:
        st.warning("No QA report generated yet.")
        return

    # Scores in columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Content", value=f"{state.qa_report.content_score:.1f}/5.0")

    with col2:
        st.metric(label="Design", value=f"{state.qa_report.design_score:.1f}/5.0")

    with col3:
        st.metric(label="Coherence", value=f"{state.qa_report.coherence_score:.1f}/5.0")

    with col4:
        avg_score = (
            state.qa_report.content_score
            + state.qa_report.design_score
            + state.qa_report.coherence_score
        ) / 3
        st.metric(label="Average", value=f"{avg_score:.1f}/5.0")

    # Detailed feedback
    if state.qa_report.feedback:
        with st.expander("💬 Detailed Feedback", expanded=True):
            st.markdown(state.qa_report.feedback)

    if state.teaching_suggestions:
        with st.expander("🎓 Teaching Suggestions", expanded=True):
            for suggestion in state.teaching_suggestions:
                st.markdown(f"- {suggestion}")


def display_run_history():
    """Display run history from database."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📜 Run History")

    history = load_run_history(limit=5)

    if not history:
        st.sidebar.info("No runs yet")
        return

    for run in history:
        with st.sidebar.expander(f"Run #{run['id']}", expanded=False):
            st.markdown(f"**Time:** {run['created_at'][:19]}")
            st.markdown(f"**Input:** {run['input'][:50]}...")
            if run["qa_scores"]:
                try:
                    scores = json.loads(run["qa_scores"])
                    st.markdown(
                        f"**QA:** C={scores.get('content', 0):.1f}, "
                        f"D={scores.get('design', 0):.1f}, "
                        f"Co={scores.get('coherence', 0):.1f}"
                    )
                except (json.JSONDecodeError, TypeError, KeyError):
                    st.markdown("**QA:** (malformed data)")

            # Validate path is within artifacts directory before allowing download
            if run["output_path"]:
                output_path = Path(run["output_path"])
                artifacts_dir = Path("artifacts").resolve()
                try:
                    resolved_path = output_path.resolve()
                    if (
                        resolved_path.is_relative_to(artifacts_dir)
                        and resolved_path.exists()
                    ):
                        with open(resolved_path, "rb") as f:
                            st.download_button(
                                "⬇ Download",
                                data=f.read(),
                                file_name=resolved_path.name,
                                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                                key=f"download_history_{run['id']}",
                            )
                except (ValueError, OSError):
                    # Path validation failed or file not accessible
                    pass


def display_run_outline(outline: dict):
    """Display presentation outline from run history."""
    if not outline:
        st.info("No outline data available")
        return

    st.subheader(outline.get("topic", "N/A"))

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Audience:** {outline.get('audience', 'N/A')}")
    with col2:
        st.write(f"**Level:** {outline.get('educational_level', 'N/A')}")

    if outline.get("learning_objectives"):
        st.write("**Learning Objectives:**")
        for obj in outline["learning_objectives"]:
            st.write(
                f"- {obj.get('objective', 'N/A')} ({obj.get('bloom_level', 'N/A')})"
            )

    if outline.get("prerequisite_knowledge"):
        st.write("**Prerequisites:**")
        for prereq in outline["prerequisite_knowledge"]:
            st.write(f"- {prereq}")

    if outline.get("sections"):
        st.write("**Sections:**")
        for i, section in enumerate(outline["sections"], 1):
            st.write(f"{i}. {section}")


def display_run_slides(content: list):
    """Display slide content from run history."""
    if not content:
        st.info("No slide content available")
        return

    for i, slide in enumerate(content, 1):
        with st.expander(f"Slide {i}: {slide.get('title', 'Untitled')}"):
            st.write(f"**Title:** {slide.get('title', 'N/A')}")

            if slide.get("bullets"):
                st.write("**Content:**")
                for bullet in slide["bullets"]:
                    st.write(f"• {bullet}")

            if slide.get("speaker_notes"):
                st.write("**Speaker Notes:**")
                st.write(slide["speaker_notes"])

            if slide.get("citations"):
                st.write("**Citations:**")
                for citation in slide["citations"]:
                    st.write(f"- {citation}")


def display_run_research(research: dict):
    """Display research data from run history."""
    if not research:
        st.info("No research data available")
        return

    if research.get("claims"):
        st.write("**Claims Found:**")
        for claim in research["claims"]:
            st.write(f"- {claim}")

    if research.get("evidences"):
        st.write("**Evidence:**")
        for evidence in research["evidences"]:
            st.write(f"- {evidence}")

    if research.get("citations"):
        st.write("**Citations:**")
        for citation in research["citations"]:
            st.write(f"- {citation}")


def display_run_qa(qa_scores: dict, qa_feedback: str):
    """Display QA report from run history."""
    if qa_scores:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Content", f"{qa_scores.get('content', 0):.1f}/5.0")
        with col2:
            st.metric("Design", f"{qa_scores.get('design', 0):.1f}/5.0")
        with col3:
            st.metric("Coherence", f"{qa_scores.get('coherence', 0):.1f}/5.0")

    st.write("**Feedback:**")
    st.write(qa_feedback or "No feedback available")


def display_run_download(output_path: str, run_id: int):
    """Display download button for run PPTX."""
    if not output_path or not Path(output_path).exists():
        st.warning("PPTX file is no longer available")
        return

    with open(output_path, "rb") as f:
        st.download_button(
            "⬇ Download PPTX",
            data=f.read(),
            file_name=Path(output_path).name,
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )


def tab_run_history():
    """Tab to view detailed history of all previous runs."""
    st.markdown("## 📚 Run History")

    cp = CheckpointManager()
    runs = cp.list_runs(limit=100)

    if not runs:
        st.info("No previous runs yet. Generate a presentation to see history!")
        return

    # Run selector
    run_options = [
        f"Run #{r['id']}: {r['input'][:40] if len(r['input']) > 40 else r['input']}... ({r['created_at'][:10]})"
        for r in runs
    ]
    selected_idx = st.selectbox(
        "Select a run to view:", range(len(runs)), format_func=lambda i: run_options[i]
    )
    selected_run = runs[selected_idx]

    # Load full run details
    run_details = cp.get_run_details(selected_run["id"])

    if not run_details:
        st.error("Could not load run details")
        return

    # Display run information
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Created", run_details["created_at"][:16])
    with col2:
        duration = run_details.get("execution_time_seconds") or 0
        st.metric("Duration", f"{duration:.1f}s" if duration else "N/A")
    with col3:
        mode = "Educational" if run_details.get("educational_mode") else "Standard"
        st.metric("Mode", mode)

    st.divider()

    # Tabs for different views
    tab_outline, tab_slides, tab_research, tab_qa, tab_download = st.tabs(
        ["📋 Outline", "🎯 Slides", "📚 Research", "✅ QA", "⬇️ Download"]
    )

    with tab_outline:
        display_run_outline(run_details.get("outline"))

    with tab_slides:
        display_run_slides(run_details.get("content"))

    with tab_research:
        display_run_research(run_details.get("research"))

    with tab_qa:
        display_run_qa(run_details.get("qa_scores"), run_details.get("qa_feedback", ""))

    with tab_download:
        display_run_download(run_details.get("output_path"), run_details["id"])


def main() -> None:
    st.set_page_config(
        page_title="PPTX Agent - Full Featured",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Sidebar configuration
    display_model_configuration()
    display_run_history()

    # Main header
    st.title("🎨 PPTX Agent - Complete Interface")

    # Mode selection
    mode_tab1, mode_tab2, mode_tab3, mode_tab4, mode_tab5 = st.tabs(
        [
            "🚀 Quick Generate",
            "🔧 Step-by-Step",
            "⚙️ Settings",
            "📖 Documentation",
            "📚 Run History",
        ]
    )

    # ==================== TAB 1: QUICK GENERATE ====================
    with mode_tab1:
        st.markdown(
            "Generate a presentation in one click. The system will run all agents "
            "automatically and create a PowerPoint file."
        )

        # Pipeline selection
        col1, col2 = st.columns([3, 1])
        with col1:
            user_input = st.text_area(
                "Presentation Topic / Brief *",
                value="Benefits of renewable energy for urban communities",
                height=100,
                help="Describe your presentation topic. Be specific for best results.",
                placeholder="Example: Climate change mitigation strategies for coastal cities",
            )

        with col2:
            use_langgraph = st.checkbox(
                "Use LangGraph",
                value=False,
                help="Use LangGraph StateGraph implementation (experimental)",
            )

            show_details = st.checkbox(
                "Show Details",
                value=True,
                help="Show outline, research, and content preview",
            )

        # Educational mode toggle
        educational_mode = display_educational_toggle()

        # Template selection
        st.markdown("---")
        use_template = st.checkbox(
            "📐 Use Design Template",
            value=False,
            help="Apply a visual design template to the presentation",
        )

        selected_template = None
        if use_template:
            try:
                from src.tools.template_manager import TemplateManager

                tm = TemplateManager()
                templates = tm.list_templates()

                if templates:
                    selected_template = st.selectbox(
                        "Select Template",
                        options=["None (Plain)"] + templates,
                        help="Choose a template design for your presentation",
                    )
                    if selected_template == "None (Plain)":
                        selected_template = None
                else:
                    st.warning(
                        "No templates available. Run `python scripts/create_default_templates.py` or upload templates in Settings."
                    )
            except Exception as e:
                st.error(f"Error loading templates: {e}")

        # Validation
        input_valid = len(user_input.strip()) >= 10
        if not input_valid and user_input:
            st.warning("⚠️ Topic must be at least 10 characters long.")

        # Generate button
        if st.button(
            "▶ Generate Presentation",
            type="primary",
            disabled=not input_valid,
            use_container_width=True,
            key="quick_generate",
        ):
            with st.spinner(
                "⏳ Generating presentation... This may take 30-60 seconds."
            ):
                try:
                    # Run pipeline with educational mode and template
                    if use_langgraph:
                        state = run_langgraph_pipeline(
                            user_input, educational_mode=educational_mode
                        )
                        # Set template for langgraph if selected
                        if selected_template:
                            state.template_name = selected_template
                    else:
                        state = run_pipeline(
                            user_input,
                            educational_mode=educational_mode,
                            template_name=selected_template,
                        )

                    # Store in session state
                    st.session_state["last_state"] = state

                    if state.errors:
                        st.error(
                            "❌ **Errors occurred:**\n\n" + "\n".join(state.errors)
                        )
                    else:
                        st.success("✅ **Presentation generated successfully!**")

                        # Show details if requested
                        if show_details:
                            st.markdown("---")

                            # Outline with pedagogical elements
                            if state.outline:
                                with st.expander("📝 Outline", expanded=False):
                                    st.markdown(f"**Topic:** {state.outline.topic}")
                                    st.markdown(
                                        f"**Audience:** {state.outline.audience}"
                                    )

                                    # Show learning objectives if present (educational mode)
                                    if (
                                        hasattr(state.outline, "learning_objectives")
                                        and state.outline.learning_objectives
                                    ):
                                        st.markdown("")
                                        display_learning_objectives(state.outline)
                                        st.markdown("")

                                    # Show prerequisite knowledge if present
                                    if (
                                        hasattr(state.outline, "prerequisite_knowledge")
                                        and state.outline.prerequisite_knowledge
                                    ):
                                        st.markdown("")
                                        display_prerequisite_knowledge(state.outline)
                                        st.markdown("")

                                    st.markdown("**Sections:**")
                                    for i, section in enumerate(
                                        state.outline.sections, 1
                                    ):
                                        st.markdown(f"{i}. {section}")

                            # Research
                            display_research_results(state)

                            # Content - use pedagogical preview if educational mode
                            if educational_mode:
                                display_pedagogical_content_preview(state)
                            else:
                                display_content_preview(state)

                        # QA Report - use pedagogical dashboard if educational mode
                        st.markdown("---")
                        if educational_mode:
                            display_pedagogical_qa_dashboard(state)
                        else:
                            display_qa_report(state)

                        # Download
                        if state.pptx_path and Path(state.pptx_path).exists():
                            st.markdown("---")
                            with open(state.pptx_path, "rb") as f:
                                data = f.read()

                            col1, col2, col3 = st.columns([2, 1, 1])
                            with col1:
                                st.download_button(
                                    label="⬇ Download PowerPoint",
                                    data=data,
                                    file_name=Path(state.pptx_path).name,
                                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                                    type="primary",
                                    use_container_width=True,
                                )
                            with col2:
                                file_size = len(data) / 1024
                                st.metric("File Size", f"{file_size:.1f} KB")
                            with col3:
                                st.metric(
                                    "Slides", len(state.content) if state.content else 0
                                )

                            st.caption(f"💾 Saved to: `{state.pptx_path}`")

                except Exception as e:
                    st.error(f"❌ **Exception occurred:**\n\n{str(e)}")
                    import traceback

                    with st.expander("🐛 Debug Traceback"):
                        st.code(traceback.format_exc())

    # ==================== TAB 2: STEP-BY-STEP ====================
    with mode_tab2:
        st.markdown(
            "Execute each agent individually and review outputs before proceeding. "
            "This gives you full control over the generation process."
        )

        # Initialize session state
        if "step_state" not in st.session_state:
            st.session_state["step_state"] = PipelineState(user_input="")

        step_state: PipelineState = st.session_state["step_state"]

        # Input
        st.markdown("**Step 0: Input**")
        step_input = st.text_area(
            "Topic / Brief",
            value=(
                step_state.user_input
                if step_state.user_input
                else "Climate change mitigation strategies"
            ),
            height=80,
            key="step_input",
        )

        # Educational mode toggle for step-by-step
        step_educational_mode = st.checkbox(
            "🎓 Educational Mode",
            value=(
                step_state.educational_mode
                if hasattr(step_state, "educational_mode")
                else False
            ),
            key="step_educational_mode",
            help="Generate with learning objectives and pedagogical elements",
        )

        if st.button("✅ Set Input", key="set_input"):
            step_state.user_input = step_input
            step_state.educational_mode = step_educational_mode
            st.session_state["step_state"] = step_state
            st.success("Input set!")

        st.markdown("---")

        # Step 1: Brainstorm
        step_state = display_phase_section(
            step_number=1,
            phase_name="Brainstorm",
            phase_key="brainstorm",
            run_func=run_brainstorm,
            run_with_extras_func=run_brainstorm,  # Using run_func directly
            state=step_state,
            can_run=bool(step_state.user_input),
            has_content_check=False,
            content_check=False,
        )

        if step_state.outline:
            # Use educational outline editor if educational mode
            if step_state.educational_mode:
                step_state = display_educational_outline_editor(step_state)
            else:
                step_state = display_outline_editor(step_state)

            # Add regenerate button for edited outline
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button(
                    "🔄 Regenerate with Edits",
                    key="regen_brainstorm_edits",
                    type="secondary",
                ):
                    with st.spinner("Regenerating based on your edits..."):
                        step_state = run_brainstorm(step_state)
                        st.session_state["step_state"] = step_state
                        st.success("Outline regenerated from your edits!")
                        st.rerun()

            st.session_state["step_state"] = step_state

        st.markdown("---")

        # Step 2: Research
        step_state = display_phase_section(
            step_number=2,
            phase_name="Research",
            phase_key="research",
            run_func=run_research,
            run_with_extras_func=run_research,
            state=step_state,
            can_run=bool(step_state.outline),
            has_content_check=False,
            content_check=False,
        )

        if hasattr(step_state, "claims"):
            display_research_results(step_state)

        st.markdown("---")

        # Step 3: Content
        research_completed = bool(getattr(step_state, "research_completed", False))
        step_state = display_phase_section(
            step_number=3,
            phase_name="Content",
            phase_key="content",
            run_func=run_content,
            run_with_extras_func=run_content,
            state=step_state,
            can_run=bool(step_state.outline) and research_completed,
            has_content_check=False,
            content_check=False,
        )

        if step_state.content:
            # Use pedagogical preview if educational mode
            if step_state.educational_mode:
                display_pedagogical_content_preview(step_state)
            else:
                step_state = display_content_preview(step_state)
            st.session_state["step_state"] = step_state

        st.markdown("---")

        # Step 4: Design
        step_state = display_phase_section(
            step_number=4,
            phase_name="Design",
            phase_key="design",
            run_func=run_design,
            run_with_extras_func=run_design,
            state=step_state,
            can_run=bool(step_state.content),
            has_content_check=True,
            content_check=bool(step_state.content),
        )

        if step_state.pptx_path and Path(step_state.pptx_path).exists():
            st.info(f"✅ PPTX file created: `{step_state.pptx_path}`")

        st.markdown("---")

        # Step 5: QA
        step_state = display_phase_section(
            step_number=5,
            phase_name="QA",
            phase_key="qa",
            run_func=run_qa,
            run_with_extras_func=run_qa,
            state=step_state,
            can_run=bool(step_state.content),
            has_content_check=True,
            content_check=bool(step_state.content),
        )

        if step_state.qa_report:
            # Use pedagogical dashboard if educational mode
            if step_state.educational_mode:
                display_pedagogical_qa_dashboard(step_state)
            else:
                display_qa_report(step_state)

        st.markdown("---")

        # Final download
        if step_state.pptx_path and Path(step_state.pptx_path).exists():
            with open(step_state.pptx_path, "rb") as f:
                data = f.read()
            st.download_button(
                label="⬇ Download Final Presentation",
                data=data,
                file_name=Path(step_state.pptx_path).name,
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                type="primary",
                use_container_width=True,
                key="step_download",
            )

        # Reset button
        if st.button("🔄 Reset All Steps", key="reset_steps"):
            st.session_state["step_state"] = PipelineState(user_input="")
            st.success("Reset completed!")
            st.rerun()

    # ==================== TAB 3: SETTINGS ====================
    with mode_tab3:
        display_settings_ui()

    # ==================== TAB 4: DOCUMENTATION ====================
    with mode_tab4:
        st.markdown("""
        ## 📖 PPTX Agent Documentation

        ### Architecture

        The PPTX Agent uses a multi-agent architecture with 5 specialized agents:

        1. **Brainstorm Agent** (uses LLM)
           - Generates presentation outline
           - Identifies topic and target audience
           - Creates 3-7 logical sections

        2. **Research Agent** (no LLM - local search)
           - Extracts factual claims
           - Searches local corpus for evidence
           - Generates citation markers

        3. **Content Agent** (uses LLM)
           - Generates slide content
           - Creates bullets and speaker notes
           - Includes citations

        4. **Design Agent** (no LLM - python-pptx)
           - Assembles PowerPoint file
           - Adds references slide
           - Saves to artifacts/

        5. **QA Agent** (uses LLM)
           - Evaluates content, design, coherence
           - Provides actionable feedback
           - Scores on 1-5 scale

        ### Configuration

        **File:** `ai_config.properties` (in project root)

        **Providers:**
        - `mock`: Offline deterministic mode (for testing)
        - `ollama`: Local AI models via Ollama
        - `openrouter`: Cloud AI via OpenRouter API

        **Agent-Specific Settings:**
        ```properties
        agent.brainstorm.temperature=0.8  # More creative
        agent.content.temperature=0.7     # Balanced
        agent.qa.temperature=0.2          # More objective
        ```

        ### Current Configuration
        """)

        ai_config = get_ai_config()
        ai = get_ai_interface()
        config_display = {
            "Provider": ai_config.get_provider(),
            "Brainstorm Model": ai.get_model_info("brainstorm")["model"],
            "Content Model": ai.get_model_info("content")["model"],
            "QA Model": ai.get_model_info("qa")["model"],
        }

        for key, value in config_display.items():
            st.markdown(f"- **{key}:** `{value}`")

        st.markdown("""
        ### Quality Scores

        QA Agent evaluates presentations on three dimensions:

        - **Content Score (1-5):** Informativeness, specificity, citations
        - **Design Score (1-5):** Clarity, formatting, visual hierarchy
        - **Coherence Score (1-5):** Logical flow, narrative arc

        **Score Guide:**
        - 5.0: Excellent, publication-ready
        - 4.0: Good, minor improvements
        - 3.0: Acceptable, some revisions
        - 2.0: Below standards
        - 1.0: Poor, redesign needed

        ### Tips for Best Results

        1. **Be Specific:** Include target audience and scope in your topic
        2. **Review Outline:** Edit sections before generating content
        3. **Check Citations:** Ensure claims are supported by evidence
        4. **Iterate:** Use QA feedback to improve
        5. **Choose Right Provider:**
           - `mock`: Fast testing (deterministic)
           - `ollama`: Local, private, free
           - `openrouter`: Cloud, powerful, costs money

        ### Keyboard Shortcuts

        - `Ctrl+Enter`: Submit form
        - `Tab`: Navigate between fields
        - `Ctrl+R`: Reload configuration

        ### Troubleshooting

        **Issue: Low QA scores**
        - Make topic more specific
        - Ensure local corpus has relevant content
        - Try different model/temperature settings

        **Issue: No citations found**
        - Add relevant documents to `corpus/` folder
        - Check that documents are indexed
        - Research agent only searches local files

        **Issue: Slow generation**
        - Use `mock` provider for testing
        - Reduce `max_tokens` in config
        - Use smaller Ollama models (e.g., llama3:7b)

        ### Support

        - Documentation: `AI_ARCHITECTURE.md`
        - Testing Guide: `COMPREHENSIVE_AGENT_TESTING.md`
        - Config Help: `ai_config.properties` (comments)
        """)

    # ==================== TAB 5: RUN HISTORY ====================
    with mode_tab5:
        tab_run_history()


if __name__ == "__main__":
    main()

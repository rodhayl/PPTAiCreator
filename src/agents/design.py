"""Design and assembly agent.

This agent takes the generated slide content and citations and produces an
actual PowerPoint file using `python-pptx`.  It uses the `CitationManager`
to produce a references slide and saves the file to the path stored in
`state.pptx_path`.

Enhanced with:
- Section divider slides
- Agenda slide
- Educational features display
- Logo and footer support
- Enhanced speaker notes
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ..state import PipelineState
from ..tools.citations import CitationManager
from ..tools.pptx_builder import build_presentation, PresentationConfig


def run_design(state: PipelineState) -> PipelineState:
    """Build PowerPoint presentation with enhanced features.

    Args:
        state: Pipeline state containing slide content and metadata

    Returns:
        Updated state with pptx_path set
    """
    if not state.content:
        state.errors.append(
            "No slide content available for PPTX generation. Please run the content agent first."
        )
        return state

    # Use citation manager stored in state if available; otherwise rebuild
    references = getattr(state, "references", None)
    if not references:
        # No references prepared; build from evidences
        cm = CitationManager()
        cm.register_evidence(state.evidences)
        references = cm.build_references_slide()

    # Determine output path
    output_dir = Path("artifacts")
    output_dir.mkdir(exist_ok=True, parents=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"presentation_{timestamp}.pptx"

    # Build presentation configuration
    template_name = getattr(state, "template_name", None)
    config = _build_presentation_config()

    # Build presentation with optional template and enhanced features
    try:
        build_presentation(
            slides=state.content,
            references=references,
            output_path=str(output_path),
            template_name=template_name,
            outline=getattr(state, "outline", None),
            config=config,
        )
        state.pptx_path = str(output_path)
    except Exception as e:
        error_msg = f"Failed to generate PowerPoint file: {str(e)}"
        # Add helpful context if relevant
        if "logo" in str(e).lower():
            error_msg += "\nTip: Check that the logo path in configuration is correct."
        state.errors.append(error_msg)

    return state


def _build_presentation_config() -> PresentationConfig:
    """Build presentation configuration from application settings.

    Returns:
        PresentationConfig object with settings from config file
    """
    try:
        # Note: logo and footer config would be loaded from ai_config.properties
        # For now, use defaults or environment variables
        return PresentationConfig(
            logo_path=None,  # TODO: Load from config
            footer_text=None,  # TODO: Load from config
            show_page_numbers=True,
            font_name="Calibri",
            title_font_size=44,
            body_font_size=20,
        )
    except Exception:
        # Return defaults if config loading fails
        return PresentationConfig()

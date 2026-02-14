"""Presentation utility functions.

This module provides shared helper functions for presentation building and
template management.
"""

from __future__ import annotations

from typing import List, Optional

from ..schemas import SlideContent, PresentationOutline


def get_section_boundaries(
    slides: List[SlideContent], outline: Optional[PresentationOutline]
) -> List[int]:
    """Get indices of slides where new sections begin.

    This function calculates where section dividers should be placed based on
    the number of sections in the outline and the number of slides generated.

    Args:
        slides: List of slide content objects
        outline: Presentation outline with section information

    Returns:
        List of slide indices where section boundaries occur

    Example:
        >>> slides = [slide1, slide2, slide3, slide4, slide5, slide6]
        >>> outline = PresentationOutline(sections=["Intro", "Main", "Conclusion"])
        >>> boundaries = get_section_boundaries(slides, outline)
        >>> # Returns [2, 4] indicating boundaries before slides 2 and 4
    """
    if not outline or len(outline.sections) <= 1:
        return []

    # Distribute sections across slides (assuming roughly equal distribution)
    num_sections = len(outline.sections)
    num_slides = len(slides)

    if num_slides < num_sections:
        # Fewer slides than sections, put section divider at start
        return list(
            range(
                0, min(num_sections - 1, num_slides), max(1, num_slides // num_sections)
            )
        )

    # Calculate breakpoints
    slides_per_section = num_slides // num_sections
    boundaries = []

    for i in range(1, num_sections):
        boundary = i * slides_per_section
        if boundary < num_slides:
            boundaries.append(boundary)

    return boundaries

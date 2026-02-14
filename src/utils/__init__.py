"""Utility functions for PPTAgent.

This package contains shared utility functions used across the application.
"""

from __future__ import annotations

from .json_repair import parse_json_with_repair
from .presentation_helpers import get_section_boundaries

__all__ = ["parse_json_with_repair", "get_section_boundaries"]

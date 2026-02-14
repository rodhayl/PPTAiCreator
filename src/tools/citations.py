"""Citation management utilities.

This module handles deduplication and formatting of citations collected from
evidence gathered during fact checking.  It returns a list of citation
strings (e.g. `[1]`) that can be attached to slide content and a mapping
from citation indices to reference entries for the final references slide.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from ..schemas import Evidence


@dataclass
class ReferenceEntry:
    key: str
    title: str
    published_at: str
    source: str


class CitationManager:
    """Manages citation indices and reference entries."""

    def __init__(self):
        self._refs: Dict[str, ReferenceEntry] = {}
        self._order: List[str] = []

    def register_evidence(self, evidences: List[Evidence]) -> None:
        """Register evidence objects and assign citation keys."""
        for ev in evidences:
            key = ev.source
            if key and key not in self._refs:
                # Use the file name (last part of URL) as a title fallback
                title = key.rsplit("/", 1)[-1]
                self._refs[key] = ReferenceEntry(
                    key=key,
                    title=title,
                    published_at=ev.published_at or "",
                    source=ev.source,
                )
                self._order.append(key)

    def get_citation_marker(self, evidence: Evidence) -> str:
        """Return a citation marker (e.g. `[1]`) for the given evidence."""
        if evidence.source not in self._refs:
            self.register_evidence([evidence])
        idx = self._order.index(evidence.source) + 1
        return f"[{idx}]"

    def build_references_slide(self) -> List[str]:
        """Return a list of reference strings for the references slide."""
        entries = []
        for i, key in enumerate(self._order, start=1):
            ref = self._refs[key]
            entries.append(f"[{i}] {ref.title} ({ref.published_at}) — {ref.source}")
        return entries

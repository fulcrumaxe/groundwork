"""Prerequisite chain visual path at module top (I-147).

Pure HTML builder over an ordered concept list — no I/O, no DB changes.
Anchors reuse lessons.slug so jump links match lesson section ids.
"""
from __future__ import annotations

import html

from .lessons import slug as lesson_slug


def _title(concept) -> str:
    if isinstance(concept, dict):
        return str(concept.get("name", concept.get("concept", "")))
    return str(concept)


def chain_html(concepts) -> str:
    """Ordered understand-X-first path; stable id='prereq' anchor."""
    items = [c for c in (concepts or []) if _title(c).strip()]
    if not items:
        return ""
    steps = []
    for concept in items:
        name = _title(concept).strip()
        anchor = lesson_slug(name)
        steps.append(
            f"<a href='#{html.escape(anchor, quote=True)}'>"
            f"{html.escape(name)}</a>")
    return "<nav id='prereq' aria-label='Prerequisites'>" + " → ".join(steps) + "</nav>"

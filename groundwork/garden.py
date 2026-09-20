"""Concept garden: streak-free gardener metaphor (seed -> sprout -> tree).

Maps a 0-1 mastery score to a growth stage. Pure function of the score
only — no streaks, counts, dates, or I/O. Complements ownership.py
mastery conventions without changing the DB.
"""
from __future__ import annotations

import html

SEED = "seed"
SPROUT = "sprout"
TREE = "tree"

STAGES = (SEED, SPROUT, TREE)

_SEED_BELOW = 0.4
_SPROUT_BELOW = 0.8


def stage(mastery) -> str:
    """Growth stage for a 0-1 mastery score."""
    try:
        v = float(mastery)
    except (TypeError, ValueError):
        return SEED
    if v != v:  # NaN
        return SEED
    if v < _SEED_BELOW:
        return SEED
    if v < _SPROUT_BELOW:
        return SPROUT
    return TREE


def garden_html(mastery, concept: str = "") -> str:
    """Garden-stage chip HTML; stable id='garden' anchor."""
    st = stage(mastery)
    label = html.escape(concept) if isinstance(concept, str) else ""
    return (
        f"<span id='garden' class='garden garden-{st}' "
        f"data-stage='{st}' title='Mastery stage: {st}'>{label or st}</span>"
    )

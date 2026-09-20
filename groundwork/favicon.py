"""Site favicon: one static SVG mark so browsers stop 404ing /favicon.ico.

Every page load was logging a console 404 for the missing icon. This is
the static baseline; per-page state (due-count badge) remains backlog
item I-87, which can extend this route later.
"""
from __future__ import annotations


def favicon_svg() -> str:
    """64px ink rounded square with a paper 'G' — offline-safe, no refs."""
    return (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>"
        "<rect width='64' height='64' rx='12' fill='#1a1a1a'/>"
        "<text x='32' y='44' font-size='36' text-anchor='middle' "
        "fill='#fff' font-family='Georgia,serif'>G</text></svg>")

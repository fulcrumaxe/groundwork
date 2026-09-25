"""Growth-rings visualization: each owned concept adds a ring (F-103).

A tree lays down one ring per year it stood its ground; the learner's
History page lays down one SVG ring per owned concept — proof you can
count, streak-free. Pure functions over counts (owned/total come from
ownhead.counts, the same owned rule as the headline), stdlib only.

Caller path (History page, never a Status demo):
``history.history_html`` appends ``section_html`` in both the data
and the empty branch. The section always renders (anchor-stable for
the tour); empty libraries get rings-to-earn copy instead of circles.
Never raises.
"""
from __future__ import annotations

from . import ownhead as ownheadmod

STATUS_ANCHOR = "status-b22-growrings"

#: Rings drawn before the overflow note takes over; the count stays exact.
MAX_RINGS = 30


def ring_count(owned) -> int:
    """Drawable rings for an owned count; hostile input yields 0."""
    try:
        return max(0, min(MAX_RINGS, int(owned)))
    except Exception:  # noqa: BLE001 -- counting never raises
        return 0


def rings_svg(owned, total) -> str:
    """Concentric-circle SVG: one ring per owned concept, count at center.

    ``""`` only when there is nothing to say (no concepts at all);
    owned-but-zero still draws the stump circle so the section reads
    as "no rings yet" rather than vanishing. Never raises.
    """
    try:
        total_i = int(total)
        if total_i <= 0:
            return ""
        n = ring_count(owned)
        owned_i = max(0, int(owned))
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""
    try:
        outer = 10 + 4 * n
        size = 2 * (outer + 8)
        circles = []
        for i in range(n):
            r = 10 + 4 * i
            op = 0.35 + 0.65 * ((i + 1) / n) if n else 0.35
            circles.append(
                f"<circle cx='{outer + 8}' cy='{outer + 8}' r='{r}' "
                f"fill='none' stroke='var(--ink)' stroke-opacity='{op:.2f}'/>")
        if not circles:
            circles.append(
                f"<circle cx='{outer + 8}' cy='{outer + 8}' r='6' "
                "fill='none' stroke='var(--stale)' stroke-dasharray='2 2'/>")
        overflow = ""
        if owned_i > MAX_RINGS:
            overflow = (f"<p><small>+{owned_i - MAX_RINGS} more rings "
                        "beyond the outer one.</small></p>")
        return (
            f"<div id='growth-rings'><svg viewBox='0 0 {size} {size}' "
            f"width='{min(size, 220)}' height='{min(size, 220)}' role='img' "
            f"aria-label='{owned_i} of {total_i} concepts owned'>"
            + "".join(circles) +
            f"<text x='{outer + 8}' y='{outer + 11}' text-anchor='middle' "
            f"font-size='12' fill='var(--ink)'>{owned_i}</text></svg>"
            f"<p><small>One ring per owned concept — "
            f"{owned_i} of {total_i}.</small></p>{overflow}</div>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def section_html(db_path: str) -> str:
    """Always-rendered History section; the anchor never moves."""
    try:
        c = ownheadmod.counts(db_path)
        svg = rings_svg(c["owned"], c["concepts"])
        if not svg:
            svg = ("<p>No concepts yet — your first ring grows with your "
                   "first owned concept.</p>")
        return (f"<h2 id='growth-rings-head'>Growth rings</h2>{svg}")
    except Exception:  # noqa: BLE001 -- history never breaks
        return ("<h2 id='growth-rings-head'>Growth rings</h2>"
                "<p>Rings temporarily unavailable.</p>")


def status_section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        sample = rings_svg(3, 9)
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Growth rings "
            "<small>(feature)</small></h3>"
            "<p>Every owned concept lays down a ring — "
            "<code>groundwork/growrings.py</code> draws one concentric "
            "SVG ring per owned concept (same owned rule as the "
            "headline) on the History page; empty libraries get "
            "rings-to-earn copy. A live sample renders below.</p>"
            f"{sample}")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Growth rings</h3>"
                "<p>Growth-rings help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "growth-rings",
        "kind": "feature",
        "title": "Growth rings",
        "blurb": ("One ring per owned concept — your proof, counted "
                  "in wood."),
        "path": "/reviews",
        "anchor": "growth-rings-head",
    }

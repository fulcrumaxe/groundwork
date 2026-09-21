"""Due queue as a mission briefing (I-73).

Each Due card reads as a numbered mission card via a CSS counter on
the existing ``#queue article`` selectors: ``briefing_css()`` resets
the counter on ``#queue`` and increments per ``article``, stamping a
``MISSION 01``-style badge with ``::before`` — zero JS, so queue
reorders, snoozes, and group collapses need no markup. The inline
``Card i of n`` position line and the ``#up-next`` tag are untouched;
the counter badge composes with them, it never duplicates them. The
``#digest`` Today block styles as the briefing header.
``briefing_css()`` returns raw CSS declarations only, never
``<style>`` tags — the parent concatenates it into the head wire next
to ``progbar_css()``. ``briefing_number()`` formats matching labels
for any server-rendered use and fails closed. Pure functions, stdlib
only, no I/O, no DB changes.
"""
from __future__ import annotations

STATUS_ANCHOR = "status-b12-briefing"

MISSION_FALLBACK = "MISSION --"
MAX_PADDED = 99

# Due-page accent from groundwork/palette.py (no generic --accent exists).
ACCENT = "var(--accent-due,#0b6e4f)"
PAPER = "var(--paper,#fff)"


def briefing_number(n=1) -> str:
    """Format a ``MISSION 03``-style label; fail-closed, never raises.

    Positive ints zero-pad to two digits (``3`` -> ``MISSION 03``);
    numbers above 99 render unpadded (``120`` -> ``MISSION 120``).
    Bools, zero, negatives, and non-numeric input fail closed to
    ``MISSION --`` rather than a lying position.
    """
    try:
        if isinstance(n, bool):
            return MISSION_FALLBACK
        v = int(n)
        if v < 1:
            return MISSION_FALLBACK
        if v <= MAX_PADDED:
            return f"MISSION {v:02d}"
        return f"MISSION {v}"
    except Exception:  # noqa: BLE001 — label lookup must never raise
        return MISSION_FALLBACK


def briefing_css() -> str:
    """Raw CSS declarations: counter-numbered mission cards plus header.

    Never emits ``<style>`` tags; the parent wires this into the head
    stylesheet. Targets only selectors ``due_html`` already renders
    (``#queue``, ``#queue article``, ``article.next``, ``#digest``).
    Never raises.
    """
    try:
        return (
            "#queue{counter-reset:mission}"
            "#queue article{counter-increment:mission;position:relative}"
            "#queue article::before{content:\"MISSION \""
            " counter(mission,decimal-leading-zero);display:inline-block;"
            "font-size:.75rem;font-weight:700;letter-spacing:.08em;"
            f"color:{ACCENT};border:1px solid "
            f"{ACCENT};border-radius:999px;"
            "padding:.05rem .6rem;margin-bottom:.5rem}"
            f"#queue article.next::before{{background:{ACCENT};"
            f"color:{PAPER}}}"
            f"#digest{{border-left:4px solid {ACCENT};"
            "padding:.25rem 0 .25rem .75rem}"
            "#digest h2{margin:.1rem 0;font-size:1.05rem;letter-spacing:.04em}"
        )
    except Exception:  # noqa: BLE001 — CSS emitter must never raise
        return ("#queue{counter-reset:mission}"
                "#queue article{counter-increment:mission}")


def tour_entry() -> dict:
    """Tour catalog entry for the guided ?tour= banner; never raises."""
    try:
        return {"id": "due-briefing", "kind": "improvement",
                "title": "Due briefing",
                "blurb": "Due cards read as numbered mission cards — "
                         "queue order needs no markup.",
                "path": "/status", "anchor": STATUS_ANCHOR}
    except Exception:  # noqa: BLE001 — registry must never raise
        return {"id": "due-briefing", "kind": "improvement",
                "title": "Due briefing", "blurb": "Numbered mission cards.",
                "path": "/status", "anchor": "status-b12-briefing"}


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Due briefing <small>(improvement)</small></h3>"
        "<p>The Due queue reads like a briefing: every card carries a "
        "<code>MISSION 01</code>-style badge via a CSS counter on the "
        "existing <code>#queue article</code> selectors — zero JS, so "
        "reorders and snoozes need no markup — and the <code>#digest</code> "
        "Today block styles as the briefing header. The inline "
        "<code>Card i of n</code> line and <code>#up-next</code> tag are "
        "untouched. <code>groundwork/briefing.py</code> provides "
        "<code>briefing_css()</code> (raw declarations only, no "
        "<code>&lt;style&gt;</code> tags — the parent concatenates it into "
        "the head wire) and fail-closed <code>briefing_number()</code>.</p>"
    )

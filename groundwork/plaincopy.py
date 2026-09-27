"""Culturally neutral milestone copy (F-143): plain celebration words.

Milestone praise leans on English wordplay and metaphor ("Owntober",
"Nicely done", "writes the first one", "your year in ..."), which
reads as noise to learners from other cultures. This module holds a
small copy table - eight (default, plain) pairs over the exact
rendered strings - plus a tone selector the History join applies to
the three milestone sections. Default tone returns input unchanged
(byte-identical legacy); ?tone=plain restates each mapped string in
factual words. No translation engine, no locale detection, no DB or
schema change. Pure functions, stdlib only, never raises.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b26-plaincopy"

DEFAULT_TONE = "default"
PLAIN_TONE = "plain"

# (default substring as rendered, plain restatement). Defaults are
# byte-exact quotes of the sibling renderers; plains stay factual.
# milestones.py section_html (History "Milestone moments" block):
#   "Milestone moments" heading -> "Milestones"
#   "... writes the first one." empty line -> factual listing line
# seasonevent.py section_html (History "seasonal-event" block):
#   "Owntober" pun -> "October goal"
#   "Nicely done." praise -> "Goal complete."
#   "a gentle seasonal goal, no streak attached." -> "a seasonal goal."
# anniversary.py block_html (History "anniversary" block):
#   "Your year in code comprehension" -> "Twelve months of practice"
#   "a quiet anniversary, not a leaderboard." -> "a private summary."
#   "(first vs second half of your year)" -> "(... of the period)"
COPY = (
    ("Milestone moments",
     "Milestones"),
    ("your first owned concept writes the first one.",
     "your first owned concept will be listed here."),
    ("Owntober",
     "October goal"),
    ("Nicely done.",
     "Goal complete."),
    ("a gentle seasonal goal, no streak attached.",
     "a seasonal goal."),
    ("Your year in code comprehension",
     "Twelve months of practice"),
    ("a quiet anniversary, not a leaderboard.",
     "a private summary."),
    ("(first vs second half of your year)",
     "(first vs second half of the period)"),
)


def tone_from_query(query) -> str:
    """'plain' for ?tone=plain, else 'default'. Never raises.

    Accepts the parse_qs shape history_html already receives
    ({"tone": ["plain"]}) plus a bare-string tone defensively;
    absent, empty, or hostile query reads as default.
    """
    try:
        if not isinstance(query, dict):
            return DEFAULT_TONE
        vals = query.get("tone", [])
        if isinstance(vals, str):
            vals = [vals]
        if not isinstance(vals, (list, tuple)) or not vals:
            return DEFAULT_TONE
        first = str(vals[0]).strip().lower()
        return PLAIN_TONE if first == PLAIN_TONE else DEFAULT_TONE
    except Exception:  # noqa: BLE001 -- tone lookup never raises
        return DEFAULT_TONE


def text(default, tone=DEFAULT_TONE) -> str:
    """Restate one known celebration string; unknown input passes through."""
    try:
        if tone != PLAIN_TONE:
            return default
        for old, new in COPY:
            if default == old:
                return new
        return default
    except Exception:  # noqa: BLE001 -- selector never raises
        return default


def apply(markup, tone=DEFAULT_TONE) -> str:
    """Swap mapped celebration strings in rendered milestone HTML.

    Same call shape as the sections it wraps: html in, html out.
    Default tone returns the input object unchanged (byte-identical
    legacy); plain tone replaces each mapped substring. Never raises.
    """
    try:
        if tone != PLAIN_TONE or not isinstance(markup, str):
            return markup
        out = markup
        for old, new in COPY:
            if old in out:
                out = out.replace(old, new)
        return out
    except Exception:  # noqa: BLE001 -- history never breaks
        return markup


def pairs() -> tuple:
    """The live copy table; the demo and tests read this, not a copy."""
    try:
        return tuple(COPY)
    except Exception:  # noqa: BLE001 -- table read never raises
        return ()


def section_html() -> str:
    """Anchored status subsection with the live mapping table."""
    try:
        rows = "".join(
            f"<tr><td>{html.escape(old)}</td>"
            f"<td>{html.escape(new)}</td></tr>"
            for old, new in COPY)
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Plain milestone copy "
            "<small>(feature)</small></h3>"
            "<p>Milestone praise restated in factual words for learners "
            "from other cultures - wordplay and metaphor out, dates and "
            "counts kept. <code>groundwork/plaincopy.py</code> holds the "
            "copy table plus <code>tone_from_query()</code> and "
            "<code>apply()</code>; <code>history.history_html</code> wraps "
            "the milestone, seasonal and anniversary sections, so "
            "<code>?tone=plain</code> restates them and the default tone "
            "renders byte-identical legacy copy. Live table:</p>"
            "<table class='log'><tr><th>Default</th><th>Plain</th></tr>"
            f"{rows}</table>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Plain milestone copy</h3>"
                "<p>Plain-copy help temporarily unavailable.</p>")


status_section_html = section_html


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "plain-milestone-copy",
        "kind": "feature",
        "title": "Plain milestone copy",
        "blurb": ("Milestone praise in plain factual words - "
                  "?tone=plain restates the wordplay."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }

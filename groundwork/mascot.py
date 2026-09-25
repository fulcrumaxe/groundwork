"""Mascot companion reacting to effort, never wins (F-117).

A small text companion on the Due page that notices attempts —
warming up, in stride, deep in it — and never mentions accuracy,
streaks, or scores. Zero attempts gets a resting line with no
guilt ("ready when you are", never "you skipped"). The mood
derives from today's attempt count only. Always renders;
hostile input rests. Pure reads; never raises.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b23-mascot"

SECTION_ANCHOR = "mascot"


def attempts_today(db_path: str) -> int:
    """Reviews recorded since local midnight UTC; hostile reads 0."""
    try:
        from . import db as dbmod
        from . import sched as schedmod
        today = schedmod.utcnow().strftime("%Y-%m-%dT00:00:00Z")
        con = dbmod.connect(db_path)
        try:
            row = con.execute(
                "SELECT COUNT(*) FROM reviews WHERE reviewed_at >= ?",
                (today,)).fetchone()
            return int(row[0] or 0)
        finally:
            con.close()
    except Exception:  # noqa: BLE001 -- counts must never raise
        return 0


def mood_for(n) -> dict:
    """{mood, line} for an attempt count; hostile input rests."""
    try:
        count = int(n)
    except (TypeError, ValueError):
        count = 0
    if count <= 0:
        return {"mood": "resting",
                "line": "Momo is resting — ready when you are."}
    if count <= 2:
        return {"mood": "warming",
                "line": "Momo is warming up with you — nice start."}
    if count < 10:
        return {"mood": "stride",
                "line": "Momo is in stride — steady attempts, no rush."}
    return {"mood": "deep",
            "line": "Momo is deep in it with you — remember water."}


def line_html(db_path: str) -> str:
    """Companion line for the Due page; always renders."""
    try:
        mood = mood_for(attempts_today(db_path))
        return (f"<p id='{SECTION_ANCHOR}' class='mascot "
                f"mascot-{html.escape(mood['mood'])}'>"
                f"{html.escape(mood['line'])}</p>")
    except Exception:  # noqa: BLE001 -- line must never raise
        return (f"<p id='{SECTION_ANCHOR}' class='mascot'>"
                "Momo is resting.</p>")


def mascot_css() -> str:
    """Raw declarations; parent concats into the head wire."""
    try:
        return (".mascot{font-style:italic;opacity:.9}"
                ".mascot-resting{opacity:.7}")
    except Exception:  # noqa: BLE001 -- CSS emitter must never raise
        return ".mascot{font-style:italic}"


def status_section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Mascot companion "
            "<small>(feature)</small></h3>"
            "<p>Effort, noticed — "
            "<code>groundwork/mascot.py</code> puts a small companion "
            "on the Due page that reacts to attempts only (never "
            "accuracy, streaks, or scores).</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Mascot companion</h3>"
                "<p>Mascot help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "mascot-companion",
        "kind": "feature",
        "title": "Mascot companion",
        "blurb": ("A small companion that notices attempts — never "
                  "wins, never streaks."),
        "path": "/due",
        "anchor": SECTION_ANCHOR,
    }

"""Carbon note: reviews graded on this device, zero cloud calls (F-149).

Local-first is a climate claim only if it is quantified from live
data. This module renders one: the learner's own review count from
the local database plus the architectural zero -- no review path
dials out (the optional LLM helper has no live caller and defaults
to localhost). Measured-only: no grams-CO2 figure appears, because
no emission factor exists inside this app, and inventing one would
be demo-ware.

Caller: ``history.history_html`` joins ``section_html`` into the
lead block, so both the attempts branch and the empty branch show
it; unreadable DB renders "" (legacy bytes). Stdlib only (``html``)
plus a read-only ``db`` query; never raises.
"""
from __future__ import annotations

import html

from . import db as dbmod

BOX_ANCHOR = "carbon"
STATUS_ANCHOR = "status-b27-carbon"


def counts(db_path) -> dict:
    """Live {reviews, cards, days} from the local DB; zeros on error."""
    out = {"reviews": 0, "cards": 0, "days": 0}
    try:
        con = dbmod.connect(db_path)
        try:
            out["reviews"] = con.execute(
                "SELECT COUNT(*) FROM reviews").fetchone()[0] or 0
            out["cards"] = con.execute(
                "SELECT COUNT(*) FROM cards").fetchone()[0] or 0
            out["days"] = con.execute(
                "SELECT COUNT(DISTINCT substr(reviewed_at, 1, 10))"
                " FROM reviews").fetchone()[0] or 0
        finally:
            con.close()
    except Exception:  # noqa: BLE001 -- unreadable DB reads zero
        return {"reviews": 0, "cards": 0, "days": 0}
    return out


def note_for(counts) -> dict:
    """Quantified note: live review count plus the architectural zero."""
    try:
        n = counts.get("reviews", 0) if isinstance(counts, dict) else 0
        if not isinstance(n, int) or isinstance(n, bool) or n < 0:
            n = 0
    except Exception:  # noqa: BLE001 -- hostile input reads zero
        n = 0
    if n:
        line = (f"{n:,} reviews graded on this device - "
                "0 cloud GPU calls")
    else:
        line = ("No reviews yet - every review runs on this device, "
                "no cloud GPU.")
    return {"reviews": n, "cloud_calls": 0, "line": line}


def section_html(db_path) -> str:
    """History-page carbon note; "" when the DB is unreadable."""
    try:
        note = note_for(counts(db_path))
        return (
            f"<h2 id='{BOX_ANCHOR}'>Carbon note</h2>"
            f"<p>{html.escape(note['line'])}</p>"
            "<p><small>Grading and scheduling run from this server's "
            "local SQLite file; nothing on the review path dials out "
            "(the optional LLM helper has no live caller and defaults "
            "to localhost).</small></p>")
    except Exception:  # noqa: BLE001 -- caller keeps legacy bytes
        return ""


def status_html(db_path) -> str:
    """Anchored status subsection with the live review count."""
    try:
        note = note_for(counts(db_path))
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Carbon note "
            "<small>(feature)</small></h3>"
            "<p>History carries a carbon note: reviews graded on this "
            "device with 0 cloud GPU calls, quantified from your own "
            f"data (live count: {note['reviews']:,} reviews). "
            "No CO2 estimate is shown: there is no measured emission "
            "factor, only the counted reviews and the architectural "
            "zero. <code>groundwork/carbon.py</code>.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Carbon note</h3>"
                "<p>Carbon note temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "carbon-note",
        "kind": "feature",
        "title": "Carbon note",
        "blurb": ("History page shows your review count graded on this "
                  "device with zero cloud GPU calls - local-first, "
                  "quantified from your own data."),
        "path": "/reviews",
        "anchor": BOX_ANCHOR,
    }

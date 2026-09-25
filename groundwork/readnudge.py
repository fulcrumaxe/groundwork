"""Gentle still-with-us reading nudge (I-144).

Long reads time-box themselves: after ten idle minutes a hidden
banner asks "still with us?" with a Keep-reading button that
re-hides it. Pure progressive enhancement — the timer resets on
any activity, dismissal never blocks, and without JS only a hidden
banner ships (legacy bytes otherwise). should_nudge answers the
same question server-side for tests; hostile input reads as False.
Pure functions, stdlib html only; never raises.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b23-readnudge"

IDLE_SECS = 600


def should_nudge(last_active, now, idle: int = IDLE_SECS) -> bool:
    """True once ``idle`` seconds pass between two epoch timestamps."""
    try:
        gap = float(now) - float(last_active)
    except (TypeError, ValueError):
        return False
    try:
        limit = int(idle)
    except (TypeError, ValueError):
        return False
    if limit <= 0:
        return False
    return gap >= limit


def nudge_html(idle: int = IDLE_SECS) -> str:
    """Hidden banner plus activity-resetting timer script."""
    try:
        secs = int(idle)
    except (TypeError, ValueError):
        secs = IDLE_SECS
    if secs <= 0:
        secs = IDLE_SECS
    return (
        "<div class='readnudge' id='readnudge' hidden>"
        "<p>Still with us? <button type='button' data-keep>"
        "Keep reading</button></p></div>"
        "<script data-readnudge>"
        "(function(){try{"
        f"var idle={secs}*1000,box=document.getElementById('readnudge');"
        "if(!box)return;"
        "var t=null;"
        "function arm(){if(t)clearTimeout(t);"
        "t=setTimeout(function(){box.hidden=false;},idle);}"
        "box.querySelector('[data-keep]').addEventListener('click',"
        "function(){box.hidden=true;arm();});"
        "['click','keydown','scroll'].forEach(function(e){"
        "document.addEventListener(e,arm,{passive:true});});"
        "arm();}catch(e){}})</script>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Still-with-us nudge "
            "<small>(improvement)</small></h3>"
            "<p>Long reads check in — "
            "<code>groundwork/readnudge.py</code> raises a gentle banner "
            "after ten idle minutes (timer resets on any activity, "
            "dismissal never blocks); without JS the page renders "
            "exactly as before.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Still-with-us nudge</h3>"
                "<p>Reading-nudge help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "read-nudge",
        "kind": "improvement",
        "title": "Still-with-us nudge",
        "blurb": ("Ten idle minutes raise a gentle keep-reading nudge."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }

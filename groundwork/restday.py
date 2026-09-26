"""Rest-day affirmations (F-122): breaks framed as consolidation.

When the Due queue sits empty after a day (or more) away, the page
currently shows only stats and silence, which reads as failure. This
module adds one quiet sentence framing the break as memory
consolidation — no streaks, no shame, no pledge tracking (F-124 owns
the anti-streak pledge; I-70 donehero owns the session-complete
numbers, which this module never re-reports).

Pure functions, stdlib only (datetime, html), no I/O, no DB/schema
changes. The caller (``Handler.due_html`` empty-queue branch) derives
plain ints — ``idle_days_from_rows`` folds the already-fetched review
rows so no new query line is needed — and appends ``restday_html()``;
the ``""`` fallback keeps legacy rendering byte-identical when there
is nothing to affirm. Always renders; never raises.
"""
from __future__ import annotations

import html
from datetime import datetime, timezone

STATUS_ANCHOR = "status-b24-restday"

SECTION_ANCHOR = "rest-day"

REST_LINES = (
    "Rest day — your memory is consolidating what you practiced.",
    "A day away lets yesterday's cards settle in.",
    "Breaks are part of the loop: rest, return, recall.",
)


def _count(value) -> int:
    """Fail-closed non-negative int coercion; garbage -> 0.

    Queues arrive as lists too: a non-empty list counts its length,
    so a busy queue is never mistaken for an empty one.
    """
    try:
        if isinstance(value, bool):
            return 0
        if isinstance(value, (list, tuple)):
            return len(value)
        num = int(value)
        return num if num > 0 else 0
    except (TypeError, ValueError):
        return 0
    except Exception:  # noqa: BLE001 -- coercion must never raise
        return 0


def idle_days_from_rows(rows, now=None) -> int:
    """Whole idle days since the newest (grade, reviewed_at) row.

    ``rows`` is the already-fetched review list the Due page holds
    (grade, reviewed_at ISO strings); no query here, never raises.
    Empty or unreadable rows yield 0 (nothing to affirm — a brand-new
    learner gets the calm empty queue, not a rest line).
    """
    try:
        stamps = [r[1] for r in (rows or []) if len(r) > 1 and r[1]]
        if not stamps:
            return 0
        latest = max(str(s)[:10] for s in stamps)
        day = datetime.strptime(latest, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        ref = now or datetime.now(timezone.utc)
        delta = (ref.replace(hour=0, minute=0, second=0, microsecond=0) - day).days
        return delta if delta > 0 else 0
    except Exception:  # noqa: BLE001 -- never break the Due page
        return 0


def is_rest_day(due_count=0, idle_days=0) -> bool:
    """True only for an empty queue after >= 1 idle day."""
    try:
        return _count(due_count) == 0 and _count(idle_days) >= 1
    except Exception:  # noqa: BLE001 -- predicate must never raise
        return False


def affirmation_for(due_count=0, idle_days=0) -> str:
    """One consolidation line for a rest day; "" when nothing to affirm.

    Non-empty queues, zero idle days, and hostile input all yield ""
    so the caller renders nothing new (legacy fallback). Rest lines
    rotate deterministically by idle day count.
    """
    try:
        if not is_rest_day(due_count, idle_days):
            return ""
        return REST_LINES[(_count(idle_days) - 1) % len(REST_LINES)]
    except Exception:  # noqa: BLE001 -- picker must never raise
        return ""


def restday_html(due_count=0, idle_days=0) -> str:
    """Anchored rest-day banner; "" when there is nothing to affirm."""
    try:
        msg = affirmation_for(due_count, idle_days)
        if not msg:
            return ""
        return (
            f"<section id='{SECTION_ANCHOR}'>"
            f"<p>{html.escape(msg)}</p></section>"
        )
    except Exception:  # noqa: BLE001 -- banner must never raise
        return ""


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch24.py."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Rest-day affirmations "
            "<small>(feature)</small></h3>"
            "<p>An empty queue after a day away reads as consolidation, "
            "not failure — <code>groundwork/restday.py</code> appends one "
            "quiet sentence to the Due page's empty-queue branch "
            "(no streaks, no pledge, no re-reported stats).</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Rest-day affirmations</h3>"
                "<p>Rest help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "rest-day-affirmation",
        "kind": "feature",
        "title": "Rest-day affirmations",
        "blurb": ("An empty queue after time away says rest is "
                  "consolidation — not failure."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }

"""Sleep-aware scheduling (F-93): never schedule new cards late at night.

New cards reviewed during quiet hours get their next due pushed to
morning instead of landing in the middle of the night. Pure functions
over ISO due strings / datetimes — no I/O, no DB.

Caller paths (real learner paths, never a Status demo):
1. ``MCPServer.submit_review`` (groundwork/mcp.py): after
   ``sched.review_card`` computes the next due, a FIRST review
   (no prior grades) passes through ``adjust_due`` so a brand-new
   card's first interval never starts at 3am. Reviewed cards keep the
   scheduler's own due untouched.
2. ``MCPServer.tool_list_due_reviews`` (groundwork/mcp.py): the
   ordered due list passes through ``defer_night_new`` with the
   reviewed card ids, so new cards display a morning due while
   reviewed cards keep their stored due. Applied post-ordering, so
   queue order never moves.
Daytime dues pass through byte-identical (legacy no-data fallback).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

STATUS_ANCHOR = "status-b21-sleepsched"

QUIET_START = 22
QUIET_END = 7
WAKE_HOUR = 7


def _clamp_hour(value, default: int) -> int:
    try:
        h = int(value)
    except (TypeError, ValueError):
        return default
    return max(0, min(23, h))


def _as_dt(value) -> datetime | None:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        try:
            dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return None
    else:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def in_quiet_hours(now=None, hour=None, quiet_start: int = QUIET_START,
                   quiet_end: int = QUIET_END) -> bool:
    """True when the given time falls inside the quiet window.

    ``hour`` (0-23) wins when given; otherwise ``now`` (datetime or ISO
    string, defaults to current UTC). Unparseable input returns False
    (legacy no-data fallback: never defer when we cannot tell time).
    A start == end window means an empty window (never quiet).
    """
    qs = _clamp_hour(quiet_start, QUIET_START)
    qe = _clamp_hour(quiet_end, QUIET_END)
    if qs == qe:
        return False
    if hour is not None:
        try:
            h = int(hour)
        except (TypeError, ValueError):
            return False
        if not 0 <= h <= 23:
            return False
    else:
        dt = _as_dt(now) if now is not None else datetime.now(timezone.utc)
        if dt is None:
            return False
        h = dt.hour
    if qs < qe:
        return qs <= h < qe
    return h >= qs or h < qe


def next_morning(now=None, wake_hour: int = WAKE_HOUR) -> datetime:
    """First wake-up time at/after ``now`` (UTC wall clock)."""
    wake = _clamp_hour(wake_hour, WAKE_HOUR)
    dt = _as_dt(now) if now is not None else datetime.now(timezone.utc)
    if dt is None:
        dt = datetime.now(timezone.utc)
    morning = dt.replace(hour=wake, minute=0, second=0, microsecond=0)
    if morning <= dt:
        morning += timedelta(days=1)
    return morning


def adjust_due(due, now=None, quiet_start: int = QUIET_START,
               quiet_end: int = QUIET_END,
               wake_hour: int = WAKE_HOUR) -> str | object:
    """Push a night-time due to morning; daytime dues pass through.

    Returns the ISO string of the (possibly deferred) due. Non-string /
    unparseable input is returned unchanged (legacy no-data fallback).
    Only dues landing inside the quiet window move, and only forward to
    the next wake-up at/after the due itself.
    """
    if not isinstance(due, str):
        return due
    dt = _as_dt(due)
    if dt is None:
        return due
    _ = now
    if not in_quiet_hours(hour=dt.hour, quiet_start=quiet_start,
                          quiet_end=quiet_end):
        return due
    return _iso(next_morning(dt, wake_hour=wake_hour))


def is_new_card(card: dict) -> bool:
    """True when a card dict looks never-reviewed (a new card).

    Non-dict input returns False (never treat unknown shapes as new).
    A card counts as new when it carries no review evidence: no truthy
    ``reviews``/``review_count``/``grade``/``last_review``/``reviewed_at``
    field and no ``grades`` history.
    """
    if not isinstance(card, dict):
        return False
    for key in ("reviews", "review_count", "n", "grade", "last_review",
                "reviewed_at", "grades"):
        val = card.get(key)
        if isinstance(val, (list, tuple)) and val:
            return False
        if isinstance(val, (int, float)) and val:
            return False
        if isinstance(val, str) and val.strip():
            return False
    return True


def defer_night_new(cards: list, now=None,
                    quiet_start: int = QUIET_START,
                    quiet_end: int = QUIET_END,
                    wake_hour: int = WAKE_HOUR,
                    reviewed_ids=None) -> list:
    """Defer new cards due in quiet hours to morning (Due-queue hook).

    Returns a new list of shallow-copied dicts; non-dict entries pass
    through untouched. Order is preserved. When ``reviewed_ids`` (a set
    of card ids with review history, e.g. from the reviews table) is
    given, newness comes from membership; otherwise the ``is_new_card``
    shape heuristic applies. Reviewed cards keep their due even at
    night — only fresh cards move, so late-night study never seeds a
    3am review the next cycle.
    """
    try:
        known = set(reviewed_ids) if reviewed_ids is not None else None
    except TypeError:
        known = None
    out: list = []
    for card in cards or []:
        if not isinstance(card, dict):
            out.append(card)
            continue
        if known is not None:
            fresh = card.get("id") not in known
        else:
            fresh = is_new_card(card)
        if not fresh or "due" not in card:
            out.append(dict(card))
            continue
        _ = now
        copy = dict(card)
        copy["due"] = adjust_due(card.get("due"), now=now,
                                 quiet_start=quiet_start,
                                 quiet_end=quiet_end, wake_hour=wake_hour)
        out.append(copy)
    return out


def morning_after_late_review(now=None,
                              wake_hour: int = WAKE_HOUR) -> str:
    """Due string for a card reviewed late at night: next wake-up.

    Thin wrapper over ``next_morning`` for ``sched.review_card`` call
    sites that schedule brand-new cards. Daytime callers should keep
    the scheduler's own due and skip this helper.
    """
    return _iso(next_morning(now, wake_hour=wake_hour))


def section_html() -> str:
    """Anchored status subsection; joined by the batch21 home module."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Sleep-aware scheduling "
            "<small>(feature)</small></h3>"
            "<p>New cards reviewed late at night get their next due "
            "pushed to morning instead of landing at 3am "
            "(<code>groundwork/sleepsched.py</code> on the review path "
            "and the due listing); daytime dues pass through unchanged. "
            "Reviewed cards keep the scheduler's own due.</p>")
    except Exception:  # noqa: BLE001 -- status must never raise
        return (f"<h3 id='{STATUS_ANCHOR}'>Sleep-aware scheduling</h3>"
                "<p>Sleep help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "sleep-aware-scheduling",
        "kind": "feature",
        "title": "Sleep-aware scheduling",
        "blurb": ("New cards reviewed late at night wake up with a "
                  "morning due instead of a 3am one."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }

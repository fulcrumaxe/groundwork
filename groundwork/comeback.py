"""Comeback path (F-123): gentle recap after 30 idle days, no shame.

A learner who returns after a month away meets a wall of overdue cards
and quits again. This module renders one welcome-back banner atop the
Due queue: how long they were away, the last few concepts they touched,
and a single low-pressure next step. No streaks, no guilt, no backlog
totals — the queue itself already says what is due.

Pure functions, stdlib only (``html``, ``datetime``). No I/O, no DB /
schema changes. The caller (``Handler.due_html``) passes its
already-fetched review rows; the banner derives everything from them.

Behavioral effect: 30+ idle days shows the recap banner; anything less
(or no history at all) yields ``""`` so fresh and active libraries
render the Due queue byte-identical. Never raises.

Distinct from its neighbours: ``resume.py`` rebuilds one interrupted
module-day session (fires even for yesterday); ``reteach.py`` re-teaches
each month-old *concept* from its first attempt; F-122 rest-day
affirmation celebrates a single rest day. This module clocks the
*learner* from their last review of anything.
"""
from __future__ import annotations

import html
from datetime import date

STATUS_ANCHOR = "status-b24-comeback"
BOX_ANCHOR = "comeback"

#: Idle days since the last review that counts as "away".
IDLE_DAYS = 30

#: Concept names recalled in the banner.
RECAP_N = 3


def _coerce_str(value) -> str:
    """Best-effort str; never raises."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return str(value)
    except Exception:
        return ""


def _parse_day(value) -> date | None:
    """Calendar day of an ISO timestamp-ish value, else None."""
    try:
        text = _coerce_str(value).strip()
        if len(text) < 10:
            return None
        return date.fromisoformat(text[:10])
    except (ValueError, TypeError):
        return None


def idle_days(last_seen, now="") -> int | None:
    """Full days from ``last_seen`` to ``now`` (today when blank).

    Returns None when ``last_seen`` is missing or unparseable, or when
    ``now`` is unparseable; a future ``last_seen`` clamps to 0.
    Never raises.
    """
    try:
        start = _parse_day(last_seen)
        if start is None:
            return None
        if isinstance(now, str) and now.strip():
            end = _parse_day(now)
            if end is None:
                return None
        elif now is None or (isinstance(now, str) and not now.strip()):
            end = date.today()
        elif isinstance(now, date):
            end = now
        else:
            return None
        return max(0, (end - start).days)
    except Exception:
        return None


def is_comeback(last_seen, now="") -> bool:
    """True iff the learner was away IDLE_DAYS or more; else False."""
    try:
        idle = idle_days(last_seen, now)
        return idle is not None and idle >= IDLE_DAYS
    except Exception:
        return False


def last_seen_from(rows) -> str:
    """Newest ``reviewed_at`` across review rows, or ``""``.

    Rows are mappings (or tuples) carrying a timestamp; anything
    missing or malformed is skipped. Never raises.
    """
    try:
        best = ""
        for row in rows or []:
            try:
                if isinstance(row, dict):
                    when = row.get("reviewed_at", row.get("when", ""))
                else:
                    when = row[0]
            except (TypeError, IndexError, KeyError):
                continue
            stamp = _coerce_str(when).strip()
            if _parse_day(stamp) is not None and stamp > best:
                best = stamp
        return best
    except Exception:
        return ""


def recap_items(rows, limit=RECAP_N) -> list:
    """Most-recent distinct ``{name, when}`` concepts, newest first.

    ``rows`` are mappings (or tuples) of (name, reviewed_at); the first
    (newest) occurrence per name wins. ``limit`` caps the list; bad
    limits fall back to RECAP_N. Never raises.
    """
    try:
        n = int(limit)
        if n <= 0:
            return []
    except (TypeError, ValueError):
        n = RECAP_N
    try:
        seen: dict[str, str] = {}
        order: list[str] = []
        for row in rows or []:
            try:
                if isinstance(row, dict):
                    name = row.get("name", row.get("concept", ""))
                    when = row.get("reviewed_at", row.get("when", ""))
                else:
                    name, when = row[0], row[1]
            except (TypeError, IndexError, KeyError):
                continue
            name = _coerce_str(name).strip()
            stamp = _coerce_str(when).strip()
            if not name or _parse_day(stamp) is None:
                continue
            if name not in seen:
                seen[name] = stamp
                order.append(name)
            elif stamp > seen[name]:
                seen[name] = stamp
        order.sort(key=lambda k: seen[k], reverse=True)
        return [{"name": k, "when": seen[k]} for k in order[:n]]
    except Exception:
        return []


def comeback_box_html(last_seen=None, now="", items=None,
                      rows=None) -> str:
    """Welcome-back banner for the Due page, or ``""`` when not away.

    Pass review rows as ``rows=`` (mappings or (name, reviewed_at)
    tuples, newest stamp wins) or the learner's newest ``reviewed_at``
    as ``last_seen``. Under IDLE_DAYS the banner stays hidden so
    active queues render byte-identical. At 30+ days it recaps: days
    away, up to RECAP_N recent concepts, and a one-card next step —
    kindly worded, never shaming. Never raises.
    """
    try:
        seen = _coerce_str(last_seen).strip()
        if not seen and rows is not None:
            seen = last_seen_from(rows)
        idle = idle_days(seen, now)
        if idle is None or idle < IDLE_DAYS:
            return ""
        picks = list(items or [])
        if not picks and rows is not None:
            picks = recap_items(rows)
        lis = "".join(
            f"<li>{html.escape(_coerce_str(p.get('name', '')) if isinstance(p, dict) else _coerce_str(p))}</li>"
            for p in picks[:RECAP_N]
            if (p.get("name", "") if isinstance(p, dict) else p))
        trails = f"<ul>{lis}</ul>" if lis else ""
        day_word = "day" if idle == 1 else "days"
        first = "the basics"
        if picks:
            head = picks[0]
            first = head.get("name", "") if isinstance(head, dict) else _coerce_str(head)
            first = first or "the basics"
        return (
            f"<section id='{BOX_ANCHOR}'>"
            f"<h2>Welcome back — gently</h2>"
            f"<p>You were away {idle} {day_word}. Nothing expired and "
            f"no streak was lost; your past work is still yours.</p>"
            f"{trails}"
            f"<p>Last time you were here: "
            f"{html.escape(first)}. "
            f"One card is plenty today — "
            f"<a href='/due?mode=one'>just one card</a> restarts the loop.</p>"
            f"</section>"
        )
    except Exception:
        return ""


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "comeback-30d", "kind": "feature",
            "title": "Comeback after time away",
            "blurb": "Away 30 days? A gentle recap greets you — no shame, one card restarts the loop.",
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Status-page subsection: visible home for this item."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Comeback after time away "
        "<small>(feature)</small></h3>"
        "<p>Thirty idle days show one welcome-back recap on the Due queue "
        "(days away, recent concepts, a one-card next step) — kindly "
        "worded, no streaks, no backlog totals. Active libraries see "
        "nothing at all. <code>groundwork/comeback.py</code> provides "
        "<code>is_comeback()</code> (idle-days gate), "
        "<code>recap_items()</code> (newest distinct concepts) and "
        "<code>comeback_box_html()</code> (Due banner, ``\"\"`` when the "
        "learner is not away).</p>"
    )

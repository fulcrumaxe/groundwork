"""Daily review cap with load-balanced overflow (I-205).

Caps the Due queue at N cards per day (``?cap=N``) and spreads the
overflow across the coming days at the same daily rate, so a large
backlog shrinks steadily instead of crushing today or hiding. Pure
functions, stdlib only, no I/O, no DB/schema changes.

Planning rule: queue order is preserved (slice only — the dial,
interleave, kata, difficulty-vote and remediation ordering upstream
survives; no re-sort here). Today's share is the first N cards; the
rest chunks into consecutive dated buckets of N ("load balance":
every coming day carries at most one full day's share). Absent or
invalid caps return the legacy queue untouched (Batch-17 ``?dial=``
precedent); nothing here ever raises.

Boundary: planning + overflow banner live here. Grading, scheduling
and queue rendering stay with cards.py/queue.py; the 5-minute fill
stays with minisession.py.
"""
from __future__ import annotations

import html
from datetime import date, datetime, timedelta, timezone

STATUS_ANCHOR = "status-b29-dailycap"

MIN_CAP = 1
MAX_CAP = 50

_PRESETS = (10, 20)


def parse_cap(value, default=None):
    """Cap N from a raw ``?cap=`` value; fail closed to ``default``.

    None, blank, bools, non-numerics and N < 1 all mean "no cap";
    N > MAX_CAP clamps to MAX_CAP. Never raises.
    """
    if value is None or isinstance(value, bool):
        return default
    try:
        text = value.strip() if isinstance(value, str) else value
        if isinstance(text, str) and not text:
            return default
        n = int(text)
    except (TypeError, ValueError):
        return default
    except Exception:  # noqa: BLE001 -- coercion must never raise
        return default
    if n < MIN_CAP:
        return default
    return min(n, MAX_CAP)


def _start_date(start):
    """First overflow date; garbage fails closed to tomorrow (UTC)."""
    tomorrow = datetime.now(timezone.utc).date() + timedelta(days=1)
    try:
        if start is None:
            return tomorrow
        if isinstance(start, datetime):
            return start.date()
        if isinstance(start, date):
            return start
        if isinstance(start, str) and start.strip():
            return date.fromisoformat(start.strip()[:10])
        return tomorrow
    except (TypeError, ValueError):
        return tomorrow
    except Exception:  # noqa: BLE001 -- dating must never raise
        return tomorrow


def split_due(due, cap, start=None, per_day=None):
    """Split the due queue into ``(today, plan)`` at cap N.

    ``today`` is the first N cards in queue order; ``plan`` is the
    overflow as consecutive dated buckets
    (``[{"date": iso, "cards": [...]}, ...]``) of ``per_day`` cards
    (default N) starting at ``start`` (default tomorrow, UTC).
    ``cap`` takes the raw ``?cap=`` value or an int. A missing or
    invalid cap returns ``(due, [])`` — the legacy queue untouched.
    Non-dict entries are skipped; the input is never mutated.
    Never raises.
    """
    try:
        n = parse_cap(cap)
        if n is None:
            return due, []
        rate = parse_cap(per_day, n)
        rows = [c for c in (due or []) if isinstance(c, dict)]
        today = rows[:n]
        rest = rows[n:]
        if not rest:
            return today, []
        day0 = _start_date(start)
        plan = []
        for i in range(0, len(rest), rate):
            plan.append({
                "date": (day0 + timedelta(days=len(plan))).isoformat(),
                "cards": rest[i:i + rate],
            })
        return today, plan
    except Exception:  # noqa: BLE001 -- the cap must never break Due
        return due, []


def apply_cap(due, raw, start=None, per_day=None):
    """Due-path entry: raw ``?cap=`` value in, ``(today, plan)`` out.

    Thin wrapper over :func:`split_due` naming the caller contract
    for ``Handler.due_html``. Never raises.
    """
    return split_due(due, raw, start=start, per_day=per_day)


def cap_box(today, plan, cap, mode="") -> str:
    """Due-page banner: capped count plus the dated overflow plan.

    ``""`` when no cap is active, so the legacy page stays
    byte-identical. With a cap and no overflow, a one-line
    fits-today note; with overflow, the counts plus one row per
    coming day. Preset links carry the session mode. Never raises.
    """
    try:
        n = parse_cap(cap)
        if n is None:
            return ""
        try:
            shown = len(today or [])
        except TypeError:
            shown = 0
        buckets = [b for b in (plan or []) if isinstance(b, dict)]
        overflow = sum(len(b.get("cards") or []) for b in buckets)
        total = shown + overflow
        qs = f"mode={mode}&" if mode in ("one", "cold") else ""
        links = " · ".join(
            f"<a href='/due?{qs}cap={v}'>{v}/day</a>" for v in _PRESETS)
        full = "/due?" + qs.rstrip("&") if qs else "/due"
        tail = f"<small>{links} · <a href='{full}'>full queue</a></small>"
        if not buckets:
            return (
                f"<p id='dailycap'><small>Daily cap {n}: "
                f"all {total} due fit today.</small><br>{tail}</p>"
            )
        lis = "".join(
            f"<li>{html.escape(str(b.get('date', '')))}: "
            f"{len(b.get('cards') or [])} cards</li>"
            for b in buckets)
        days = len(buckets)
        noun = "day" if days == 1 else "days"
        return (
            f"<p id='dailycap'><small>Daily cap {n}: showing {shown} "
            f"of {total} due - {overflow} spread over {days} coming "
            f"{noun}.</small><br>{tail}</p>"
            f"<ol id='dailycap-plan'>{lis}</ol>"
        )
    except Exception:  # noqa: BLE001 -- banner never raises
        return ""


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        "<h3 id='status-b29-dailycap'>Daily review cap "
        "<small>(improvement)</small></h3>"
        "<p>Cap Due at N cards a day (<code>?cap=N</code>) — today's "
        "share stays most-overdue-first and the overflow spreads "
        "across the coming mornings at the same daily rate. "
        "<code>groundwork/dailycap.py</code> provides "
        "<code>parse_cap()</code> (param parsing, fails closed to no "
        "cap), <code>split_due()</code> (order-preserving slice into "
        "today plus dated overflow buckets) and "
        "<code>cap_box()</code> (Due banner with the overflow plan).</p>"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "daily-cap",
        "kind": "improvement",
        "title": "Daily review cap",
        "blurb": "Cap Due at N cards a day — overflow spreads across "
                 "coming mornings instead of crushing today.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }

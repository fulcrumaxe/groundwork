"""Spacing optimizer (F-62): per-learner intervals from recall data.

The scheduler's intervals are one-size-fits-all; a learner who never
forgets retry-cards and always forgets cache-cards gets the same gaps
for both. This module owns the per-concept fit: over a grade history
it grows the interval on passes (×GROWTH per consecutive pass, capped
at MAX_DAYS) and collapses to BASE_DAYS on any fail, so strong
concepts stretch out and fragile ones return tomorrow. Grades arrive
newest-last; anything unparseable is ignored (never counted as a
pass). Db-free library — ``sched.py`` is untouched; pure functions,
stdlib only, no I/O, no DB changes.
"""
from __future__ import annotations

STATUS_ANCHOR = "status-b13-spacingopt"

BASE_DAYS = 1.0
GROWTH = 2.2
MAX_DAYS = 60.0
PASS_GRADE = 4


def clean_grades(grades) -> list[int]:
    """Usable grades, oldest-first; unparseable entries are dropped."""
    out = []
    try:
        for g in grades or []:
            try:
                out.append(int(g))
            except Exception:  # noqa: BLE001 -- bad grade, skip it
                continue
        return out
    except Exception:  # noqa: BLE001 -- optimizer must never raise
        return []


def streak(grades) -> int:
    """Consecutive trailing passes (grade >= 4); garbage → 0.

    The streak is the optimizer's memory: sched counts it to stretch
    the gap. Never raises.
    """
    try:
        n = 0
        for g in reversed(clean_grades(grades)):
            if g >= PASS_GRADE:
                n += 1
            else:
                break
        return n
    except Exception:  # noqa: BLE001 -- optimizer must never raise
        return 0


def apply_streak(base_days: float, streak_count: int) -> float:
    """Base gap stretched by a pass streak, capped at MAX_DAYS.

    Shared with sched so the forecast and the scheduler agree.
    Garbage inputs fail closed to BASE_DAYS; never raises.
    """
    try:
        try:
            start = float(base_days)
        except Exception:  # noqa: BLE001 -- base must never raise
            start = BASE_DAYS
        if start != start or start <= 0:  # NaN / non-positive
            start = BASE_DAYS
        start = min(MAX_DAYS, start)
        try:
            n = max(0, int(streak_count))
        except Exception:  # noqa: BLE001 -- streak must never raise
            n = 0
        return min(MAX_DAYS, start * (GROWTH ** n))
    except Exception:  # noqa: BLE001 -- optimizer must never raise
        return BASE_DAYS


def next_interval(grades, base: float = BASE_DAYS) -> float:
    """Days until the next review after this history.

    Counts consecutive trailing passes (grade >= 4): each multiplies
    the base by GROWTH, capped at MAX_DAYS. Any trailing fail (or no
    history at all) means BASE. ``base`` clamps to (0, MAX_DAYS];
    never raises.
    """
    try:
        return apply_streak(base, streak(grades))
    except Exception:  # noqa: BLE001 -- optimizer must never raise
        return BASE_DAYS


def describe(grades) -> str:
    """One-line reading of the fit: streak length and current gap."""
    try:
        hist = clean_grades(grades)
        run = streak(hist)
        gap = next_interval(hist)
        if not hist:
            return f"no recalls yet — next gap {gap:.1f}d"
        if run == len(hist):
            return (f"{run} straight passes — "
                    f"stretched to {gap:.1f}d")
        if run:
            return f"last fail broken by {run} passes — gap {gap:.1f}d"
        return f"still fragile — back tomorrow ({gap:.1f}d)"
    except Exception:  # noqa: BLE001 -- describe must never raise
        return "no recalls yet"


def section_html() -> str:
    """Status-page subsection: visible home for this item."""
    strong = next_interval([5, 4, 5, 5])
    fragile = next_interval([5, 5, 2])
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Spacing optimizer <small>(feature)</small></h3>"
        "<p>Review gaps now fit the learner, not the average: "
        "<code>groundwork/spacingopt.py</code> provides "
        "<code>next_interval()</code> (consecutive passes stretch the "
        "gap ×2.2 to a 60-day ceiling; any fail collapses to tomorrow) "
        "and <code>describe()</code>. Since Batch 14 the scheduler "
        "calls it for real: <code>sched.review_card(grades=)</code> "
        "stretches the due gap by the trailing pass streak. Same history shape, two "
        f"learners: four straight passes → {strong:.1f}d; a recent fail "
        f"→ {fragile:.1f}d.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "spacing-optimizer",
        "kind": "feature",
        "title": "Spacing optimizer",
        "blurb": "Per-concept gaps from your own recalls — strong ideas stretch out, fragile ones return tomorrow.",
        "path": "/status",
        "anchor": "status-b13-spacingopt",
    }

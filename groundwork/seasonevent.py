"""Seasonal events: Hacktober-style own-5 goal, local and streak-free (F-131).

One fixed window (October, "Owntober"): own 5 concepts whose owned-date
falls inside it. Computed from existing tables via milestones — no new
storage, no network, no streaks. Caller: history.history_html parts list.
Outside the window the section omits itself ("" keeps legacy bytes).
"""
from __future__ import annotations

import html
from datetime import date

STATUS_ANCHOR = "status-b25-seasonevent"

GOAL = 5
EVENT_MONTH = 10
EVENT_TITLE = "Owntober"


def _today(today=None) -> date:
    if today is None:
        return date.today()
    if isinstance(today, date):
        return today
    try:
        return date.fromisoformat(str(today)[:10])
    except ValueError:
        return date.today()


def current_event(today=None) -> dict | None:
    """Active event window or None; `today` injectable (date or ISO str)."""
    try:
        d = _today(today)
        if d.month != EVENT_MONTH:
            return None
        y = d.year
        return {"id": "owntober", "title": EVENT_TITLE,
                "start": f"{y}-10-01", "end": f"{y}-10-31", "goal": GOAL}
    except Exception:  # noqa: BLE001 -- resolution never raises
        return None


def progress(db_path: str, today=None) -> dict:
    """{owned, goal, done} counting owned-dates inside the window; 0/None-safe."""
    try:
        ev = current_event(today)
        if ev is None:
            return {"owned": 0, "goal": GOAL, "done": False, "event": None}
        from . import milestones as milesmod
        owned = milesmod.owned_dates(db_path)
        n = sum(1 for w in owned.values()
                if ev["start"] <= str(w or "")[:10] <= ev["end"])
        return {"owned": n, "goal": GOAL, "done": n >= GOAL, "event": ev}
    except Exception:  # noqa: BLE001 -- progress never raises
        return {"owned": 0, "goal": GOAL, "done": False, "event": None}


def section_html(db_path: str, today=None) -> str:
    """History event section; "" when no event is active (legacy bytes)."""
    try:
        p = progress(db_path, today)
        ev = p["event"]
        if ev is None:
            return ""
        n, g = p["owned"], p["goal"]
        line = (f"Goal met — {n} of {g} owned this October. Nicely done."
                if p["done"] else
                f"{n} of {g} owned this October — a gentle seasonal goal, "
                "no streak attached.")
        return (f"<h2 id='seasonal-event'>{html.escape(ev['title'])} — "
                f"own {g} concepts</h2><p>{line}</p>")
    except Exception:  # noqa: BLE001 -- history never breaks
        return ""


def status_section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch25.py."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Seasonal events "
            "<small>(feature)</small></h3>"
            "<p>Each October brings Owntober — "
            "<code>groundwork/seasonevent.py</code> counts concepts owned "
            "inside the month toward a goal of 5 (read from the existing "
            "tables, no new storage, no streaks) on the History page.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Seasonal events</h3>"
                "<p>Seasonal help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour registry entry for seasonal events."""
    return {"id": "seasonal-event", "kind": "feature",
            "title": "Seasonal events",
            "blurb": "Each October: own 5 concepts. Gentle goal, no streak.",
            "path": "/status", "anchor": STATUS_ANCHOR}

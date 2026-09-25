"""Study-with-a-friend side-by-side lesson view (I-143).

One lesson rendered in two labelled panes so two learners on the
same machine can read together, each with their own position
markers. Deliberately local only: friends and markers arrive as
plain data (query params / localStorage on the client), there is no
live sync, no transport, no second cursor protocol — a literal
live-sync view would need all of that plus human subjects, so the
scoped twin-pane view is the shippable half. Solo visits (fewer
than two distinct names) render byte-identical: buddy_html returns
"". Pure functions, stdlib html only; never raises.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b23-buddyview"

MAX_MARKERS = 8


def clean_name(value) -> str:
    """Display name or "" for blank/hostile input."""
    try:
        if not isinstance(value, str):
            return ""
        return value.strip()[:40]
    except Exception:  # noqa: BLE001 -- names must never raise
        return ""


def buddy_markers(marks) -> list:
    """Clamped [(name, pct)] position markers; hostile input gives []."""
    try:
        if not isinstance(marks, (list, tuple)):
            return []
        out = []
        for m in marks[:MAX_MARKERS]:
            if not isinstance(m, (list, tuple)) or len(m) != 2:
                continue
            name = clean_name(m[0])
            if not name:
                continue
            try:
                pct = min(100, max(0, int(m[1])))
            except (TypeError, ValueError):
                continue
            out.append((name, pct))
        return out
    except Exception:  # noqa: BLE001 -- markers must never raise
        return []


def pane_html(lesson_title: str, who: str) -> str:
    """One labelled pane for one friend."""
    try:
        title = html.escape(str(lesson_title or "Lesson"))
        name = html.escape(clean_name(who) or "Friend")
        return (f"<div class='buddy-pane'><h4>{title} "
                f"<small>({name}'s pane)</small></h4></div>")
    except Exception:  # noqa: BLE001 -- panes must never raise
        return ""


def buddy_html(lesson_title: str, friends, marks=None) -> str:
    """Twin-pane view; "" unless two or more distinct friends."""
    try:
        names = []
        for f in (friends or []):
            n = clean_name(f)
            if n and n not in names:
                names.append(n)
        if len(names) < 2:
            return ""
        panes = "".join(pane_html(lesson_title, n) for n in names[:2])
        dots = "".join(
            f"<li>{html.escape(n)} — {p}%</li>"
            for n, p in buddy_markers(marks))
        markers = f"<ul class='buddy-marks'>{dots}</ul>" if dots else ""
        return (f"<div class='buddy-view'>{panes}{markers}</div>")
    except Exception:  # noqa: BLE001 -- view must never raise
        return ""


def entry_html(base: str) -> str:
    """Friend-name form (GET ?buddy=); always rendered on module pages."""
    try:
        action = html.escape(str(base or "/modules"))
        return (
            f"<form class='buddy-entry' method='get' action='{action}'>"
            "<label>Study with a friend "
            "<input name='buddy' maxlength='40' placeholder='You'>"
            "<input name='buddy' maxlength='40' placeholder='Friend'>"
            "</label> <button type='submit'>Study together</button></form>")
    except Exception:  # noqa: BLE001 -- entry must never raise
        return ""


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Study with a friend "
            "<small>(improvement)</small></h3>"
            "<p>One lesson, two panes — "
            "<code>groundwork/buddyview.py</code> renders a side-by-side "
            "view for two named friends with per-friend position markers, "
            "all local (no sync, no network); solo visits render exactly "
            "as before.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Study with a friend</h3>"
                "<p>Buddy view help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "buddy-view",
        "kind": "improvement",
        "title": "Study with a friend",
        "blurb": ("Same lesson side by side — two panes, local only."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }

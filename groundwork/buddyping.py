"""Study-buddy pings without leaderboards (F-125).

Social accountability as local nudge content: when two named friends
open one module together, the page shows a one-line ping addressed to
the pair — a welcome before anything is owned, encouragement midway,
a joint celebration at full ownership. Deliberately no ranking, no
cross-learner comparison, no network and no messaging: the ping is a
string the learner path renders next to the buddy view. Names are
cleaned with buddyview.clean_name, so hostile input is handled in
exactly one place, and solo visits (fewer than two distinct names)
render byte-identical: ping_html returns "". Pure functions, stdlib
html only; never raises. The caller is ``Handler.module_html`` after
the owned-progress bar.
"""
from __future__ import annotations

import html

from . import buddyview as buddyviewmod

STATUS_ANCHOR = "status-b24-buddyping"

WELCOME = "welcome"
CHEER = "cheer"
CELEBRATE = "celebrate"


def pair_names(friends) -> list:
    """First two distinct friend names via the shared buddy cleaner."""
    try:
        if not isinstance(friends, (list, tuple)):
            return []
        names = []
        for f in friends:
            n = buddyviewmod.clean_name(f)
            if n and n not in names:
                names.append(n)
            if len(names) >= 2:
                break
        return names
    except Exception:  # noqa: BLE001 -- pings must never raise
        return []


def _count(value) -> int | None:
    """Non-negative int or None for hostile input."""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    return max(0, n)


def pick_ping(owned_n, total_n) -> str:
    """Which nudge fits; hostile/unknown counts read as a fresh start."""
    try:
        owned = _count(owned_n)
        total = _count(total_n)
        if owned is None or total is None:
            return WELCOME
        if owned <= 0:
            return WELCOME
        if total > 0 and owned >= total:
            return CELEBRATE
        return CHEER
    except Exception:  # noqa: BLE001 -- picking must never raise
        return WELCOME


def ping_text(kind, friends, owned_n=0, total_n=0) -> str:
    """Plain-text nudge for the pair; "" when no pair or bad kind."""
    try:
        names = pair_names(friends)
        if len(names) < 2:
            return ""
        a, b = names[0], names[1]
        owned = _count(owned_n)
        total = _count(total_n)
        if kind == CELEBRATE and total:
            return (f"{a} and {b}: all {total} concepts owned — "
                    "nice work, both of you.")
        if kind == CHEER:
            if total:
                return (f"{a} and {b}: {owned or 0} of {total} owned — "
                        "keep going, gently.")
            return (f"{a} and {b}: {owned or 0} owned so far — "
                    "keep going, gently.")
        if kind == WELCOME:
            return (f"{a} and {b}: own your first concept together — "
                    "one card each, then compare notes.")
        return ""
    except Exception:  # noqa: BLE001 -- text must never raise
        return ""


def ping_html(friends, owned_n=0, total_n=0) -> str:
    """Ping banner; "" unless two or more distinct friends."""
    try:
        text = ping_text(pick_ping(owned_n, total_n), friends,
                         owned_n, total_n)
        if not text:
            return ""
        return f"<p class='buddy-ping'>{html.escape(text)}</p>"
    except Exception:  # noqa: BLE001 -- banner must never raise
        return ""


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch24.py."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Study-buddy pings "
            "<small>(feature)</small></h3>"
            "<p>Accountability without leaderboards — "
            "<code>groundwork/buddyping.py</code> renders one local nudge "
            "for a named study pair (welcome, encouragement, celebration), "
            "reusing the buddy view's name cleaner; solo visits render "
            "exactly as before.</p>")
    except Exception:  # noqa: BLE001 -- status must never render
        return (f"<h3 id='{STATUS_ANCHOR}'>Study-buddy pings</h3>"
                "<p>Buddy-ping help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "buddy-ping",
        "kind": "feature",
        "title": "Study-buddy pings",
        "blurb": ("A gentle nudge for your study pair — no leaderboards."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }

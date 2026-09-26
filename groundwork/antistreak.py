"""Anti-streak pledge (F-124): why we never count streaks.

A standing principle statement for the History page, rendered right
after the month review. Pure static copy: no DB read, no I/O, stdlib
only — so it renders identically with zero reviews and the tour
anchor never moves.

Distinct from F-122 rest-day affirmation (a separate item): the
affirmation is a contextual rest-day message for the Due queue
("rest is fine today"); this pledge is the standing principle for
History ("chains are never counted, ever"). Separate anchors, no
shared copy. The caller is ``history.history_html``.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b24-antistreak"

ANCHOR = "antistreak"

PLEDGE = "We never count streaks."

REASONS: tuple = (
    ("Missed days cost nothing.",
     "A gap leaves no debt and breaks nothing. The queue keeps no "
     "grudges — one card today restarts the loop."),
    ("Memory runs on intervals, not chains.",
     "Reviews return when forgetting is likely, spaced by how well "
     "each card holds — an unbroken chain would schedule worse, not "
     "better."),
    ("Proof counts, presence does not.",
     "Owned concepts, accuracy, and practice days say what you know. "
     "Showing up daily without learning proves nothing."),
)


def reasons() -> tuple:
    """The three (title, body) pledge reasons."""
    return REASONS


def pledge() -> str:
    """The one-line pledge."""
    return PLEDGE


def pledge_html() -> str:
    """The pledge reasons as an escaped list."""
    items = "".join(
        f"<li><b>{html.escape(t)}</b> {html.escape(b)}</li>"
        for t, b in REASONS)
    return f"<p>{html.escape(PLEDGE)}</p><ul>{items}</ul>"


def history_section(db_path=None) -> str:
    """History-page section: the pledge. db_path accepted, ignored."""
    _ = db_path
    return f"<h2 id='{ANCHOR}'>Anti-streak pledge</h2>{pledge_html()}"


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch24.py."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Anti-streak pledge "
        "<small>(feature)</small></h3>"
        "<p>Why streaks are never counted — missed days cost nothing, "
        "memory runs on intervals. "
        "<code>groundwork/antistreak.py</code> renders the standing "
        "pledge on the History page after the month review.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "antistreak-pledge",
        "kind": "feature",
        "title": "Anti-streak pledge",
        "blurb": "Why Groundwork never counts streaks — missed days cost nothing.",
        "path": "/reviews",
        "anchor": ANCHOR,
    }

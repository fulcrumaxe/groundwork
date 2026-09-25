"""Unify all timestamps into <time datetime> elements (I-93).

One entry point for every human-visible date on every page: full
instants route to tztime.stamp_html (relative body, explicit-UTC
title), calendar days route to tztime.day_html (short body,
midnight-UTC tooltip). Callers stop hand-rolling date markup, so a
timestamp is always a machine-readable <time datetime> with a
hoverable exact value. Pure router, stdlib only; never raises.
"""
from __future__ import annotations

from . import tztime as tztimemod

STATUS_ANCHOR = "status-b22-timetag"


def stamp(value) -> str:
    """Any date-ish value as one <time> element. Never raises.

    Instants (ISO with a time part) get relative bodies; calendar
    days keep their short bodies; missing/unparseable values render
    an unknown time rather than blank.
    """
    try:
        text = str(value or "").strip()
        if not text:
            return tztimemod.day_html(None)
        if "T" in text or len(text) > 10:
            return tztimemod.stamp_html(text)
        return tztimemod.day_html(text)
    except Exception:  # noqa: BLE001 -- stamps never raise
        return "<time title='unknown date (UTC)'>unknown</time>"


def status_section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        sample = stamp("2026-01-05")
        return (
            f"<h3 id='{STATUS_ANCHOR}'>One stamp everywhere "
            "<small>(improvement)</small></h3>"
            "<p>Every human-visible date is a <code>&lt;time&gt;</code> "
            "now — <code>groundwork/timetag.py</code> routes instants "
            "and calendar days through the timezone-explicit stamps on "
            "History days, workload, journal, known-dates, and the "
            "skip-confirmation. A live sample renders below.</p>"
            f"<p>{sample}</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>One stamp everywhere</h3>"
                "<p>Stamp help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "one-stamp",
        "kind": "improvement",
        "title": "One stamp everywhere",
        "blurb": ("Every date on every page is a real <time> element — "
                  "hover for the exact instant."),
        "path": "/reviews",
        "anchor": "attempts",
    }

"""Timezone-explicit timestamps with title tooltips (I-26).

Relative times ("3h ago") hide which zone they are relative to, and
bare dates ("2026-01-05") hide it entirely. Every stamp this module
emits is an ISO instant with an explicit UTC title tooltip, and
absolute dates carry a visible UTC suffix — hover any time for the
exact instant. Pure functions, stdlib only; the History attempt rows
and coverage dates call it. Never raises.
"""
from __future__ import annotations

import html
from datetime import datetime, timezone

STATUS_ANCHOR = "status-b22-tztime"

_WEEK_SECS = 7 * 86400


def _parse(raw) -> datetime | None:
    try:
        text = str(raw or "").strip().replace("Z", "+00:00")
        if not text:
            return None
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:  # noqa: BLE001 -- bad stamps parse as None
        return None


def _now() -> datetime:
    from datetime import datetime as _dt, timezone as _tz
    return _dt.now(_tz.utc)


def stamp_html(raw) -> str:
    """Relative stamp with an explicit-UTC title tooltip.

    "3h ago" keeps its short body; the title names the exact instant
    plus zone. Stamps older than a week render the absolute date with
    a visible UTC suffix. Unparseable input renders an unknown time,
    never "". Never raises.
    """
    try:
        iso = str(raw or "").strip()
        dt = _parse(iso)
        if dt is None:
            return "<time title='unknown date (UTC)'>unknown</time>"
        title = f"{html.escape(iso, quote=True)} (UTC)"
        try:
            secs = int((_now() - dt).total_seconds())
        except Exception:  # noqa: BLE001 -- delta failure reads old
            secs = _WEEK_SECS
        if secs < 0:
            rel = "in the future"
        elif secs < 90:
            rel = "just now"
        elif secs < 5400:
            rel = f"{secs // 60}m ago"
        elif secs < 129600:
            rel = f"{secs // 3600}h ago"
        elif secs < _WEEK_SECS:
            rel = f"{secs // 86400}d ago"
        else:
            rel = f"{iso[:10]} UTC"
        return (f"<time datetime='{html.escape(iso, quote=True)}' "
                f"title='{title}'>{html.escape(rel)}</time>")
    except Exception:  # noqa: BLE001 -- stamps never raise
        return "<time title='unknown date (UTC)'>unknown</time>"


def day_html(day) -> str:
    """YYYY-MM-DD cell with an explicit-UTC title tooltip.

    Coverage timelines store calendar days, not instants; the stamp
    keeps the short body and puts midnight-UTC in the tooltip.
    Hostile input renders unknown; never raises.
    """
    try:
        text = str(day or "").strip()[:10]
        if len(text) != 10 or text[4] != "-" or text[7] != "-":
            return "<time title='unknown date (UTC)'>unknown</time>"
        safe = html.escape(text, quote=True)
        return (f"<time datetime='{safe}' "
                f"title='{safe}T00:00:00Z (UTC)'>{safe}</time>")
    except Exception:  # noqa: BLE001 -- stamps never raise
        return "<time title='unknown date (UTC)'>unknown</time>"


def status_section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        sample = stamp_html("2026-01-05T10:00:00Z")
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Timezone-explicit stamps "
            "<small>(improvement)</small></h3>"
            "<p>Relative times keep their short bodies but every stamp "
            "now names its zone — <code>groundwork/tztime.py</code> "
            "renders History attempt and coverage stamps as ISO instants "
            "with explicit UTC title tooltips. A live sample renders "
            "below.</p>"
            f"<p>{sample}</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Timezone-explicit stamps</h3>"
                "<p>Stamp help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "timezone-stamps",
        "kind": "improvement",
        "title": "Timezone-explicit stamps",
        "blurb": ("Hover any attempt time for the exact UTC instant — "
                  "no more guessing zones."),
        "path": "/reviews",
        "anchor": "timestamps",
    }

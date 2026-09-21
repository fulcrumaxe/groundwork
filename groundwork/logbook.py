"""History page as a logbook (I-71).

Monospace date cells, ruled row separators, and a slightly muted
table header over the real History selectors from
``groundwork/history.py``: the ``table.log`` attempts/coverage/day
tables, the ``p.ok``/``p.stale`` attempt rows, and the ``#timestamps``
note — no markup, DB, or schema changes. ``logbook_css()`` returns raw
CSS declarations only, never ``<style>`` tags — the parent
concatenates it into the head wire next to ``progbar_css()``. All
motion-free by design (no transitions or animations), plus a
``prefers-reduced-motion`` override that re-asserts ``transition:none``
so reduced-motion users stay unaffected. Pure functions, stdlib only,
no I/O.
"""
from __future__ import annotations

import re

STATUS_ANCHOR = "status-b12-logbook"

RULE_COLOR = "#d8d8d8"
HEADER_TONE = "#595959"

TABLE_SELECTORS = ("table.log",)
DATE_SELECTORS = ("table.log td:first-child", "p.ok small", "p.stale small")

_MONO = ("ui-monospace,SFMono-Regular,Menlo,Consolas,"
         "\"Liberation Mono\",monospace")

_HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def table_selectors() -> tuple:
    """History table selectors the rules target; fails closed, never raises."""
    try:
        if isinstance(TABLE_SELECTORS, tuple) and all(
                isinstance(s, str) and s.strip() for s in TABLE_SELECTORS):
            return TABLE_SELECTORS
        return ("table.log",)
    except Exception:  # noqa: BLE001 — selector lookup must never raise
        return ("table.log",)


def date_selectors() -> tuple:
    """Date/timestamp selectors set in monospace; fails closed, never raises."""
    try:
        if isinstance(DATE_SELECTORS, tuple) and all(
                isinstance(s, str) and s.strip() for s in DATE_SELECTORS):
            return DATE_SELECTORS
        return ("table.log td:first-child", "p.ok small", "p.stale small")
    except Exception:  # noqa: BLE001 — selector lookup must never raise
        return ("table.log td:first-child", "p.ok small", "p.stale small")


def _tone(value, default: str) -> str:
    """Validated #rgb/#rrggbb color; anything else fails closed to default."""
    try:
        if isinstance(value, str) and _HEX_RE.match(value):
            return value
        return default
    except Exception:  # noqa: BLE001 — color lookup must never raise
        return default


def rule_color(value=RULE_COLOR) -> str:
    """Row-rule color; non-hex input fails closed to RULE_COLOR, never raises."""
    try:
        return _tone(value, RULE_COLOR)
    except Exception:  # noqa: BLE001 — color lookup must never raise
        return RULE_COLOR


def header_tone(value=HEADER_TONE) -> str:
    """Muted header-ink color; non-hex input fails closed, never raises."""
    try:
        return _tone(value, HEADER_TONE)
    except Exception:  # noqa: BLE001 — color lookup must never raise
        return HEADER_TONE


def logbook_css() -> str:
    """Raw CSS declarations: logbook theme plus reduced-motion override.

    Never emits ``<style>`` tags; the parent wires this into the head
    stylesheet. Motion-free by design — no durations, transitions, or
    animations — with a ``prefers-reduced-motion`` block re-asserting
    ``transition:none``. Never raises.
    """
    try:
        rule = rule_color()
        tone = header_tone()
        dates = "".join(f"{s}{{font-family:{_MONO};"
                        "font-variant-numeric:tabular-nums;white-space:nowrap}}"
                        for s in date_selectors())
        tables = ("table.log{border-collapse:collapse}"
                  f"table.log td{{border-bottom:1px solid {rule}}}"
                  f"table.log th{{color:{tone};font-weight:600;"
                  f"border-bottom:2px solid {rule}}}")
        off = "".join(f"{s}{{transition:none}}"
                      for s in date_selectors() + table_selectors())
        return (tables + dates + "@media(prefers-reduced-motion:reduce){"
                + off + "}")
    except Exception:  # noqa: BLE001 — CSS emitter must never raise
        return ("table.log{border-collapse:collapse}"
                "table.log td{border-bottom:1px solid #d8d8d8}"
                "table.log th{color:#595959;font-weight:600;"
                "border-bottom:2px solid #d8d8d8}"
                "table.log td:first-child{font-family:monospace}"
                "p.ok small{font-family:monospace}"
                "p.stale small{font-family:monospace}"
                "@media(prefers-reduced-motion:reduce){"
                "table.log td{transition:none}}")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Logbook History <small>(improvement)</small></h3>"
        "<p>The History page reads like a logbook: first-column dates in "
        "<code>table.log</code> and relative times in <code>p.ok small</code> / "
        "<code>p.stale small</code> are set monospace with tabular numerals, "
        "rows are ruled with a <code>border-bottom</code> on "
        "<code>table.log td</code>, and <code>table.log th</code> headers are "
        "slightly muted. <code>groundwork/logbook.py</code> provides "
        "<code>logbook_css()</code> (raw declarations only, no "
        "<code>&lt;style&gt;</code> tags — the parent concatenates it into "
        "the head wire) and validated color helpers that fail closed, never "
        "raise. Motion-free by design; a "
        "<code>prefers-reduced-motion</code> block re-asserts "
        "<code>transition:none</code>.</p>"
    )


def tour_entry() -> dict:
    """Tour registry entry for the logbook theme; never raises."""
    try:
        return {"id": "logbook-history", "kind": "improvement",
                "title": "Logbook History",
                "blurb": "History reads like a logbook: monospace dates, ruled rows, muted headers.",
                "path": "/status", "anchor": STATUS_ANCHOR}
    except Exception:  # noqa: BLE001 — tour entry must never raise
        return {"id": "logbook-history", "kind": "improvement",
                "title": "Logbook History",
                "blurb": "History reads like a logbook.",
                "path": "/status", "anchor": "status-b12-logbook"}

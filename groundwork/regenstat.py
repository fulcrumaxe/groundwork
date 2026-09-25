"""Regeneration status, transparently (I-135).

The confusing-flags queue names what needs rewriting; this module
says where each flagged section stands: queue position plus flagged
age, rendered beside the queue banner on the module page. No new
storage — flagged_at already rides the confusing_flags rows — and no
fake progress states: a flag is either awaiting rewrite (with its
age) or gone. Pure functions over the existing table; never raises.
"""
from __future__ import annotations

import html

from . import confusing as confusingmod
from . import db as dbmod
from . import tztime as tztimemod

STATUS_ANCHOR = "status-b22-regenstat"


def flag_statuses(db_path: str, mid: str) -> list:
    """[{section, flagged_at, position}] oldest-first for one module.

    Empty module, no flags, or hostile input yields []; never raises.
    """
    try:
        mid_s = str(mid or "").strip()
        if not mid_s:
            return []
        con = dbmod.connect(db_path)
        try:
            confusingmod._ensure_table(con)
            rows = con.execute(
                "SELECT section_id, flagged_at FROM confusing_flags"
                " WHERE section_id LIKE ? ORDER BY rowid",
                (f"{mid_s}:%",)).fetchall()
        finally:
            con.close()
        return [{"section": str(r[0]), "flagged_at": str(r[1] or ""),
                 "position": i + 1}
                for i, r in enumerate(rows)]
    except Exception:  # noqa: BLE001 -- stats never raise
        return []


def status_html(db_path: str, mid: str) -> str:
    """Per-flag regen status for Handler.module_html.

    "" when nothing is flagged so unflagged pages render
    byte-identical (legacy no-data fallback). Never raises.
    """
    try:
        flags = flag_statuses(db_path, mid)
        if not flags:
            return ""
        items = "".join(
            f"<li>{html.escape(f['section'], quote=True)} — "
            f"awaiting rewrite, {tztimemod.stamp_html(f['flagged_at'])} "
            f"(#{f['position']} in queue)</li>"
            for f in flags)
        return (f"<div id='regen-status'><p><b>Regeneration status:</b> "
                f"{len(flags)} section(s) flagged.</p>"
                f"<ul>{items}</ul></div>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def status_section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        sample = (
            "<div id='regen-status'><p><b>Regeneration status:</b> "
            "1 section(s) flagged.</p><ul><li>m:add#what-it-does — "
            "awaiting rewrite, "
            f"{tztimemod.stamp_html('2026-01-05T10:00:00Z')} "
            "(#1 in queue)</li></ul></div>")
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Regeneration status "
            "<small>(improvement)</small></h3>"
            "<p>Flagged means queued, visibly — "
            "<code>groundwork/regenstat.py</code> lists every flagged "
            "section with its queue position and flagged age beside the "
            "regen-queue banner (<code>Handler.module_html</code>); "
            "unflagged pages render exactly as before. A live sample "
            "renders below.</p>"
            f"{sample}")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Regeneration status</h3>"
                "<p>Status help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "regen-status",
        "kind": "improvement",
        "title": "Regeneration status",
        "blurb": ("Every flagged section shows its queue position and "
                  "age — nothing waits silently."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }

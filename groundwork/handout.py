"""Printable lesson handout (I-119): one lesson as a print-ready page.

A per-section "Print handout" link on the module rendering path opens
``/modules/<mid>/handout/<node>``: a standalone HTML doc with embedded
print CSS, the lesson summary, how-steps, key lines, worked example,
and a read-time estimate. Lessons without study content fall back to
``EMPTY_HTML`` so lesson-less modules render byte-identical legacy
pages. Stdlib only (``html``, ``json``, ``sqlite3``,
``urllib.parse``); never raises.
"""
from __future__ import annotations

import html
import json
import sqlite3
from urllib.parse import quote, unquote

from . import printcss as printcssmod
from . import readtime as readtimemod

STATUS_ANCHOR = "status-b20-handout"

EMPTY_HTML = "<p>No lesson content yet.</p>"

_CONTENT_KEYS = ("summary", "how", "key_lines", "worked",
                 "docstring", "source")


def handout_css() -> str:
    """printcss plus handout rules; raw declarations, no <style> tags."""
    return (printcssmod.print_css() +
            "@media print{.handout{max-width:100%;margin:0}"
            "h1{break-after:avoid}pre,section{break-inside:avoid}}")


def _has_content(lesson) -> bool:
    try:
        return isinstance(lesson, dict) and any(
            lesson.get(k) for k in _CONTENT_KEYS)
    except Exception:  # noqa: BLE001
        return False


def handout_html(lesson, name: str = "", minutes=None) -> str:
    """Standalone handout doc; EMPTY_HTML for missing/empty lessons."""
    try:
        if not _has_content(lesson):
            return EMPTY_HTML
        if isinstance(minutes, int):
            mins = minutes
        else:
            try:
                mins = readtimemod.minutes_for(lesson)
            except Exception:  # noqa: BLE001
                mins = 1
        esc = html.escape
        title = esc(str(name or lesson.get("name") or "Lesson"))
        secs = [f"<h1>{title} <small>({mins} min)</small></h1>"]
        summary = lesson.get("summary")
        if isinstance(summary, str) and summary.strip():
            secs.append(f"<section><h2>Summary</h2><p>{esc(summary)}</p></section>")
        how = [s for s in (lesson.get("how") or [])
               if isinstance(s, str) and s.strip()]
        if how:
            secs.append("<section><h2>How it works</h2><ol>" + "".join(
                f"<li>{esc(s)}</li>" for s in how) + "</ol></section>")
        key_lines = lesson.get("key_lines")
        if isinstance(key_lines, str) and key_lines.strip():
            secs.append(f"<section><h2>Key lines</h2><pre>{esc(key_lines)}</pre></section>")
        worked = lesson.get("worked")
        if isinstance(worked, str) and worked.strip():
            secs.append(f"<section><h2>Worked example</h2><pre>{esc(worked)}</pre></section>")
        return ("<!DOCTYPE html><html><head><meta charset='utf-8'>"
                f"<title>{title}</title><style>{handout_css()}</style></head>"
                f"<body class='handout'>{''.join(secs)}</body></html>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return EMPTY_HTML


def handout_link_html(mid, node) -> str:
    """Per-section 'Print handout' link; "" on hostile input."""
    try:
        if not isinstance(mid, str) or not mid or not isinstance(node, str) or not node:
            return ""
        return (f" <a class='handout-link' href='/modules/{quote(mid, safe='')}"
                f"/handout/{quote(node, safe='')}'>Print handout</a>")
    except Exception:  # noqa: BLE001
        return ""


def page_for(db_path: str, mid: str, node: str) -> str:
    """Handout doc for one lesson; EMPTY_HTML when unknown/empty."""
    try:
        node = unquote(str(node or ""))
        con = sqlite3.connect(str(db_path))
        try:
            row = con.execute("SELECT lessons FROM modules WHERE id=?",
                              (str(mid),)).fetchone()
        finally:
            con.close()
        if not row:
            return EMPTY_HTML
        lessons = json.loads(row[0] or "[]")
        for lesson in lessons:
            if not isinstance(lesson, dict):
                continue
            cid = lesson.get("concept_id", "")
            name = lesson.get("name", "")
            keys = {cid, name}
            if ":" in str(cid):
                keys.add(str(cid).split(":", 1)[1])
            if node in keys:
                return handout_html(lesson, name)
        return EMPTY_HTML
    except Exception:  # noqa: BLE001
        return EMPTY_HTML


def section_html() -> str:
    """Anchored status subsection; joined by the batch20 home module."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Printable lesson handout <small>(improvement)</small></h3>"
        "<p>Any single lesson exports as a clean print-ready handout "
        "with its read-time estimate. <code>groundwork/handout.py</code> "
        "serves <code>/modules/&lt;id&gt;/handout/&lt;lesson&gt;</code> "
        "from the module rendering path (<code>Handler.module_html</code>); "
        "lessons without study content keep the legacy page.</p>"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "lesson-handout",
        "kind": "improvement",
        "title": "Printable lesson handout",
        "blurb": "Any single lesson exports as a clean print-ready "
                 "handout with its read-time estimate.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }

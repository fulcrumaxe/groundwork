"""Gradebook export: your owned proofs as LMS-ready CSV (F-166).

A teacher's multi-student gradebook needs rosters and student
identity this single-user app will never have (the F-164 bar).
The honest solo slice: YOUR gradebook -- one row per concept you
have met (concept, module, owned, owned date, attempts, passes)
as plain CSV with stable headers, shaped so an instructor or LMS
operator can map columns at import time (they supply student
identity; the app stores none). No claim of one-click
Canvas/Moodle/Blackboard import: the file is evidence, and the
mapping note beside it says exactly which column means what.

Grain is the point: I-231 exports attempt rows (no owned flag, no
owned date), F-161 reports module aggregates as History HTML (not
portable), F-160 packs per-module JSON for a successor dev (no
dates, not CSV). This is the whole library, one concept per row,
one portable file.

Caller: ``history.history_html`` lead block renders
``section_html`` (proof table plus download link plus copy-paste
CSV). No owned concepts anywhere renders an anchor-stable
placeholder, so empty History stays table-free (tablescroll
contract). Stdlib only (``csv``, ``html``, ``io``,
``urllib.parse``) plus lazy sibling reads (``db``,
``ownership``, ``milestones``); section builders never raise.
"""
from __future__ import annotations

import csv
import html
import io
from urllib.parse import quote

STATUS_ANCHOR = "status-b28-gradebook"
BOX_ANCHOR = "gradebook"
FILENAME = "gradebook.csv"
HEADER = ("concept", "module", "owned", "owned_date", "attempts", "passes")


def rows(db_path) -> list:
    """One evidence dict per concept, library-wide. Never raises."""
    try:
        from . import db as dbmod
        from . import milestones as milesmod
        from . import ownership as ownmod
        dates = milesmod.owned_dates(db_path)
        con = dbmod.connect(db_path)
        try:
            mods = con.execute(
                "SELECT id, task_summary FROM modules"
                " ORDER BY created_at, id").fetchall()
            out = []
            for m in mods:
                mid = m["id"]
                omap = ownmod.owned_map(con, mid)
                names = {r["id"]: r["name"] for r in con.execute(
                    "SELECT id, name FROM concepts"
                    " WHERE module_id=?", (mid,)).fetchall()}
                passes = {r["cid"]: r["ok"] or 0 for r in con.execute(
                    "SELECT cards.concept_id AS cid,"
                    " SUM(CASE WHEN reviews.grade >= 4"
                    " THEN 1 ELSE 0 END) AS ok"
                    " FROM cards LEFT JOIN reviews"
                    " ON reviews.card_id = cards.id"
                    " WHERE cards.concept_id IN"
                    " (SELECT id FROM concepts WHERE module_id=?)"
                    " GROUP BY cards.concept_id", (mid,)).fetchall()}
                for cid in sorted(omap, key=lambda c: names.get(c, c)):
                    attempts, owned = omap[cid]
                    out.append({
                        "concept": names.get(cid, cid),
                        "module": m["task_summary"] or mid,
                        "owned": bool(owned),
                        "owned_date": dates.get(cid, ""),
                        "attempts": attempts or 0,
                        "passes": passes.get(cid, 0),
                    })
            return out
        finally:
            con.close()
    except Exception:  # noqa: BLE001 -- exports never raise
        return []


def _cell(value) -> str:
    """CSV-safe text; hostile values degrade to ""."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return str(value)
    except Exception:  # noqa: BLE001 -- renderer never raises
        return ""


def _num(value) -> int:
    """CSV-safe count; hostile values degrade to 0."""
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def csv_text(rows) -> str:
    """Pure CSV render; header-only when there is nothing to grade."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(list(HEADER))
    try:
        items = list(rows or [])
    except TypeError:
        items = []
    for r in items:
        if not isinstance(r, dict):
            continue
        w.writerow([_cell(r.get("concept")), _cell(r.get("module")),
                    "yes" if r.get("owned") else "no",
                    _cell(r.get("owned_date")), _num(r.get("attempts")),
                    _num(r.get("passes"))])
    return buf.getvalue()


def gradebook_csv(db_path) -> str:
    """Whole-library gradebook CSV, mirroring exports.reviews_csv."""
    return csv_text(rows(db_path))


def download_href(text) -> str:
    """data: URI so the CSV downloads with no new web route."""
    try:
        return "data:text/csv;charset=utf-8," + quote(str(text or ""))
    except Exception:  # noqa: BLE001 -- link never raises
        return "data:text/csv;charset=utf-8,"


def section_html(db_path) -> str:
    """History gradebook: table plus download plus copy-paste CSV.

    Gated on any-owned: with no owned proofs a gradebook proves
    nothing, and empty History stays table-free. Once earned, ALL
    concepts list -- a gradebook shows every assignment, not passes.
    Never raises.
    """
    try:
        data = rows(db_path)
        if not any(r["owned"] for r in data):
            return (f"<section id='{BOX_ANCHOR}'><h2>Gradebook export</h2>"
                    "<p>No gradebook yet -- own a concept first, then "
                    "export your proofs as CSV.</p></section>")
        text = csv_text(data)
        trs = "".join(
            f"<tr><td>{html.escape(_cell(r['concept']))}</td>"
            f"<td>{html.escape(_cell(r['module']))}</td>"
            f"<td>{'yes' if r['owned'] else 'no'}</td>"
            f"<td>{html.escape(_cell(r['owned_date']))}</td>"
            f"<td>{_num(r['attempts'])}</td>"
            f"<td>{_num(r['passes'])}</td></tr>"
            for r in data)
        return (
            f"<section id='{BOX_ANCHOR}'><h2>Gradebook export</h2>"
            "<p>Your proofs, one row per concept -- "
            f"<a href='{download_href(text)}' download='{FILENAME}'>"
            f"Download {FILENAME}</a> for your records or your "
            "instructor. <small>Your file only: map owned to "
            "pass/fail and passes/attempts to a score at import; "
            "no student identity leaves this device.</small></p>"
            "<table class='log'><tr><th>Concept</th><th>Module</th>"
            "<th>Owned</th><th>Owned date</th><th>Attempts</th>"
            f"<th>Passes</th></tr>{trs}</table>"
            "<details><summary>Copy-paste CSV</summary><pre>"
            f"{html.escape(text)}</pre></details></section>")
    except Exception:  # noqa: BLE001 -- History bytes always survive
        return (f"<section id='{BOX_ANCHOR}'><h2>Gradebook export</h2>"
                "<p>Gradebook temporarily unavailable.</p></section>")


def status_html(db_path) -> str:
    """Anchored status subsection with live gradebook counts."""
    try:
        data = rows(db_path)
        owned_n = sum(1 for r in data if r["owned"])
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Gradebook export "
            "<small>(feature)</small></h3>"
            "<p>Gradebook export (feature): your owned proofs as "
            "one portable CSV -- one row per concept (concept, "
            "module, owned, owned date, attempts, passes) -- "
            "<code>groundwork/gradebook.py</code>, rendered on "
            f"History. Live: {owned_n}/{len(data)} concepts owned. "
            "Instructors map columns at import; no student identity "
            "leaves this device.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Gradebook export</h3>"
                "<p>Gradebook export temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "gradebook-export",
        "kind": "feature",
        "title": "Gradebook export",
        "blurb": ("Your owned proofs as one portable CSV -- one row per "
                  "concept, ready for your records or your instructor."),
        "path": "/reviews",
        "anchor": BOX_ANCHOR,
    }

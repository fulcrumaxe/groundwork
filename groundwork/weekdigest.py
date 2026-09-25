"""Weekly lesson digest: what changed in code you studied (I-149).

Lessons studied in the last seven days (concepts with reviews in
the window) whose before/after version pair differs get one digest
row each: module, lesson, and changed-line counts. Groups by
module, caps at 25 rows, escapes everything. No studied changes —
or hostile input — renders "" so History keeps its legacy bytes.
Pure queries over existing tables (no schema); never raises.
"""
from __future__ import annotations

import html
import json
from datetime import timedelta

STATUS_ANCHOR = "status-b23-weekdigest"

CAP = 25


def _changed_lines(before, after) -> int:
    try:
        b = str(before or "").splitlines()
        a = str(after or "").splitlines()
        return sum(1 for line in a if line not in b) + sum(
            1 for line in b if line not in a)
    except Exception:  # noqa: BLE001 -- counts must never raise
        return 0


def changed_for(lessons) -> list:
    """[{concept, before, after, changed}] for differing pairs."""
    try:
        out = []
        for lesson in (lessons or []):
            if not isinstance(lesson, dict):
                continue
            before = lesson.get("before")
            after = lesson.get("after")
            if not before or not after or before == after:
                continue
            out.append({"concept": str(lesson.get("concept_id")
                                       or lesson.get("concept") or "lesson"),
                        "before": before, "after": after,
                        "changed": _changed_lines(before, after)})
        return out
    except Exception:  # noqa: BLE001 -- scan must never raise
        return []


def group_by_module(changes) -> dict:
    """{module_summary: [changes]} preserving first-seen order."""
    try:
        groups: dict = {}
        for c in (changes or []):
            if not isinstance(c, dict):
                continue
            key = str(c.get("module") or "Module")
            groups.setdefault(key, []).append(c)
        return groups
    except Exception:  # noqa: BLE001 -- grouping must never raise
        return {}


def digest_html(changes, cap: int = CAP) -> str:
    """Grouped digest list, capped; "" when nothing changed."""
    try:
        items = [c for c in (changes or []) if isinstance(c, dict)]
        if not items:
            return ""
        try:
            limit = int(cap)
        except (TypeError, ValueError):
            limit = CAP
        items = items[:max(0, limit)]
        groups = group_by_module(items)
        bits = []
        for module, rows in groups.items():
            lis = "".join(
                f"<li>{html.escape(r.get('concept', 'lesson'))} — "
                f"{int(r.get('changed', 0))} changed lines</li>"
                for r in rows)
            bits.append(f"<h4>{html.escape(module)}</h4><ul>{lis}</ul>")
        return (f"<div class='weekdigest'><h3>Weekly lesson digest</h3>"
                f"{''.join(bits)}</div>")
    except Exception:  # noqa: BLE001 -- digest must never raise
        return ""


def block_html(db_path: str) -> str:
    """Digest over lessons studied in the last 7 days; "" when quiet."""
    try:
        from . import db as dbmod
        from . import sched as schedmod
        since = (schedmod.utcnow() - timedelta(days=7)).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        con = dbmod.connect(db_path)
        try:
            studied = {r[0] for r in con.execute(
                "SELECT DISTINCT cards.concept_id FROM reviews"
                " JOIN cards ON cards.id = reviews.card_id"
                " WHERE reviews.reviewed_at >= ?", (since,)).fetchall()}
            mods = con.execute(
                "SELECT id, task_summary, lessons FROM modules").fetchall()
        finally:
            con.close()
        changes = []
        for m in mods:
            try:
                lessons = json.loads(m["lessons"] or "[]")
            except (ValueError, TypeError):
                continue
            for c in changed_for(lessons):
                cid = c.get("concept")
                if cid in studied or any(
                        str(s).endswith(":" + cid) or str(s) == cid
                        for s in studied):
                    c["module"] = m["task_summary"] or m["id"]
                    changes.append(c)
        return digest_html(changes)
    except Exception:  # noqa: BLE001 -- block must never raise
        return ""


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Weekly lesson digest "
            "<small>(improvement)</small></h3>"
            "<p>What changed in code you studied — "
            "<code>groundwork/weekdigest.py</code> lists lessons with "
            "reviews in the last seven days whose version pair differs, "
            "grouped by module and capped at 25; quiet weeks render "
            "exactly as before.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Weekly lesson digest</h3>"
                "<p>Digest help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "weekly-lesson-digest",
        "kind": "improvement",
        "title": "Weekly lesson digest",
        "blurb": ("What changed in code you studied this week."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }

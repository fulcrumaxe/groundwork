"""Demo: printable lesson handout (I-119).

Full behavior: every lesson on the module rendering path carries a
"Print handout" link (Handler.module_html); one click opens the
standalone print-ready doc (/modules/<mid>/handout/<node>) with the
lesson summary, how-steps, key lines, worked example, and read-time
estimate. seed_db picks the first lesson with summary+how whose
concept row exists, so the filmed module page really renders the
exact link the click beat targets. No overdue-day seeds, so the
sleepsched quiet-hours cushion does not apply.
"""
from __future__ import annotations

import json
import sqlite3
from urllib.parse import quote

SCENARIO = {
    "id": "handout",
    "kind": "improvement",
    "batch": 20,
    "item": "I-119",
    "title": "Printable lesson handout",
    "blurb": "Any single lesson exports as a clean print-ready handout with its read-time estimate.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 20 - Improvement I-119",
         "title": "Printable lesson handout",
         "subtitle": "Any single lesson exports as a clean print-ready handout with its read-time estimate."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b20-handout",
         "caption": "Status documents the improvement: one lesson, one print-ready page.",
         "assert_js": "() => !!document.querySelector('#status-b20-handout')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_mid}",
         "focus": "a.handout-link",
         "caption": "The module page carries a Print handout link on every lesson.",
         "assert_js": "() => !!document.querySelector(\"a.handout-link[href='/modules/{seed_mid}/handout/{seed_node_enc}']\")",
         "assert_want": "True"},
        {"type": "chrome", "duration": 12,
         "url_path": "/modules/{seed_mid}",
         "caption": "One click opens the standalone handout: summary, steps, key lines, read time.",
         "js": ["() => { const a = document.querySelector(\"a.handout-link[href='/modules/{seed_mid}/handout/{seed_node_enc}']\"); "
                "if (!a) return 'link-missing'; a.click(); return 'clicked'; }"],
         "poll_js": "() => document.body.className + ' | ' + document.title",
         "poll_want": "handout",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => document.body.innerText.includes('{seed_lesson}') && document.body.innerText.includes('min')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 6,
         "caption": "Same route from code: full doc for the lesson, empty fallback for unknown nodes.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import handout as m; "
              "db = os.environ['DEMO_DB']; "
              "out = m.page_for(db, '{seed_mid}', '{seed_node}'); "
              "print('standalone-doc:', out.startswith('<!DOCTYPE html>')); "
              "print('lesson-present:', '{seed_lesson}' in out); "
              "print('print-css:', '@media print' in out); "
              "print('has-read-time:', 'min)' in out); "
              "print('unknown-node:', repr(m.page_for(db, '{seed_mid}', 'no-such-node')))"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 20",
         "title": "Print the lesson, keep the estimate.",
         "subtitle": "handout.py serves /modules/<id>/handout/<lesson> -- empty lessons keep the legacy page."},
    ],
}


def seed_db(db_path: str) -> dict:
    """First lesson with summary+how whose concept row exists.

    Returns the module_html node form (concepts.id split on the first
    ":", i.e. the lesson concept_id) plus its quoted href form, so the
    click beat targets the exact link the module page renders.
    """
    con = sqlite3.connect(db_path)
    try:
        mods = con.execute("SELECT id, lessons FROM modules").fetchall()
        for mid, raw in mods:
            try:
                lessons = json.loads(raw or "[]")
            except ValueError:
                continue
            for lesson in lessons:
                if not isinstance(lesson, dict):
                    continue
                summary = lesson.get("summary")
                if not (isinstance(summary, str) and summary.strip()):
                    continue
                how = [s for s in (lesson.get("how") or [])
                       if isinstance(s, str) and s.strip()]
                if not how:
                    continue
                cid = str(lesson.get("concept_id") or "")
                if not cid:
                    continue
                row = con.execute(
                    "SELECT id FROM concepts WHERE module_id=? AND id=?",
                    (mid, f"{mid}:{cid}")).fetchone()
                if not row:
                    continue
                node = row[0].split(":", 1)[1]
                return {"seeded": True, "mid": mid, "node": node,
                        "node_enc": quote(node, safe=""),
                        "lesson": str(lesson.get("name") or node)}
        return {"seeded": False, "reason": "no lesson with summary+how"}
    finally:
        con.close()

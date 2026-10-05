"""Feature demo: predict-then-reveal (F-64).

Full behavior: lesson snippets hide under a native <details> cover
until the learner commits to a prediction (since Batch 16 -- no
JavaScript, so no-JS readers struggle first too). seed_db picks a
module with sourced lessons; the module beat clicks the first cover
open and asserts the reveal.
"""
from __future__ import annotations

import json
import sqlite3

SCENARIO = {
    "id": "predict",
    "kind": "feature",
    "batch": 13,
    "item": "F-64",
    "title": "Predict-then-reveal",
    "blurb": "Every snippet hides under a one-click cover -- predict first.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 13 - Feature F-64",
         "title": "Predict-then-reveal",
         "subtitle": "Every snippet hides under a one-click cover -- predict first."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b13-predict",
         "caption": "Status homes the widget with a live covered double(21) sample.",
         "assert_js": "() => !!document.querySelector('#status-b13-predict') && "
                      "!!document.querySelector('details.predict:not([open])')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: one details, one pre, no open attribute.",
         "commands": [
             ["python3", "-c",
              "from groundwork import predict as m; "
              "w = m.cover_html('double(21)'); "
              "print('covered:', m.is_covered(w)); "
              "print('open fails:', m.is_covered(w.replace('<details', '<details open'))); "
              "print('empty:', repr(m.cover_html('   ')))"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/modules/{seed_module_id}",
         "focus": "details.predict",
         "caption": "One click reveals -- the cover is native details, no JavaScript required.",
         "js": ["() => { const d = document.querySelector('details.predict'); "
                "if (!d) return 'no-cover'; "
                "const s = d.querySelector('summary'); "
                "if (!s) return 'no-summary'; s.click(); return 'revealed'; }"],
         "assert_js": "() => { const d = document.querySelector('details.predict'); "
                      "return !!d && d.open; }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 13",
         "title": "Predict, then reveal.",
         "subtitle": "predict.py covers lesson snippets -- rendering wraps, language sniffed."},
    ],
}


def seed_db(db_path: str) -> dict:
    """First module whose lessons carry source snippets to cover."""
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT id, lessons FROM modules ORDER BY rowid").fetchall()
        for mid, lessons_json in rows:
            try:
                lessons = json.loads(lessons_json or "[]")
            except ValueError:
                continue
            if [L for L in lessons if isinstance(L, dict)
                    and (L.get("source") or "").strip()]:
                return {"seeded": True, "module_id": mid}
        return {"seeded": False, "reason": "no sourced lessons"}
    finally:
        con.close()

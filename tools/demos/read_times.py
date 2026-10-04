"""Improvement demo: lesson read times (Batch 3, I-101).

Full functionality: the module table of contents shows "N min" per
lesson, computed from word count over study text at 200 wpm (min 1).
seed_db picks the module with the most lessons; beats film the TOC,
recompute the minutes from the fixture DB, and show the lessons below.
"""
from __future__ import annotations

import json
import sqlite3

SCENARIO = {
    "id": "read-times",
    "kind": "improvement",
    "batch": 3,
    "item": "I-101",
    "title": "Lesson read times",
    "blurb": "The module table of contents estimates minutes per lesson.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 3 - Improvement I-101",
         "title": "Lesson read times",
         "subtitle": "The module table of contents estimates minutes per lesson."},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules/{seed_mid}",
         "focus": "#readtime",
         "caption": "The table of contents estimates minutes per lesson.",
         "assert_js": "() => { const t = document.querySelector('#readtime'); "
                      "if (!t) return 'missing'; "
                      "return t.querySelectorAll('a').length + '|' + "
                      "(t.textContent.match(/\\d+ min/g) || []).length; }",
         "assert_want": "{seed_concepts}|{seed_concepts}"},
        {"type": "terminal", "duration": 7,
         "caption": "Same numbers from the rule: word count at 200 wpm, minimum one minute.",
         "commands": [
             ["python3", "-c",
              "import json, os, sqlite3; "
              "from groundwork import readtime as m; "
              "con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "row = con.execute(\"SELECT lessons FROM modules WHERE id='{seed_mid}'\").fetchone(); "
              "[print(L.get('name'), '->', m.minutes_for(L), 'min') for L in json.loads(row[0])]"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_mid}",
         "caption": "Estimates atop the real lessons they describe.",
         "assert_js": "() => !!document.querySelector('#readtime') + '|' + "
                      "!!document.querySelector(\"section[id^='lesson-']\")",
         "assert_want": "true|true"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 3",
         "title": "Plan the reading.",
         "subtitle": "readtime.py counts words -- no timing data needed."},
    ],
}


def seed_db(db_path: str) -> dict:
    """The module with the most lessons wins the most estimates."""
    con = sqlite3.connect(db_path)
    try:
        best, best_n = None, 0
        for mid, lessons in con.execute(
                "SELECT id, lessons FROM modules").fetchall():
            try:
                n = len(json.loads(lessons or "[]"))
            except (ValueError, TypeError):
                n = 0
            if n > best_n:
                best, best_n = mid, n
        if not best:
            return {"seeded": False, "reason": "no lessons"}
        n_concepts = con.execute(
            "SELECT COUNT(*) FROM concepts WHERE module_id=?",
            (best,)).fetchone()[0]
        if not n_concepts:
            return {"seeded": False, "reason": "no concepts"}
        return {"seeded": True, "mid": best, "lessons": best_n,
                "concepts": n_concepts}
    finally:
        con.close()

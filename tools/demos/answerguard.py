"""Improvement demo: empty-answer guard (I-151).

Pure server-side check run before submit: blank answers get an
inline warning instead of a silent submit. guard() returns the
verdict; guard_html() renders the role=alert warning line.
Video: Status anchor, live verdicts, warning HTML, tour catalog.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "answerguard",
    "kind": "improvement",
    "batch": 5,
    "item": "I-151",
    "title": "Empty-answer guard",
    "blurb": "Blank submits get an inline warning instead of silence.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 5 - Improvement I-151",
         "title": "Empty-answer guard",
         "subtitle": "Blank submits get an inline warning instead of silence."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b5-answerguard",
         "caption": "Status documents the improvement with its live anchor.",
         "assert_js": "() => !!document.querySelector('#status-b5-answerguard')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The verdict in one call: real answers pass, blanks warn.",
         "commands": [
             ["python3", "-c",
              "from groundwork import answerguard as m; "
              "print(m.guard('  hello  ')); "
              "print(m.guard('   ')); "
              "print(m.guard(None))"],
         ]},
        {"type": "terminal", "duration": 7,
         "caption": "The warning renders as an inline alert; min_chars raises the bar.",
         "commands": [
             ["python3", "-c",
              "from groundwork import answerguard as m; "
              "print(m.guard_html(m.guard('')['warning'])); "
              "print(m.guard('hi', min_chars=5)); "
              "print(m.guard_html(''))"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/tour",
         "caption": "The tour catalog lists Answer guard with a Show-me link.",
         "js": ["() => { const li = [...document.querySelectorAll('li')].find("
                "l => l.innerText.includes('Answer guard')); "
                "if (!li) return 'missing'; li.id = 'tour-hit'; return 'tagged'; }"],
         "focus": "#tour-hit",
         "assert_js": "() => { const li = document.querySelector('#tour-hit'); "
                      "return !!li && li.innerText.includes('Show me'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 5",
         "title": "No more silent submits.",
         "subtitle": "answerguard.py checks before submit -- no DB, no page chrome."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Pure helper: no fixture state needed; verify the library opens."""
    con = sqlite3.connect(db_path)
    try:
        row = con.execute("SELECT COUNT(*) FROM reviews").fetchone()
        return {"seeded": True, "reviews": row[0] if row else 0}
    finally:
        con.close()

"""Improvement demo: reading-progress bar (I-120).

Pure server-HTML helper: progress_bar(pct) renders a stable
id='readprogress' bar with inline width, clamped to 0-100.
Video: Status anchor, live helper output, clamp edges, tour catalog.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "readprogress",
    "kind": "improvement",
    "batch": 5,
    "item": "I-120",
    "title": "Reading-progress bar",
    "blurb": "A slim bar shows how far through a module page you are.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 5 - Improvement I-120",
         "title": "Reading-progress bar",
         "subtitle": "A slim bar shows how far through a module page you are."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b5-readprogress",
         "caption": "Status documents the improvement with its live anchor.",
         "assert_js": "() => !!document.querySelector('#status-b5-readprogress')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The helper in one call: stable id, progressbar role, inline width.",
         "commands": [
             ["python3", "-c",
              "from groundwork import readprogress as m; "
              "print(m.progress_bar(42))"],
         ]},
        {"type": "terminal", "duration": 7,
         "caption": "Clamped to 0-100: overflows, negatives and junk all render safe.",
         "commands": [
             ["python3", "-c",
              "from groundwork import readprogress as m; "
              "print(m.progress_bar(999)); "
              "print(m.progress_bar(-5)); "
              "print(m.progress_bar('nope'))"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/tour",
         "caption": "The tour catalog lists Reading progress with a Show-me link.",
         "js": ["() => { const li = [...document.querySelectorAll('li')].find("
                "l => l.innerText.includes('Reading progress')); "
                "if (!li) return 'missing'; li.id = 'tour-hit'; return 'tagged'; }"],
         "focus": "#tour-hit",
         "assert_js": "() => { const li = document.querySelector('#tour-hit'); "
                      "return !!li && li.innerText.includes('Show me'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 5",
         "title": "How far through you are.",
         "subtitle": "readprogress.py renders the bar -- reduced-motion safe, no JS."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Pure helper: no fixture state needed; verify the library opens."""
    con = sqlite3.connect(db_path)
    try:
        row = con.execute("SELECT COUNT(*) FROM modules").fetchone()
        return {"seeded": True, "modules": row[0] if row else 0}
    finally:
        con.close()

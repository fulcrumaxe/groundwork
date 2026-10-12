"""Improvement demo: learner-vs-expected output diff (I-157).

Full behavior: wrong type-8 predictions show yours against expected
line by line (text in feedback, HTML table in docs); matches and
missing references render the legacy single line. Pure helpers.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "outdiff",
    "kind": "improvement",
    "batch": 24,
    "item": "I-157",
    "title": "Output mismatch side-by-side",
    "blurb": "Wrong prediction? Yours vs expected, line by line.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 24 - Improvement I-157",
         "title": "Output mismatch side-by-side",
         "subtitle": "One-line repr becomes a line-by-line diff."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b24-outdiff",
         "caption": "Status carries the live sample table with its anchor.",
         "assert_js": "() => !!document.querySelector('#status-b24-outdiff') "
                      "&& !!document.querySelector('table.outdiff')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "Row pairs name the first mismatch; matches stay silent.",
         "commands": [
             ["python3", "-c",
              "from groundwork import outdiff as m; "
              "print('mismatch:', m.has_mismatch('a\\nb\\n', 'a\\nB\\n'), '| first:', m.first_mismatch('a\\nb\\n', 'a\\nB\\n')); "
              "print('match:', repr(m.mismatch_text('5', '5'))); "
              "print(m.mismatch_text('6', '5'))"],
         ]},
        {"type": "terminal", "duration": 7,
         "caption": "HTML renders the same pairs; hostile input yields ''.",
         "commands": [
             ["python3", "-c",
              "from groundwork import outdiff as m; "
              "print(m.mismatch_html('a\\nb\\n', 'a\\nB\\n')[:160]); "
              "print('match-html:', repr(m.mismatch_html('x', 'x'))); "
              "print('rows:', m.rows('a', 'b'))"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/tour",
         "caption": "The tour catalog lists the diff with a Show-me link.",
         "js": ["() => { const li = [...document.querySelectorAll('li')].find("
                "l => l.innerText.includes('Output mismatch')); "
                "if (!li) return 'missing'; li.id = 'tour-hit'; return 'tagged'; }"],
         "focus": "#tour-hit",
         "assert_js": "() => { const li = document.querySelector('#tour-hit'); "
                      "return !!li && li.innerText.includes('Show me'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 24",
         "title": "See the miss.",
         "subtitle": "outdiff.py diffs yours vs expected -- matches stay quiet."},
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

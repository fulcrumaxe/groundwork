"""Improvement demo: result verdict auto-scroll (I-30).

Full behavior: after grading, the result screen's verdict block
(id='verdict') takes focus and scrolls into view, honouring
prefers-reduced-motion -- queue-return position stays owned by
scrollpos. The submit beat answers a due card and asserts the
verdict is present, focused, and scripted.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "autoscroll",
    "kind": "improvement",
    "batch": 7,
    "item": "I-30",
    "title": "Result verdict auto-scroll",
    "blurb": "After grading, the verdict block takes focus and scrolls into view.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 7 - Improvement I-30",
         "title": "Result verdict auto-scroll",
         "subtitle": "Grade it, and the verdict comes to you -- motion-aware."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b7-autoscroll",
         "caption": "Status documents the improvement: focusable verdict, reduced-motion aware.",
         "assert_js": "() => !!document.querySelector('#status-b7-autoscroll')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: the verdict paragraph becomes a focusable anchor.",
         "commands": [
             ["python3", "-c",
              "from groundwork import autoscroll as m; "
              "print(m.verdict_open(True)); "
              "print(m.enhance_result(\"<p class='verdict ok'>Great</p>\"))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "article:has(form[action='/cards/{seed_card_id}/review'])",
         "caption": "A due card waits -- answer it and watch where the verdict lands.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"textarea[name='answer']\"); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Submit -- the verdict takes focus and scrolls into view.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector(\"textarea[name='answer']\"); "
                "if (!ta) return 'no-textarea'; ta.value = 'a demo answer'; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.getElementById('verdict') ? 'verdict-found' : 'waiting'",
         "poll_want": "verdict-found",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => { const v = document.getElementById('verdict'); "
                      "return !!v && document.activeElement === v && "
                      "!!document.querySelector('[data-autoscroll-verdict]'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 7",
         "title": "The verdict finds you.",
         "subtitle": "autoscroll.py owns the result half -- scrollpos keeps the queue half."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Force one textarea-type card due-first for the submit beat to answer."""
    con = sqlite3.connect(db_path)
    try:
        card = con.execute(
            "SELECT id FROM cards WHERE exercise_type IN "
            "('5','6','24','25','82','83','84','85','86','90','26','27','28',"
            "'29','31','32','33','34','35','37','38','39','40')"
            " ORDER BY due LIMIT 1").fetchone()
        if not card:
            card = con.execute(
                "SELECT id FROM cards ORDER BY due LIMIT 1").fetchone()
        if not card:
            return {"seeded": False, "reason": "no cards"}
        cid = card[0]
        con.execute("UPDATE cards SET due='2000-01-01T00:00:00Z' WHERE id=?",
                    (cid,))
        con.commit()
        return {"seeded": True, "card_id": cid}
    finally:
        con.close()

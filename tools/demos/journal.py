"""Feature demo: metacognition journal (Batch 4, F-68).

Full functionality: /journal asks a data-driven weekly misjudgment
question and keeps private entries. seed_db plants four confident
misses on explain exercises, so the prompt must name the exact gap;
the beats then save a new entry and show it listed.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "journal",
    "kind": "feature",
    "batch": 4,
    "item": "F-68",
    "title": "Metacognition journal",
    "blurb": "Weekly what-did-you-misjudge prompt, answered privately.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 4 - Feature F-68",
         "title": "Metacognition journal",
         "subtitle": "Weekly what-did-you-misjudge prompt, answered privately."},
        {"type": "terminal", "duration": 7,
         "caption": "The prompt is data-driven: confidence beat accuracy by 100 points.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import journal as j; "
              "print(j.week_prompt(os.environ.get('DEMO_DB', 'groundwork.db')))"],
         ]},
        {"type": "chrome", "duration": 9,
         "url_path": "/journal",
         "focus": "#journal",
         "caption": "This week's question, the private form, past entries.",
         "assert_js": "() => document.body.innerText.includes('felt 100% confident but scored 0%') + '|' + "
                      "document.body.innerText.includes('{seed_past}')",
         "assert_want": "true|true"},
        {"type": "chrome", "duration": 9,
         "url_path": "/journal",
         "caption": "Saving an entry keeps it under today's prompt.",
         "js": ["() => { const f = document.querySelector(\"form[action='/journal']\"); "
                "if (!f) return 'journal-form-missing'; "
                "const ta = f.querySelector('textarea[name=body]'); "
                "if (!ta) return 'no-body-box'; ta.value = '{seed_new}'; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 4000)",
         "poll_want": "Entry saved",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => document.body.innerText.includes('Entry saved')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 7,
         "url_path": "/journal",
         "focus": "#journal article",
         "caption": "Back in the journal: the new entry leads past entries.",
         "assert_js": "() => document.body.innerText.includes('{seed_new}')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 4",
         "title": "What did you misjudge?",
         "subtitle": "journal.py turns calibration gaps into private prompts."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Four confident misses on explain cards, plus one past entry.

    Grade 2 at confidence 5 is 0% accuracy against 100% felt
    confidence -- the widest possible gap, so the prompt must name
    explain exercises with those exact numbers.
    """
    con = sqlite3.connect(db_path)
    try:
        cards = con.execute(
            "SELECT id FROM cards WHERE exercise_type = '5'"
            " ORDER BY due LIMIT 4").fetchall()
        if len(cards) < 4:
            return {"seeded": False, "reason": "need 4 explain cards"}
        con.execute("DELETE FROM reviews")
        for (cid,) in cards:
            con.execute("INSERT INTO reviews(card_id, grade, confidence,"
                        " submission) VALUES(?, 2, 5, 'journal seed')",
                        (cid,))
        past, new = "JournalPast42", "JournalNew42"
        con.execute("DELETE FROM journal_entries WHERE body IN (?, ?)",
                    (past, new))
        con.execute("INSERT INTO journal_entries(created_day, prompt, body)"
                    " VALUES('2026-01-02', 'past seed prompt', ?)", (past,))
        con.commit()
        return {"seeded": True, "past": past, "new": new}
    finally:
        con.close()

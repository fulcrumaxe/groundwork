"""Pilot improvement demo: answer history diff (I-197).

Full functionality: a repeat review whose answer changed shows
"Last time you wrote X" on the verdict screen; first attempts and
unchanged repeats stay quiet. seed_db forces one card due-first with
a stored prior answer of "Paris"; the /due beat submits "Lyon".
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "answerhist",
    "kind": "improvement",
    "batch": 29,
    "item": "I-197",
    "title": "Answer history diff",
    "blurb": "When your answer changes, the result shows what you wrote last time.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 29 - Improvement I-197",
         "title": "Answer history diff",
         "subtitle": "Repeat reviews now name your prior answer -- catch repeated mistakes."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b29-answerhist",
         "caption": "Status documents the improvement with a live format sample.",
         "assert_js": "() => !!document.querySelector('#status-b29-answerhist')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: changed answers name the prior; first attempts stay quiet.",
         "commands": [
             ["python3", "-c",
              "from groundwork import answerhist as m; "
              "print(repr(m.diff_line('Paris', 'Lyon'))); "
              "print(repr(m.diff_line('Paris', 'Paris'))); "
              "print(repr(m.diff_line('', 'Lyon')))"],
         ]},
        {"type": "chrome", "duration": 14,
         "url_path": "/due",
         "caption": "Answer the due card with a changed answer -- the verdict names your prior.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector('textarea[name=answer]'); "
                "if (!ta) return 'no-textarea'; ta.value = 'Lyon'; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Last time you wrote",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => document.body.innerText.includes('Last time you wrote \"Paris\"')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 6,
         "caption": "Proof in the fixture DB: prior 'Paris', current answer differs.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "rows = con.execute('SELECT submission FROM reviews ORDER BY rowid DESC LIMIT 2').fetchall(); "
              "print([r[0][:40] for r in rows])"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 29",
         "title": "Repeated mistakes, caught.",
         "subtitle": "answerhist.py attaches the diff at grade time -- no schema change."},
    ],
}


def seed_db(db_path: str) -> dict:
    """One textarea card due-now with a stored prior answer of 'Paris'.

    Prefers textarea exercise types so the beat can type a changed
    answer into a real field; the beat targets this card's form by
    exact action URL and native-submits (f.submit skips the collapse
    interception, landing on the full verdict page like no-JS).
    """
    con = sqlite3.connect(db_path)
    try:
        card = con.execute(
            "SELECT id FROM cards WHERE exercise_type IN "
            "('5','6','24','25','82','83','84','85','86','90')"
            " ORDER BY due LIMIT 1").fetchone()
        if not card:
            card = con.execute(
                "SELECT id FROM cards ORDER BY due LIMIT 1").fetchone()
        if not card:
            return {"seeded": False, "reason": "no cards"}
        cid = card[0]
        con.execute("UPDATE cards SET due='2000-01-01T00:00:00Z' WHERE id=?",
                    (cid,))
        con.execute("DELETE FROM reviews WHERE card_id=?", (cid,))
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, submission)"
            " VALUES(?, 2, 3, 'Paris')", (cid,))
        con.commit()
        return {"seeded": True, "card_id": cid, "prior": "Paris"}
    finally:
        con.close()

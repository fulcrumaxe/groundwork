"""Feature demo: weekly letter (Batch 4, F-106).

Full functionality: Status carries an auto-drafted private progress
note -- this week's attempts, owned count, the weakest skill, and one
concrete next step. seed_db plants a weak explain pair plus a strong
recall trio, so the letter must name the tender spot exactly.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

SCENARIO = {
    "id": "weekly-letter",
    "kind": "feature",
    "batch": 4,
    "item": "F-106",
    "title": "Weekly letter",
    "blurb": "An auto-drafted private progress note -- gentle, never streaky.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 4 - Feature F-106",
         "title": "Weekly letter",
         "subtitle": "An auto-drafted private progress note -- gentle, never streaky."},
        {"type": "terminal", "duration": 8,
         "caption": "The draft: five attempts, a tender spot, one next step.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import letter as l; "
              "print(l.draft(os.environ.get('DEMO_DB', 'groundwork.db')))"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/status",
         "focus": "#status-letter",
         "caption": "Status carries the letter: gentle, data-driven, private.",
         "assert_js": "() => { const h = document.querySelector('#status-letter'); "
                      "const p = h ? h.nextElementSibling : null; "
                      "const t = p ? p.textContent : ''; "
                      "return t.includes('this week you made 5 attempts across 2 active days, passing 3 (60%)') + '|' + "
                      "t.includes('tender spot is explain (0% this week)'); }",
         "assert_want": "true|true"},
        {"type": "terminal", "duration": 6,
         "caption": "Explain at 0% is the tender spot; recall at 100% is not.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; "
              "con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "rows = con.execute('SELECT cards.exercise_type, COUNT(*), SUM(grade >= 4) FROM reviews JOIN cards ON cards.id = reviews.card_id GROUP BY 1 ORDER BY 1').fetchall(); "
              "[print('type %s: %d attempts, %d passed' % r) for r in rows]"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 4",
         "title": "Keep going -- gently.",
         "subtitle": "letter.py drafts prose from the week's real numbers."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Weak explain pair (0%) plus strong recall trio (100%).

    Two active days, five attempts, three passes; one card stays due
    so the letter names a concrete next step.
    """
    con = sqlite3.connect(db_path)
    try:
        explain = con.execute(
            "SELECT id FROM cards WHERE exercise_type = '5'"
            " ORDER BY due LIMIT 2").fetchall()
        recall = con.execute(
            "SELECT id FROM cards WHERE exercise_type = '1'"
            " ORDER BY due LIMIT 3").fetchall()
        if len(explain) < 2 or len(recall) < 3:
            return {"seeded": False, "reason": "need explain + recall cards"}
        now = datetime.now(timezone.utc).replace(microsecond=0)
        con.execute("DELETE FROM reviews")
        day1 = (now - timedelta(days=1)).replace(hour=12, minute=0)
        day2 = (now - timedelta(days=2)).replace(hour=12, minute=0)
        for i, (cid,) in enumerate(explain):
            iso = (day1 - timedelta(minutes=i)).strftime(
                "%Y-%m-%dT%H:%M:%SZ")
            con.execute("INSERT INTO reviews(card_id, grade, confidence,"
                        " reviewed_at, submission) VALUES(?, ?, 3, ?, 'letter seed')",
                        (cid, (2, 3)[i], iso))
        for i, (cid,) in enumerate(recall):
            iso = (day2 - timedelta(minutes=i)).strftime(
                "%Y-%m-%dT%H:%M:%SZ")
            con.execute("INSERT INTO reviews(card_id, grade, confidence,"
                        " reviewed_at, submission) VALUES(?, ?, 4, ?, 'letter seed')",
                        (cid, (5, 5, 4)[i], iso))
        con.execute("UPDATE cards SET due='2999-01-01T00:00:00Z'")
        con.execute("UPDATE cards SET due='2000-01-01T00:00:00Z' WHERE id=?",
                    (explain[0][0],))
        con.commit()
        return {"seeded": True}
    finally:
        con.close()

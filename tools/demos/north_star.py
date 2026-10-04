"""Feature demo: north-star dashboard (Batch 4, F-52).

Full functionality: Status shows delayed accuracy -- pass rate on
reviews of mature cards only (21+ day stability) -- plus owned
concepts. seed_db plants four mature reviews at 75% plus two fluent
immature passes that must NOT count, and one owned concept.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "north-star",
    "kind": "feature",
    "batch": 4,
    "item": "F-52",
    "title": "North-star dashboard",
    "blurb": "Delayed accuracy on mature cards -- the number that matters.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 4 - Feature F-52",
         "title": "North-star dashboard",
         "subtitle": "Delayed accuracy on mature cards -- the number that matters."},
        {"type": "terminal", "duration": 8,
         "caption": "The snapshot: mature-only accuracy, owned, attempts.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import northstar as n; "
              "s = n.snapshot(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "print('mature reviews:', s['mature_n']); "
              "print('delayed accuracy: %.0f%%' % (s['delayed_acc'] * 100)); "
              "print('owned:', s['owned'], '| attempts:', s['attempts'])"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/status",
         "focus": "#status-northstar",
         "caption": "Status: 75% delayed accuracy on four mature recalls.",
         "assert_js": "() => { const h = document.querySelector('#status-northstar'); "
                      "const p = h ? h.nextElementSibling : null; "
                      "return p ? p.textContent : 'missing'; }",
         "assert_want": "1 concepts owned \u00b7 8 attempts. Delayed accuracy 75% (n=4)"},
        {"type": "terminal", "duration": 6,
         "caption": "Same-day fluency excluded: only mature rows count.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; "
              "con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "m = con.execute('SELECT COUNT(*), SUM(grade >= 4) FROM reviews WHERE prev_stability >= 21').fetchone(); "
              "f = con.execute('SELECT COUNT(*), SUM(grade >= 4) FROM reviews WHERE prev_stability < 21').fetchone(); "
              "print('mature: %d reviews, %d passed' % m); "
              "print('immature: %d reviews, %d passed (excluded)' % f)"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 4",
         "title": "The number that matters.",
         "subtitle": "northstar.py counts mature recalls; fluency never counts."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Four mature reviews at 75%, two fluent passes excluded, one owned.

    Owned needs a grade>=4 pass on a modify/create exercise plus two
    attempts, so the owned concept's pair lands on a modify-type card
    with low stability snapshots (never mature, never double-counted).
    """
    con = sqlite3.connect(db_path)
    try:
        recall = con.execute(
            "SELECT id, concept_id FROM cards WHERE exercise_type = '1'"
            " ORDER BY due LIMIT 6").fetchall()
        mod = con.execute(
            "SELECT id, concept_id FROM cards WHERE exercise_type IN "
            "('12','14','19','20','27','24','23') ORDER BY due LIMIT 1"
            ).fetchone()
        if len(recall) < 6 or not mod:
            return {"seeded": False, "reason": "need recall + modify cards"}
        con.execute("DELETE FROM reviews")
        for (cid, _), grade in zip(recall[:4], (5, 4, 2, 5)):
            con.execute("INSERT INTO reviews(card_id, grade, confidence,"
                        " prev_stability, submission)"
                        " VALUES(?, ?, 3, 25.0, 'northstar mature')",
                        (cid, grade))
        for cid, _ in recall[4:6]:
            con.execute("INSERT INTO reviews(card_id, grade, confidence,"
                        " prev_stability, submission)"
                        " VALUES(?, 5, 5, 2.0, 'northstar fluent')",
                        (cid,))
        for _ in range(2):
            con.execute("INSERT INTO reviews(card_id, grade, confidence,"
                        " prev_stability, submission)"
                        " VALUES(?, 5, 4, 1.0, 'northstar owned')",
                        (mod[0],))
        con.commit()
        return {"seeded": True, "owned_concept": mod[1]}
    finally:
        con.close()

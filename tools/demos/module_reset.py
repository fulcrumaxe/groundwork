"""Feature demo: module reset (Batch 3, I-236).

Full functionality: a confirm page states what goes (reviews,
scheduling, mastery) and what stays (lessons, cards); confirming
wipes progress and the module redisplays at zero. seed_db plants two
passing reviews per card plus drifted scheduling and high mastery so
the wipe has something to delete.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "module-reset",
    "kind": "feature",
    "batch": 3,
    "item": "I-236",
    "title": "Module reset",
    "blurb": "Start a module over from a confirm page -- lessons stay, progress goes.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 3 - Feature I-236",
         "title": "Module reset",
         "subtitle": "Start a module over from a confirm page -- lessons stay, progress goes."},
        {"type": "chrome", "duration": 6,
         "url_path": "/modules/{seed_mid}",
         "focus": "#reset",
         "caption": "Every module page offers a Reset progress entry point.",
         "assert_js": "() => { const a = document.querySelector('#reset a'); "
                      "return a ? a.getAttribute('href') : 'missing'; }",
         "assert_want": "/modules/{seed_mid}/reset"},
        {"type": "chrome", "duration": 7,
         "url_path": "/modules/{seed_mid}/reset",
         "caption": "A confirm page states what goes and what stays.",
         "assert_js": "() => !!document.querySelector('#reset-confirm') + '|' + "
                      "document.body.innerText.includes('Lessons and cards stay')",
         "assert_want": "true|true"},
        {"type": "chrome", "duration": 12,
         "url_path": "/modules/{seed_mid}/reset",
         "caption": "Confirming wipes reviews, restores fresh scheduling, zeroes mastery.",
         "js": ["() => { const f = document.querySelector(\"form[action='/modules/{seed_mid}/reset']\"); "
               "if (!f) return 'reset-form-missing'; f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 4000)",
         "poll_want": "Reset complete",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => document.body.innerText.includes("
                      "'{seed_reviews} review(s) deleted, {seed_cards} card(s) back')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules/{seed_mid}",
         "caption": "Back on the module: lessons stay, progress reads zero.",
         "assert_js": "() => document.body.innerText.includes("
                      "'0/{seed_concepts} concepts owned')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 6,
         "caption": "Proof in the fixture DB: no reviews, zeroed mastery, fresh scheduling.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; "
              "con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "mid = '{seed_mid}'; "
              "r = con.execute('SELECT COUNT(*) FROM reviews WHERE card_id IN (SELECT cards.id FROM cards JOIN concepts ON concepts.id = cards.concept_id WHERE concepts.module_id=?)', (mid,)).fetchone()[0]; "
              "m = con.execute('SELECT MAX(mastery) FROM concepts WHERE module_id=?', (mid,)).fetchone()[0]; "
              "s = con.execute('SELECT COUNT(DISTINCT stability) FROM cards JOIN concepts ON concepts.id = cards.concept_id WHERE concepts.module_id=?', (mid,)).fetchone()[0]; "
              "print('reviews left:', r); print('max mastery:', m); print('distinct stabilities:', s)"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 3",
         "title": "Lessons stay, progress goes.",
         "subtitle": "reset.py deletes reviews, restores scheduling, zeroes mastery."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant two passing reviews per card plus drifted scheduling.

    Pre-existing reviews for the module are cleared first so the
    wiped count is deterministic. The module with the most cards
    makes the wipe unmistakable.
    """
    con = sqlite3.connect(db_path)
    try:
        m = con.execute(
            "SELECT concepts.module_id, COUNT(*) FROM cards "
            "JOIN concepts ON concepts.id = cards.concept_id "
            "GROUP BY concepts.module_id "
            "ORDER BY COUNT(*) DESC LIMIT 1").fetchone()
        if not m:
            return {"seeded": False, "reason": "no cards"}
        mid = m[0]
        cards = con.execute(
            "SELECT cards.id FROM cards JOIN concepts"
            " ON concepts.id = cards.concept_id"
            " WHERE concepts.module_id=?", (mid,)).fetchall()
        con.execute(
            "DELETE FROM reviews WHERE card_id IN (SELECT cards.id"
            " FROM cards JOIN concepts ON concepts.id = cards.concept_id"
            " WHERE concepts.module_id=?)", (mid,))
        planted = 0
        for (cid,) in cards:
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, submission)"
                " VALUES(?, 5, 4, 'reset seed pass')", (cid,))
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, submission)"
                " VALUES(?, 4, 3, 'reset seed pass 2')", (cid,))
            planted += 2
        con.execute(
            "UPDATE cards SET stability=6.0, difficulty=0.9, lapses=2,"
            " due='2000-01-01T00:00:00Z'"
            " WHERE concept_id IN (SELECT id FROM concepts"
            " WHERE module_id=?)", (mid,))
        con.execute("UPDATE concepts SET mastery=0.95 WHERE module_id=?",
                    (mid,))
        con.commit()
        n_concepts = con.execute(
            "SELECT COUNT(*) FROM concepts WHERE module_id=?",
            (mid,)).fetchone()[0]
        return {"seeded": True, "mid": mid, "concepts": n_concepts,
                "cards": len(cards), "reviews": planted}
    finally:
        con.close()

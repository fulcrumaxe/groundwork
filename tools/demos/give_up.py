"""Batch 1 improvement demo: the give-up path.

Full functionality: stuck on a Due card, Give up reveals the answer
only AFTER the attempt is recorded -- blank plus floor confidence
grades an honest 0 and counts one lapse. seed_db forces one card
due-first with zeroed lapses and no reviews; the /due interaction
beat native-submits the seeded give-up form (f.submit skips the
collapse interception, landing on the full verdict page like no-JS)
and the terminal beat shows the grade-0 row in the fixture DB.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "give-up",
    "kind": "improvement",
    "batch": 1,
    "item": "I-159",
    "title": "Give-up path",
    "blurb": "Stuck? Give up shows the answer and records the lapse honestly.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 1 - Improvement give-up",
         "title": "Give-up path",
         "subtitle": "Stuck? Surrender reveals the answer and logs an honest grade 0."},
        {"type": "chrome", "duration": 7,
         "url_path": "/due",
         "focus": "#giveup",
         "caption": "Every answer form ends with Give up -- the honest exit for stuck moments.",
         "assert_js": "() => { const b = document.querySelector('#giveup'); "
                      "return b ? b.textContent : 'missing'; }",
         "assert_want": "Give up"},
        {"type": "terminal", "duration": 6,
         "caption": "The rule: blank plus floor confidence is a surrender, graded 0 with a lapse.",
         "commands": [
             ["python3", "-c",
              "from groundwork import reveal as r, giveup as g; "
              "print('surrender?', r.is_reveal_request('', 1), '| attempt?', r.is_reveal_request('Paris', 4)); "
              "print('grade:', g.GIVEUP_GRADE, '|', g.lapse_line(1))"],
         ]},
        {"type": "chrome", "duration": 14,
         "url_path": "/due",
         "caption": "Give up on the seeded card -- the verdict reveals the answer and names the cost.",
         "js": ["() => { const forms = Array.prototype.slice.call(document.querySelectorAll(\"form[action='/cards/{seed_card_id}/review']\")); "
                "const g = forms.filter(function (f) { return f.querySelector('button.giveup'); })[0]; "
                "if (!g) return 'giveup-form-missing'; g.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Gave up",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => document.body.innerText.includes('Recorded as a lapse')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 6,
         "caption": "Proof in the fixture DB: grade-0 review, blank submit, lapse counted.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "print('review:', con.execute(\"SELECT grade, confidence, submission FROM reviews WHERE card_id='{seed_card_id}' ORDER BY rowid DESC LIMIT 1\").fetchone()); "
              "print('lapses:', con.execute(\"SELECT lapses FROM cards WHERE id='{seed_card_id}'\").fetchone())"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 1",
         "title": "Surrender, logged honestly.",
         "subtitle": "Blank plus confidence 1: answer revealed, lapse recorded."},
    ],
}


def seed_db(db_path: str) -> dict:
    """One card due-first with zeroed lapses and no reviews.

    The give-up form exists on every exercise type, so any card will
    do; backdating to 2000 makes it the undisputed lead card (stable
    #giveup anchor) and wiping its reviews keeps the DB-proof beat to
    exactly one grade-0 row. The beat picks the seeded form containing
    button.giveup -- never first-form-on-page, since the answer form
    shares the same action URL.
    """
    con = sqlite3.connect(db_path)
    try:
        card = con.execute(
            "SELECT id FROM cards ORDER BY due LIMIT 1").fetchone()
        if not card:
            return {"seeded": False, "reason": "no cards"}
        cid = card[0]
        con.execute("UPDATE cards SET due='2000-01-01T00:00:00Z', lapses=0"
                    " WHERE id=?", (cid,))
        con.execute("DELETE FROM reviews WHERE card_id=?", (cid,))
        con.commit()
        return {"seeded": True, "card_id": cid}
    finally:
        con.close()

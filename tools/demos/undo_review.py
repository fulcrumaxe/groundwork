"""Improvement demo: undo last review (Batch 4, I-224).

Full functionality: a misclicked grade is recoverable within 60
seconds -- scheduling and mastery restore, the review row drops.
seed_db wipes reviews and stages one due card with known scheduling;
the beats answer it, then undo it, proving the full loop.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "undo-review",
    "kind": "improvement",
    "batch": 4,
    "item": "I-224",
    "title": "Undo last review",
    "blurb": "Misclick recovery within 60 seconds -- scheduling restored.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 4 - Improvement I-224",
         "title": "Undo last review",
         "subtitle": "Misclick recovery within 60 seconds -- scheduling restored."},
        {"type": "chrome", "duration": 12,
         "url_path": "/due",
         "caption": "Answer the due card -- the verdict lands with a grade.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector('textarea[name=answer]'); "
                "if (!ta) return 'no-textarea'; ta.value = 'Lyon'; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.includes('PASS') || "
                      "document.body.innerText.includes('FAIL') ? 'verdict-shown' : 'waiting'",
         "poll_want": "verdict-shown",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/reviews",
         "focus": "#undo",
         "caption": "History offers undo: the review is seconds old.",
         "assert_js": "() => { const h = document.querySelector('#undo'); "
                      "const p = h ? h.nextElementSibling : null; "
                      "return p ? p.textContent : 'missing'; }",
         "assert_want": "Misclick? Undo grade"},
        {"type": "chrome", "duration": 10,
         "url_path": "/reviews",
         "caption": "Undoing restores scheduling and drops the row.",
         "js": ["() => { const f = document.querySelector(\"form[action='/reviews/undo']\"); "
                "if (!f) return 'undo-form-missing'; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 4000)",
         "poll_want": "scheduling restored",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => document.body.innerText.includes('scheduling restored')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 5,
         "caption": "Proof: zero reviews, and the staged scheduling is back.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; "
              "con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "print('reviews left:', con.execute('SELECT COUNT(*) FROM reviews').fetchone()[0]); "
              "row = con.execute(\"SELECT stability, difficulty, lapses FROM cards WHERE id = '{seed_card_id}'\").fetchone(); "
              "print('scheduling back to:', tuple(row)); "
              "print('mastery back to:', con.execute(\"SELECT mastery FROM concepts WHERE id = '{seed_concept}'\").fetchone()[0])"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 4",
         "title": "Misclicks forgiven.",
         "subtitle": "undo.py snapshots every review and restores within 60 seconds."},
    ],
}


def seed_db(db_path: str) -> dict:
    """One textarea card due now with staged scheduling to restore.

    Prefers textarea exercise types so the beat can type into a real
    field; the beat targets this card's form by exact action URL and
    native-submits (f.submit skips the collapse interception, landing
    on the full verdict page like no-JS).
    """
    con = sqlite3.connect(db_path)
    try:
        card = con.execute(
            "SELECT id, concept_id FROM cards WHERE exercise_type IN "
            "('5','6','24','25','82','83','84','85','86','90')"
            " ORDER BY due LIMIT 1").fetchone()
        if not card:
            card = con.execute(
                "SELECT id, concept_id FROM cards ORDER BY due LIMIT 1"
                ).fetchone()
        if not card:
            return {"seeded": False, "reason": "no cards"}
        cid, concept = card[0], card[1]
        con.execute("DELETE FROM reviews")
        con.execute("UPDATE cards SET due='2999-01-01T00:00:00Z'")
        con.execute("UPDATE cards SET due='2000-01-01T00:00:00Z',"
                    " stability=3.0, difficulty=0.5, retrievability=0.8,"
                    " lapses=2 WHERE id=?", (cid,))
        con.execute("UPDATE concepts SET mastery=0.4 WHERE id=?",
                    (concept,))
        con.commit()
        return {"seeded": True, "card_id": cid, "concept": concept}
    finally:
        con.close()

"""Improvement demo: clarity votes (Batch 4, I-114).

Full functionality: learners rate each lesson 1-5 and the average
feeds generation quality. seed_db plants two votes (4, 5) on the
first lesson; the beat casts a third vote for 5, so the average must
move from 4.5 to 4.7.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "clarity-votes",
    "kind": "improvement",
    "batch": 4,
    "item": "I-114",
    "title": "Clarity votes",
    "blurb": "Rate each lesson 1-5; averages feed generation quality.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 4 - Improvement I-114",
         "title": "Clarity votes",
         "subtitle": "Rate each lesson 1-5; averages feed generation quality."},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules/{seed_mid}",
         "focus": "#clarity",
         "caption": "The first lesson averages 4.5 from two votes, with a 1-5 form.",
         "assert_js": "() => { const h = document.querySelector('#clarity'); "
                      "return h ? h.textContent : 'missing'; }",
         "assert_want": "Clarity 4.5/5 from 2 votes"},
        {"type": "chrome", "duration": 12,
         "url_path": "/modules/{seed_mid}",
         "caption": "Voting 5 records the third vote.",
         "js": ["() => { const p = document.querySelector('#clarity'); "
                "const f = p ? p.nextElementSibling : null; "
                "if (!f || f.tagName !== 'FORM') return 'rate-form-missing'; "
                "const i = document.createElement('input'); i.type = 'hidden'; "
                "i.name = 'score'; i.value = '5'; f.appendChild(i); "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 4000)",
         "poll_want": "Clarity vote recorded",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => document.body.innerText.includes('Clarity vote recorded')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 7,
         "url_path": "/modules/{seed_mid}",
         "focus": "#clarity",
         "caption": "Back on the lesson: 4.7 from three votes.",
         "assert_js": "() => { const h = document.querySelector('#clarity'); "
                      "return h ? h.textContent : 'missing'; }",
         "assert_want": "Clarity 4.7/5 from 3 votes"},
        {"type": "terminal", "duration": 5,
         "caption": "Proof in the fixture DB: three votes, average 4.7.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import clarity as c; "
              "db = os.environ.get('DEMO_DB', 'groundwork.db'); "
              "avg, n = c.summaries(db, ['{seed_cid}'])['{seed_cid}']; "
              "print(f'average: {avg:.1f}/5 from {n} votes')"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 4",
         "title": "Yours teaches the author.",
         "subtitle": "clarity.py validates, stores, and averages lesson votes."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Two votes (4, 5) on the biggest module's first lesson."""
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
        c = con.execute(
            "SELECT id FROM concepts WHERE module_id=?"
            " ORDER BY rowid LIMIT 1", (mid,)).fetchone()
        if not c:
            return {"seeded": False, "reason": "module without concepts"}
        cid = c[0]
        con.execute("DELETE FROM clarity_ratings WHERE concept_id=?",
                    (cid,))
        con.execute("INSERT INTO clarity_ratings(concept_id, score)"
                    " VALUES(?, 4)", (cid,))
        con.execute("INSERT INTO clarity_ratings(concept_id, score)"
                    " VALUES(?, 5)", (cid,))
        con.commit()
        return {"seeded": True, "mid": mid, "cid": cid}
    finally:
        con.close()

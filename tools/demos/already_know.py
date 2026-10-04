"""Improvement demo: already-know skip (Batch 4, I-133).

Full functionality: learners self-certify a known lesson and its
cards come due in 30 days for delayed verification -- no fake passes
logged. seed_db clears any prior skip on the first lesson; the beat
skips it, so the verification date must appear.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "already-know",
    "kind": "improvement",
    "batch": 4,
    "item": "I-133",
    "title": "Already-know skip",
    "blurb": "Know it? Skip the line -- the cards verify you in 30 days.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 4 - Improvement I-133",
         "title": "Already-know skip",
         "subtitle": "Know it? Skip the line -- the cards verify you in 30 days."},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules/{seed_mid}",
         "focus": "#already-know",
         "caption": "Know it? The first lesson offers a verify-me-later skip.",
         "assert_js": "() => { const f = document.querySelector('#already-know'); "
                      "return f ? f.textContent : 'missing'; }",
         "assert_want": "Already know this"},
        {"type": "chrome", "duration": 12,
         "url_path": "/modules/{seed_mid}",
         "caption": "Skipping schedules verification 30 days out.",
         "js": ["() => { const f = document.querySelector('#already-know'); "
                "if (!f || f.tagName !== 'FORM') return 'skip-form-missing'; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 4000)",
         "poll_want": "verification due",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => document.body.innerText.includes('verification due')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 7,
         "url_path": "/modules/{seed_mid}",
         "focus": "#already-know",
         "caption": "Back on the lesson: verification is scheduled.",
         "assert_js": "() => { const p = document.querySelector('#already-know'); "
                      "return p ? p.textContent : 'missing'; }",
         "assert_want": "verified no later than"},
        {"type": "terminal", "duration": 6,
         "caption": "Proof: one skip row, and the cards pushed 30 days out.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; "
              "con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "rows = con.execute(\"SELECT verify_due FROM known_skips WHERE concept_id = '{seed_cid}'\").fetchall(); "
              "print('skip rows:', len(rows), '-> verify_due:', rows[0][0][:10] if rows else None); "
              "pushed = con.execute(\"SELECT COUNT(*) FROM cards WHERE concept_id = '{seed_cid}' AND due >= date('now', '+29 days')\").fetchone()[0]; "
              "print('cards pushed out:', pushed, 'of {seed_ncards}')"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 4",
         "title": "Skip the line, verify later.",
         "subtitle": "known.py logs the skip and schedules real verification."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Clear prior skips; pull the first lesson's cards due now.

    Cards due now prove the push: after the skip they must sit ~30
    days out instead.
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
        c = con.execute(
            "SELECT id FROM concepts WHERE module_id=?"
            " ORDER BY rowid LIMIT 1", (mid,)).fetchone()
        if not c:
            return {"seeded": False, "reason": "module without concepts"}
        cid = c[0]
        cards = con.execute(
            "SELECT id FROM cards WHERE concept_id=?", (cid,)).fetchall()
        if not cards:
            return {"seeded": False, "reason": "concept without cards"}
        con.execute("DELETE FROM known_skips WHERE concept_id=?", (cid,))
        con.execute("UPDATE cards SET due='2000-01-01T00:00:00Z'"
                    " WHERE concept_id=?", (cid,))
        con.commit()
        return {"seeded": True, "mid": mid, "cid": cid,
                "ncards": len(cards)}
    finally:
        con.close()

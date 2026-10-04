"""Feature demo: coverage timeline (Batch 1).

Full functionality: History's coverage section lists every session --
what it made (cards), what stuck (attempts, owned) -- newest first,
each row linking to its module. seed_db stamps the newest module with
a distinctive date so the timeline has a verifiable first row, and
ensures at least one review exists so the section renders.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "coverage-timeline",
    "kind": "feature",
    "batch": 1,
    "item": "F-282",
    "title": "Coverage timeline",
    "blurb": "Every session, what it made, and what stuck.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 1 - Feature coverage-timeline",
         "title": "Coverage timeline",
         "subtitle": "Every session, what it made, and what stuck."},
        {"type": "chrome", "duration": 12,
         "url_path": "/reviews#coverage",
         "focus": "#coverage",
         "caption": "History's coverage timeline: every session, its cards, attempts, owned.",
         "assert_js": "() => !!document.querySelector('#coverage') && "
                      "document.body.innerText.includes('{seed_day}') && "
                      "!!document.querySelector(\"a[href='/modules/{seed_mid}']\")",
         "assert_want": "True"},
        {"type": "chrome", "duration": 9,
         "url_path": "/modules/{seed_mid}",
         "caption": "Each row links to its session: cards, lessons, owned progress.",
         "assert_js": "() => location.pathname.includes('{seed_mid}') && "
                      "!!document.querySelector(\"a[href='/modules']\")",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "Sessions, attempts, newest date: the timeline is modules plus review counts.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "print('sessions:', con.execute('SELECT COUNT(*) FROM modules').fetchone()[0]); "
              "print('attempts:', con.execute('SELECT COUNT(*) FROM reviews').fetchone()[0]); "
              "print('newest session:', con.execute('SELECT substr(created_at,1,10) FROM modules ORDER BY created_at DESC LIMIT 1').fetchone()[0])"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 1",
         "title": "Sessions into a story.",
         "subtitle": "history.py renders the timeline from modules plus review counts."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Stamp the newest module with a distinctive date; ensure a review exists.

    The timeline orders modules by created_at DESC, so stamping the
    newest module keeps it row one with a verifiable date cell. The
    section only renders when the reviews table is non-empty, so an
    empty fixture gets one planted review.
    """
    con = sqlite3.connect(db_path)
    try:
        m = con.execute(
            "SELECT id FROM modules ORDER BY created_at DESC LIMIT 1").fetchone()
        if not m:
            return {"seeded": False, "reason": "no modules"}
        mid = m[0]
        day = "2026-10-01"
        con.execute("UPDATE modules SET created_at=? WHERE id=?",
                    (day + "T08:00:00Z", mid))
        n_rev = con.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
        if not n_rev:
            card = con.execute(
                "SELECT cards.id FROM cards JOIN concepts"
                " ON concepts.id = cards.concept_id"
                " WHERE concepts.module_id=? LIMIT 1", (mid,)).fetchone()
            if not card:
                card = con.execute(
                    "SELECT id FROM cards LIMIT 1").fetchone()
            if card:
                con.execute(
                    "INSERT INTO reviews(card_id, grade, confidence, submission)"
                    " VALUES(?, 4, 3, 'coverage seed')", (card[0],))
        con.commit()
        sessions = con.execute("SELECT COUNT(*) FROM modules").fetchone()[0]
        attempts = con.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
        return {"seeded": True, "mid": mid, "day": day,
                "sessions": sessions, "attempts": attempts}
    finally:
        con.close()

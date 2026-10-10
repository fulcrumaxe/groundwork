"""Feature demo: spaced teaching (F-90).

Full behavior: a concept first attempted 30+ days ago returns to
the Due queue beside the learner's own first words, with a fresh
self-explain prompt. seed_db plants a 45-day-old first attempt
with a marker recording; the Due beat films the live re-teach
box targeting that concept only.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

MARKER = "reteach-seed own words about this idea"

SCENARIO = {
    "id": "reteach",
    "kind": "feature",
    "batch": 20,
    "item": "F-90",
    "title": "Re-taught after 30 days",
    "blurb": "A month-old concept returns with your own words beside a fresh prompt.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 20 - Feature F-90",
         "title": "Re-taught after 30 days",
         "subtitle": "Your first words return beside a fresh explain-it-again prompt."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b20-reteach",
         "caption": "Status documents the ritual with a live sample box.",
         "assert_js": "() => !!document.querySelector('#status-b20-reteach') && "
                      "document.body.innerText.includes('totals two numbers')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule: 30+ days returns, 29 stays quiet, garbage fails closed.",
         "commands": [
             ["python3", "-c",
              "from groundwork import reteach as m; "
              "print('45d:', m.due_for_reteach('2000-01-01T00:00:00Z', now='2000-02-15')); "
              "print('29d:', m.due_for_reteach('2000-01-02T00:00:00Z', now='2000-01-31')); "
              "print('garbage:', m.due_for_reteach('soon', now='2000-01-31')); "
              "rows = m.first_attempts([{'name': 'add', 'reviewed_at': '2000-01-01', 'submission': 'my words'}]); "
              "print('box:', 'Your words from then' in m.reteach_box_html(rows), '| empty:', repr(m.reteach_box_html([])))"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/due",
         "focus": "#reteach",
         "caption": "The Due queue re-teaches the seeded concept: its name, your old words, a fresh prompt.",
         "assert_js": "() => { const b = document.querySelector('#reteach'); "
                      "return !!b && b.innerText.includes('{seed_name}') && "
                      "b.innerText.includes('reteach-seed own words') && "
                      "b.innerText.includes('Explain {seed_name} again'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 5,
         "caption": "Proof in the fixture: the seeded first attempt is 45 days old.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "row = con.execute(\"SELECT concepts.name, MIN(reviews.reviewed_at) FROM reviews "
              "JOIN cards ON cards.id = reviews.card_id JOIN concepts ON concepts.id = cards.concept_id "
              "WHERE concepts.name='{seed_name}'\").fetchone(); "
              "print('first_seen:', row[0], row[1][:10])"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 20",
         "title": "Teach it again, better.",
         "subtitle": "reteach.py watches first attempts -- fresh databases see no box."},
    ],
}


def _safe(name) -> bool:
    return bool(name) and all(ch.isalnum() or ch in " _-." for ch in name)


def seed_db(db_path: str) -> dict:
    """A 45-day-old first attempt with a marker recording."""
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT concepts.name, cards.id FROM cards"
            " JOIN concepts ON concepts.id = cards.concept_id"
            " ORDER BY concepts.name, cards.rowid").fetchall()
        seen = set()
        target = None
        for name, card_id in rows:
            if not _safe(name) or name in seen:
                continue
            seen.add(name)
            target = (name, card_id)
            break
        if not target:
            return {"seeded": False, "reason": "no safe concept"}
        name, card_id = target
        stamp = (datetime.now(timezone.utc) - timedelta(days=45)).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        con.execute("INSERT INTO reviews(card_id, grade, confidence,"
                    " reviewed_at, submission) VALUES(?, 3, 3, ?, ?)",
                    (card_id, stamp, MARKER))
        con.commit()
        return {"seeded": True, "name": name, "card_id": card_id}
    finally:
        con.close()

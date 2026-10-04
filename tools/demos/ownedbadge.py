"""Improvement demo: Owned badge reveal animation (I-58).

Full behavior: newly Owned concepts celebrate with a calm 240ms
fade+scale on a dedicated .owned-badge class, sealed with a CSS ring
-- shapes and text only, no emoji; reduced-motion users see the end
state instantly. seed_db makes the first concept of the first module
Owned (a passing modify-grade review plus a second attempt); the
module page chip wears the reveal class.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-ownedbadge-62"

SCENARIO = {
    "id": "ownedbadge",
    "kind": "improvement",
    "batch": 10,
    "item": "I-58",
    "title": "Owned badge reveal",
    "blurb": "Newly Owned concepts celebrate with a calm quarter-second reveal.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 10 - Improvement I-58",
         "title": "Owned badge reveal",
         "subtitle": "Owned, celebrated -- a quarter-second, no emoji."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b10-ownedbadge",
         "caption": "Status shows the live sample: ring seal, 240ms, reduced-motion safe.",
         "assert_js": "() => !!document.querySelector('#status-b10-ownedbadge') && "
                      "!!document.querySelector('.owned-badge')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: Owned gains the class, every other word stays plain.",
         "commands": [
             ["python3", "-c",
              "from groundwork import ownedbadge as m; "
              "print(m.badge_html('Owned')); "
              "print(m.badge_class('Owned'), '|', m.badge_class('Learning')); "
              "print(m.badge_css()[:120])"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/modules/{seed_module_id}",
         "focus": "section[id^='lesson-']",
         "caption": "The Owned concept chip wears the reveal class -- earned, then celebrated.",
         "assert_js": "() => !!document.querySelector('.owned-badge')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 10",
         "title": "Earned, then celebrated.",
         "subtitle": "ownedbadge.py reveals the chip -- chiplinks wires it to lessons."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Make the first concept of the first module Owned.

    Owned needs a passing grade on a modify/create card plus 2+
    attempts, so the seed plants one far-future type-62 (modify)
    card on the concept and two passing reviews on it.
    """
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT m.id, c.id FROM modules m JOIN concepts c"
            " ON c.module_id = m.id"
            " ORDER BY m.rowid, c.rowid LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no modules"}
        mid, cid = row
        con.execute("DELETE FROM reviews WHERE card_id=?", (CARD_ID,))
        con.execute(
            "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
            " front, back, payload, due)"
            " VALUES(?, ?, '62', ?, ?, ?, '2030-01-01T00:00:00Z')",
            (CARD_ID, cid, "seed card (never due)",
             "seed", json.dumps({"grounded": True})))
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, submission)"
            " VALUES(?, 5, 4, 'seed pass')", (CARD_ID,))
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, submission)"
            " VALUES(?, 4, 3, 'seed pass')", (CARD_ID,))
        con.commit()
        return {"seeded": True, "module_id": mid, "card_id": CARD_ID}
    finally:
        con.close()

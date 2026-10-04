"""Improvement demo: difficulty dots (Batch 1).

Full functionality: every Due card wears a 5-dot FSRS difficulty meter
(cards._difficulty_dots) with the exact number on hover; the lead card
carries the #difficulty tour anchor. seed_db forces one card due-first
with stored difficulty 0.8, so the meter reads 4 of 5 dots.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "difficulty-dots",
    "kind": "improvement",
    "batch": 1,
    "item": "I-75",
    "title": "Difficulty dots",
    "blurb": "Five-dot FSRS difficulty meter on every card. Hover for the number.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 1 - Improvement difficulty-dots",
         "title": "Difficulty dots",
         "subtitle": "Five-dot FSRS difficulty meter on every card."},
        {"type": "chrome", "duration": 9,
         "url_path": "/due",
         "focus": "article.next",
         "caption": "The lead card wears its difficulty: 4 of 5 dots, number on hover.",
         "assert_js": "() => document.querySelector('#difficulty').getAttribute('title')",
         "assert_want": "Difficulty 4/5"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: FSRS difficulty times five, rounded to dots.",
         "commands": [
             ["python3", "-c",
              "from groundwork import cards as m; "
              "print('0.2 ->', m._difficulty_dots(0.2)); "
              "print('0.8 ->', m._difficulty_dots(0.8)); "
              "print('1.0 ->', m._difficulty_dots(1.0))"],
         ]},
        {"type": "terminal", "duration": 6,
         "caption": "The fixture proves it: this card's stored difficulty is 0.8.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "print(con.execute(\"SELECT difficulty FROM cards WHERE id='{seed_card_id}'\").fetchone())"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "caption": "In context: the meter sits beside the concept name on every card.",
         "assert_js": "() => document.querySelector('#difficulty').textContent",
         "assert_want": "●●●●○"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 1",
         "title": "Difficulty at a glance.",
         "subtitle": "Hover any meter for the exact number."},
    ],
}


def seed_db(db_path: str) -> dict:
    """One card due-first with stored difficulty 0.8 (4 of 5 dots).

    The most-overdue card renders first on /due and carries the
    #difficulty anchor (web.py tags the lead card only), so backdating
    one card to 2000 plus pinning difficulty 0.8 determines the exact
    meter the beats assert: title 'Difficulty 4/5', glyphs 4 filled.
    """
    con = sqlite3.connect(db_path)
    try:
        card = con.execute(
            "SELECT id FROM cards ORDER BY due LIMIT 1").fetchone()
        if not card:
            return {"seeded": False, "reason": "no cards"}
        cid = card[0]
        con.execute("UPDATE cards SET due='2000-01-01T00:00:00Z',"
                    " difficulty=0.8 WHERE id=?", (cid,))
        con.commit()
        return {"seeded": True, "card_id": cid,
                "difficulty": 0.8, "dots": 4}
    finally:
        con.close()

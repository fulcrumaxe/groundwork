"""Feature demo: cognitive-load guard (F-94).

Full behavior: when recent grades show strain (>=50% low), the Due session
plan admits only one new concept; reviews always survive. seed_db plants a
strained tail of failing reviews; the caller beat runs the real session
planner guarded vs unguarded on the live fixture.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "cogniload",
    "kind": "feature",
    "batch": 21,
    "item": "F-94",
    "title": "Cognitive-load guard",
    "blurb": "Strained sessions introduce fewer new concepts; reviews always survive.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 21 - Feature F-94",
         "title": "Cognitive-load guard",
         "subtitle": "Failing a lot? Fewer new ideas -- reviews always survive."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b21-cogniload",
         "caption": "Status documents the strain thresholds with a live sample.",
         "assert_js": "() => !!document.querySelector('#status-b21-cogniload')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 9,
         "caption": "The rule in one line: strain halves the cap, then floors it at one.",
         "commands": [
             ["python3", "-c",
              "from groundwork import cogniload as m; "
              "print('strained:', m.strain_of([1, 2, 1, 5, 1]), "
              "'-> cap', m.new_concept_cap([1, 2, 1, 5, 1])); "
              "print('rested:', m.strain_of([5, 4, 5]), "
              "'-> cap', m.new_concept_cap([5, 4, 5])); "
              "print('note:', m.guard_note([1, 2, 1, 5, 1]))"],
         ]},
        {"type": "terminal", "duration": 11,
         "caption": "The real planner on the strained fixture: many new ideas collapse to one.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; "
              "from groundwork import minisession as ms; "
              "db = os.environ.get('DEMO_DB', 'groundwork.db'); "
              "con = sqlite3.connect(db); "
              "due = [dict(id=r[0], due=r[1], concept=r[2]) for r in "
              "con.execute('SELECT cards.id, cards.due, concepts.name FROM cards "
              "JOIN concepts ON concepts.id = cards.concept_id')]; "
              "tried = {}; "
              "recent = []; "
              "rows = con.execute('SELECT card_id, grade FROM reviews ORDER BY rowid DESC').fetchall(); "
              "[tried.update({r[0]: tried.get(r[0], 0) + 1}) or recent.append(r[1]) for r in rows]; "
              "plain = ms.pick_cards(due); "
              "guarded = ms.pick_cards(due, recent=recent, tried=tried); "
              "new = lambda ps: len({c['concept'] for c in ps if not tried.get(c['id'], 0)}); "
              "print('recent tail:', recent[:10]); "
              "print('unguarded new concepts:', new(plain)); "
              "print('guarded new concepts:', new(guarded))"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/due",
         "focus": "#minisession",
         "caption": "The Due session box carries the guarded plan.",
         "assert_js": "() => { const b = document.querySelector('#minisession'); "
                      "return !!b && b.innerText.includes('About'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 21",
         "title": "Strained? Smaller steps.",
         "subtitle": "cogniload.py caps new concepts -- the guard never empties a plan."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a strained tail: eight failing reviews on distinct cards."""
    con = sqlite3.connect(db_path)
    try:
        cards = con.execute(
            "SELECT id FROM cards WHERE id NOT IN"
            " (SELECT card_id FROM reviews) LIMIT 8").fetchall()
        if len(cards) < 8:
            return {"seeded": False, "reason": "too few new cards"}
        for i, (cid,) in enumerate(cards):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, submission)"
                " VALUES(?, ?, 2, 'cogniload seed')",
                (cid, 1 if i % 2 else 2))
        con.commit()
        return {"seeded": True, "fails": len(cards)}
    finally:
        con.close()

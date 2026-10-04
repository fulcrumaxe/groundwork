"""Feature demo: personal bests (Batch 4, F-101).

Full functionality: History celebrates strongest memory (highest
stability), most practiced concept, and sharpest skill (best accuracy
with 3+ attempts) -- personal only, never streaks. seed_db stages
all three, so each must read exactly.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "personal-bests",
    "kind": "feature",
    "batch": 4,
    "item": "F-101",
    "title": "Personal bests",
    "blurb": "Strongest memory, most practiced, sharpest skill -- no streaks.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 4 - Feature F-101",
         "title": "Personal bests",
         "subtitle": "Strongest memory, most practiced, sharpest skill -- no streaks."},
        {"type": "terminal", "duration": 8,
         "caption": "The bests, computed directly: memory, practice, skill.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import bests as b; "
              "r = b.bests(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "print('strongest:', r['strong']['concept'], '%.0f-day' % r['strong']['stability']); "
              "print('practiced:', r['practiced']['concept'], r['practiced']['n'], 'attempts'); "
              "print('sharpest: %s (%.0f%% over %d)' % (r['sharp'][0], 100 * r['sharp'][1], r['sharp'][2]))"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/reviews",
         "focus": "#bests",
         "caption": "History frames your bests fondly: memory, practice, skill.",
         "assert_js": "() => { const h = document.querySelector('#bests'); "
                      "const p = h ? h.nextElementSibling : null; "
                      "const t = p ? p.textContent : ''; "
                      "return t.includes('Strongest memory: {seed_strong} (90-day stability)') + '|' + "
                      "t.includes('Most practiced: {seed_practiced} (5 attempts)') + '|' + "
                      "t.includes('Sharpest skill: recall (100% over 3 attempts)'); }",
         "assert_want": "true|true|true"},
        {"type": "terminal", "duration": 6,
         "caption": "The rows behind the bests: stability, attempts, skill buckets.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; "
              "con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "s = con.execute('SELECT concepts.name, MAX(cards.stability) FROM cards JOIN concepts ON concepts.id = cards.concept_id').fetchone(); "
              "print('max stability:', '%s %.0f-day' % s); "
              "p = con.execute('SELECT concepts.name, COUNT(*) FROM reviews JOIN cards ON cards.id = reviews.card_id JOIN concepts ON concepts.id = cards.concept_id GROUP BY concepts.id ORDER BY 2 DESC LIMIT 1').fetchone(); "
              "print('most reviews:', '%s %d' % p)"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 4",
         "title": "Fond, not streaky.",
         "subtitle": "bests.py reads stability, attempts, and skill accuracy."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Stage all three bests: 90-day memory, 5-attempt concept, recall skill.

    The practiced concept's five attempts land on explain cards at
    40%, so the 3-for-3 recall skill still wins sharpest; practice
    reviews spread over one concept so no recall concept ties it.
    """
    con = sqlite3.connect(db_path)
    try:
        strong = con.execute(
            "SELECT cards.id, concepts.name FROM cards"
            " JOIN concepts ON concepts.id = cards.concept_id"
            " ORDER BY cards.due LIMIT 1").fetchone()
        prac = con.execute(
            "SELECT cards.id, concepts.name FROM cards"
            " JOIN concepts ON concepts.id = cards.concept_id"
            " WHERE exercise_type = '5' ORDER BY cards.due LIMIT 1"
            ).fetchone()
        recall = con.execute(
            "SELECT id FROM cards WHERE exercise_type = '1'"
            " ORDER BY due LIMIT 3").fetchall()
        if not strong or not prac or len(recall) < 3:
            return {"seeded": False, "reason": "need varied cards"}
        con.execute("DELETE FROM reviews")
        con.execute("UPDATE cards SET stability=1.0")
        con.execute("UPDATE cards SET stability=90.1 WHERE id=?",
                    (strong[0],))
        for i, grade in enumerate((5, 5, 2, 2, 2)):
            con.execute("INSERT INTO reviews(card_id, grade, confidence,"
                        " submission) VALUES(?, ?, 3, ?)",
                        (prac[0], grade, f"best seed {i}"))
        for i, (cid,) in enumerate(recall):
            con.execute("INSERT INTO reviews(card_id, grade, confidence,"
                        " submission) VALUES(?, 5, 4, ?)",
                        (cid, f"best recall {i}"))
        con.commit()
        return {"seeded": True, "strong": strong[1],
                "practiced": prac[1]}
    finally:
        con.close()

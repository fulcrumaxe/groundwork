"""Feature demo: History deals the overconfidence card live (F-67 integration).

Full behavior: the History coach deals coach_card() from live
attempts -- firing only at 10+ attempts with a 25+ point gap, naming
the real weakest skill. seed_db plants skewed reviews on two skills
(recall gap 0.80, apply gap 0.60); the dealt card must name recall.
"""
from __future__ import annotations

import sqlite3

RECALL_CARDS = 4
APPLY_CARDS = 2
REVIEWS_PER_CARD = 2

SCENARIO = {
    "id": "coachcard",
    "kind": "feature",
    "batch": 15,
    "item": "F-67",
    "title": "History deals the card",
    "blurb": "Live attempts deal the intervention -- weakest skill named, small samples silent.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 15 - Feature F-67",
         "title": "History deals the card",
         "subtitle": "Live attempts deal the intervention -- weakest skill named."},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one call: two skewed skills deal naming the weaker; small-n stays silent.",
         "commands": [
             ["python3", "-c",
              "from groundwork import overconf as m; "
              "rows = [('recall', 1, 5)] * 8 + [('apply', 2, 5)] * 4; "
              "card = m.coach_card(rows); "
              "print('fires:', 'overconf-card' in card, '| names recall:', 'recall' in card); "
              "print('small-n silent:', m.coach_card([('recall', 1, 5)] * 9) == ''); "
              "print('modest silent:', m.coach_card([('recall', 5, 1)] * 12) == '')"],
         ]},
        {"type": "chrome", "duration": 11,
         "url_path": "/reviews",
         "focus": ".overconf-card",
         "caption": "History deals from the live rows: gap stated, weakest skill named.",
         "assert_js": "() => { const c = document.querySelector('.overconf-card'); "
                      "return !!c && c.textContent.includes('Overconfidence check') && "
                      "c.textContent.includes('Weakest spot: recall'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 6,
         "caption": "Proof in the fixture DB: twelve skewed attempts across two skills.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "rows = con.execute(\"SELECT cards.exercise_type, COUNT(*), AVG(reviews.grade), AVG(reviews.confidence)"
              " FROM reviews JOIN cards ON cards.id = reviews.card_id"
              " WHERE reviews.submission='coachcard seed'"
              " GROUP BY cards.exercise_type ORDER BY cards.exercise_type\").fetchall(); "
              "[print('type', r[0], '| n:', r[1], '| avg grade:', round(r[2], 1), '| avg conf:', round(r[3], 1)) for r in rows]"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 15",
         "title": "The gap deals, live.",
         "subtitle": "coach_card() reads History rows -- recall named weakest, habit attached."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Skewed reviews on recall (gap 0.80) and apply (gap 0.60).

    Apply rows land first so recall rows are newest -- recall wins
    any per-skill tie by listing order as well as by gap.
    """
    con = sqlite3.connect(db_path)
    try:
        apply_ids = [r[0] for r in con.execute(
            "SELECT id FROM cards WHERE exercise_type='10' ORDER BY rowid"
            " LIMIT ?", (APPLY_CARDS,)).fetchall()]
        recall_ids = [r[0] for r in con.execute(
            "SELECT id FROM cards WHERE exercise_type='1' ORDER BY rowid"
            " LIMIT ?", (RECALL_CARDS,)).fetchall()]
        if len(apply_ids) < APPLY_CARDS or len(recall_ids) < RECALL_CARDS:
            return {"seeded": False, "reason": "not enough type-1/10 cards"}
        for cid in apply_ids:
            for _ in range(REVIEWS_PER_CARD):
                con.execute(
                    "INSERT INTO reviews(card_id, grade, confidence,"
                    " submission) VALUES(?, 2, 5, 'coachcard seed')",
                    (cid,))
        for cid in recall_ids:
            for _ in range(REVIEWS_PER_CARD):
                con.execute(
                    "INSERT INTO reviews(card_id, grade, confidence,"
                    " submission) VALUES(?, 1, 5, 'coachcard seed')",
                    (cid,))
        con.commit()
        return {"seeded": True,
                "attempts": (len(apply_ids) + len(recall_ids))
                * REVIEWS_PER_CARD}
    finally:
        con.close()

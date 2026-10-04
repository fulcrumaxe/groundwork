"""Feature demo: README badge (Batch 4, F-386).

Full functionality: /badge.svg serves the live owned-count shield
for any README, from the same owned map as the Projects page.
seed_db owns exactly one concept, so the badge must read 1/N.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "readme-badge",
    "kind": "feature",
    "batch": 4,
    "item": "F-386",
    "title": "README badge",
    "blurb": "Your live owned count as an embeddable SVG shield.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 4 - Feature F-386",
         "title": "README badge",
         "subtitle": "Your live owned count as an embeddable SVG shield."},
        {"type": "terminal", "duration": 8,
         "caption": "The badge, rendered directly: one owned of every concept.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import badge as b; "
              "db = os.environ.get('DEMO_DB', 'groundwork.db'); "
              "print('counts:', b.counts(db)); "
              "print(b.badge_svg(db))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/status",
         "caption": "Status links the live badge next to the counts.",
         "assert_js": "() => { const s = document.querySelector('#status-badge a'); "
                      "return s ? s.getAttribute('href') : 'missing'; }",
         "assert_want": "/badge.svg"},
        {"type": "chrome", "duration": 8,
         "url_path": "/badge.svg",
         "caption": "The shield itself: 1 owned, served as a live image.",
         "js": ["() => { const s = document.querySelector('svg'); "
                "if (!s) return 'no-svg'; s.style.transform = 'scale(4)'; "
                "s.style.transformOrigin = '0 0'; return 'scaled'; }"],
         "assert_js": "() => { const s = document.querySelector('svg'); "
                      "return (s ? s.textContent : 'missing') + '|' + location.pathname; }",
         "assert_want": "1/{seed_total} concepts owned|/badge.svg"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 4",
         "title": "Proof, embeddable.",
         "subtitle": "badge.py shields the same owned map as Projects."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Own exactly one concept via a modify-type passing pair.

    Owned needs a grade>=4 pass on a modify/create exercise plus two
    attempts; wiping reviews first keeps every other concept unowned.
    """
    con = sqlite3.connect(db_path)
    try:
        mod = con.execute(
            "SELECT id, concept_id FROM cards WHERE exercise_type IN "
            "('12','14','19','20','27','24','23') ORDER BY due LIMIT 1"
            ).fetchone()
        if not mod:
            return {"seeded": False, "reason": "need a modify card"}
        con.execute("DELETE FROM reviews")
        for _ in range(2):
            con.execute("INSERT INTO reviews(card_id, grade, confidence,"
                        " submission) VALUES(?, 5, 4, 'badge seed')",
                        (mod[0],))
        total = con.execute("SELECT COUNT(*) FROM concepts").fetchone()[0]
        con.commit()
        return {"seeded": True, "owned_concept": mod[1], "total": total}
    finally:
        con.close()

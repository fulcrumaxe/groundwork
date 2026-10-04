"""Improvement demo: card deep-links (I-7).

Full behavior: every card carries a #card-<id> anchor on its module
page, and every History attempt links straight to the exact card it
graded. seed_db guarantees one review so History has an attempt to
point with; beats follow the link target on the module page.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "cardlinks",
    "kind": "improvement",
    "batch": 6,
    "item": "I-7",
    "title": "Card deep-links",
    "blurb": "Every History attempt links straight to the exact card.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 6 - Improvement I-7",
         "title": "Card deep-links",
         "subtitle": "Missed one? History jumps to the exact card -- no scrolling."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b6-cardlinks",
         "caption": "Status names the anchors: #card-<id> beside #lesson-<slug>.",
         "assert_js": "() => !!document.querySelector('#status-b6-cardlinks')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: blank ids fall back, never 404-shaped.",
         "commands": [
             ["python3", "-c",
              "from groundwork import cardlinks as m; "
              "print(m.card_url('abc', 'm1:ex002')); "
              "print(m.history_link('abc', 'm1:ex002', 'Attempt')); "
              "print(repr(m.card_url('', '')))"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/reviews",
         "focus": "#attempts",
         "caption": "History attempts link to the exact card -- module plus anchor.",
         "assert_js": "() => !!document.querySelector('#attempts') && "
                      "!!document.querySelector(\"a[href*='#card-']\")",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/modules/{seed_mid}#{seed_anchor}",
         "focus": "article[id='{seed_anchor}']",
         "caption": "The landing: the graded card's own article, anchored and lit.",
         "assert_js": "() => !!document.querySelector(\"article[id='{seed_anchor}']\")",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 6",
         "title": "Every attempt has an address.",
         "subtitle": "cardlinks.py anchors articles -- History just points."},
    ],
}


def _slug(token) -> str:
    """Fragment-safe slug mirroring cardlinks.card_anchor (no import)."""
    import re
    if not isinstance(token, str):
        return ""
    out = "".join(ch if (ch.isalnum() or ch in "-_") else "-"
                  for ch in token)
    return "card-" + "-".join(p for p in out.split("-") if p)


def seed_db(db_path: str) -> dict:
    """Ensure one review exists; return its module + card for the beats."""
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT concepts.module_id, cards.id FROM reviews"
            " JOIN cards ON cards.id = reviews.card_id"
            " JOIN concepts ON concepts.id = cards.concept_id"
            " ORDER BY reviews.rowid DESC LIMIT 1").fetchone()
        if not row:
            card = con.execute(
                "SELECT concepts.module_id, cards.id FROM cards"
                " JOIN concepts ON concepts.id = cards.concept_id"
                " LIMIT 1").fetchone()
            if not card:
                return {"seeded": False, "reason": "no cards"}
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, submission)"
                " VALUES(?, 2, 3, 'deep-link seed')", (card[1],))
            con.commit()
            row = card
        return {"seeded": True, "mid": row[0], "cid": row[1],
                "anchor": _slug(row[1])}
    finally:
        con.close()

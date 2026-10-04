"""Improvement demo: scroll position kept (I-14).

Full behavior: answering a card and coming back lands you where you
left off, not at the top. The queue records scrollY per origin and
tags each card article; the review POST anchors the origin; the
result screen restores the offset and links back to the anchored
card. seed_db plants one flashcard as the sole due card; the /due
beat answers it natively and polls the anchored back link.
"""
from __future__ import annotations

import sqlite3

CARD_ID = "demo-scrollpos-1"

SCENARIO = {
    "id": "scrollpos",
    "kind": "improvement",
    "batch": 6,
    "item": "I-14",
    "title": "Scroll position kept",
    "blurb": "Answering a card lands you back where you left off.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 6 - Improvement I-14",
         "title": "Scroll position kept",
         "subtitle": "Answer, return, keep reading -- the queue holds your place."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b6-scrollpos",
         "caption": "Status documents the loop: record on queue, restore on result.",
         "assert_js": "() => !!document.querySelector('#status-b6-scrollpos')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: origins anchor to cards, keys drop anchors.",
         "commands": [
             ["python3", "-c",
              "from groundwork import scrollpos as m; "
              "print(m.back_href('/due', 'c9')); "
              "print(m.storage_key('/due#card-c9')); "
              "print(m.origin_field('/due', 'c9'))"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/due",
         "caption": "The queue side: the card article is anchored, the form names its origin.",
         "assert_js": "() => !!document.querySelector("
                      "\"article[id='card-{seed_card_id}']\") && "
                      "!!document.querySelector(\"input[name='origin'][value='/due']\")",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Answer it -- the result links back to the anchored card.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const sel = f.querySelector(\"select[name='answer']\"); "
                "if (!sel) return 'no-select'; sel.value = '4'; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Continue where you left off",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => { const a = Array.prototype.find.call("
                      "document.querySelectorAll('a'), "
                      "el => el.textContent.includes('Continue where')); "
                      "return !!a && a.getAttribute('href').includes('#card-'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 6",
         "title": "Keep reading.",
         "subtitle": "scrollpos.py pairs record and restore -- anchors do the rest."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one flashcard as the sole due card in the fixture."""
    con = sqlite3.connect(db_path)
    try:
        concept = con.execute(
            "SELECT id FROM concepts ORDER BY rowid LIMIT 1").fetchone()
        if not concept:
            return {"seeded": False, "reason": "no concepts"}
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        con.execute("DELETE FROM reviews WHERE card_id=?", (CARD_ID,))
        con.execute(
            "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
            " front, back, payload, due)"
            " VALUES(?, ?, '1', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, concept[0],
             "Recall: what does this module teach?",
             "Its core concept, in your own words.",
             "{}"))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()

"""Improvement demo: click-to-pair matching (I-164).

Full behavior: match-pairs cards pair by tapping a left item then
its right partner -- pairs land in the same m<i> fields the letter
grader reads, so grading is untouched. seed_db plants one etype-30
card as the sole due card.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-matchpair-164"

PAYLOAD = {"left": ["timeout", "retries"],
           "right": ["config", "policy"]}

SCENARIO = {
    "id": "matchpair",
    "kind": "improvement",
    "batch": 25,
    "item": "I-164",
    "title": "Click-to-pair matching",
    "blurb": "Tap left, tap right -- pairs land where the grader reads.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 25 - Improvement I-164",
         "title": "Click-to-pair matching",
         "subtitle": "No more letter typing -- typed boxes stay as fallback."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b25-matchpair",
         "caption": "Status shows the live pairing widget on a demo pair.",
         "assert_js": "() => !!document.querySelector('#status-b25-matchpair') "
                      "&& !!document.querySelector('.mpair')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Letters resolve per row; pairs serialize to i=LETTER.",
         "commands": [
             ["python3", "-c",
              "from groundwork import matchpair as m; "
              "print('letter:', m.letter_for(['config', 'policy'], 'policy')); "
              "print(m.serialize({0: 'b', 1: 'a'})); "
              "print('empty sides:', repr(m.pair_html('c', [], ['x'])))"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/due",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const l = f.querySelector(\"button[data-mp='l'][data-i='0']\"); "
                "const r = f.querySelector(\"button[data-mp='r'][data-L='B']\"); "
                "if (!l || !r) return 'no-buttons'; l.click(); r.click(); "
                "var h = f.querySelector('input[name=m0]'); "
                "h.setAttribute('value', h.value); return h.value; }"],
         "focus": "form[action='/cards/{seed_card_id}/review']",
         "caption": "Tap 0, tap B -- the typing box fills itself.",
         "poll_js": "() => document.querySelector(\"form[action='/cards/{seed_card_id}/review'] input[name=m0]\").value",
         "poll_want": "B",
         "poll_required": True,
         "assert_js": "() => document.querySelector(\"form[action='/cards/{seed_card_id}/review'] input[name=m0]\").value === 'B'",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 25",
         "title": "Tap, tap, graded.",
         "subtitle": "matchpair.py writes the same fields -- grader untouched."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one match-pairs card as the sole due card."""
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT id FROM concepts ORDER BY rowid LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no concepts"}
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        con.execute("DELETE FROM reviews WHERE card_id=?", (CARD_ID,))
        con.execute(
            "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
            " front, back, payload, due)"
            " VALUES(?, ?, '30', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0],
             "Match each setting to its owner: timeout, retries.",
             "timeout=config, retries=policy",
             json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()

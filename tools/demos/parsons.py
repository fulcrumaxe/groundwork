"""Improvement demo: stable Parsons drag lists (I-91).

Full behavior: Due-queue Parsons cards (type 11) render ol.parsons
with an inline N x 44px min-height reserve, so dragging lines only
changes li order -- never page height. seed_db plants a 5-line type-11
card as the sole due card; the /due beats show the 220px reserve in
the live list and submit the correct order for a pass verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-b18-parsons"
LINES = ["def total(xs):", "    out = 0", "    for x in xs:",
         "        out += x", "    return out"]
# Displayed shuffled; solution order L0..L4 sits at indices 3 1 4 0 2.
SHOWN = [LINES[3], LINES[1], LINES[4], LINES[0], LINES[2]]
ANSWER = "3 1 4 0 2"

SCENARIO = {
    "id": "parsons",
    "kind": "improvement",
    "batch": 18,
    "item": "I-91",
    "title": "Stable Parsons drag lists",
    "blurb": "Parsons code-order lists reserve space for every line before first paint -- the submit row stays put.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 18 - Improvement I-91",
         "title": "Stable Parsons drag lists",
         "subtitle": "N x 44px reserved before first paint -- reorder moves lines, never the page."},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one call: 5 lines reserve 220px; empty lists render legacy-identical.",
         "commands": [
             ["python3", "-c",
              "from groundwork import parsons as m; "
              "lines = ['a', 'b', 'c', 'd', 'e']; "
              "print('reserve 5 lines:', m.reserve_px(lines), 'px'); "
              "print('floor css:', m.parsons_css()); "
              "print('empty has no reserve:', 'min-height' not in m.list_html('c', []))"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b18-parsons",
         "caption": "Status homes the improvement: min-height, never height, so wrapped lines never clip.",
         "assert_js": "() => !!document.querySelector('#status-b18-parsons')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "form[action='/cards/{seed_card_id}/review']",
         "caption": "The live Due card: 5 shuffled lines inside a 220px-reserved list.",
         "assert_js": "() => { const ol = document.querySelector('ol.parsons'); "
                      "return !!ol && (ol.getAttribute('style') || '').includes("
                      "'min-height:220px'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 12,
         "url_path": "/due",
         "caption": "Type the correct order -- the verdict passes on the reserved list.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const nums = f.querySelector(\"input[name='answer_text']\"); "
                "if (!nums) return 'no-answer-text'; nums.value = '3 1 4 0 2'; "
                "const hid = f.querySelector(\"input[type='hidden'][name='answer']\"); "
                "if (hid) hid.value = '3 1 4 0 2'; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Correct order",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Correct order')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 18",
         "title": "Drag lines, not layouts.",
         "subtitle": "parsons.py reserves the space -- parkeys delegates, byte-identical when empty."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one 5-line type-11 card (pipeline shape) as the sole due card."""
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT id FROM concepts ORDER BY rowid LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no concepts"}
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        con.execute("DELETE FROM reviews WHERE card_id=?", (CARD_ID,))
        block = "\n".join(LINES)
        payload = {"lines": SHOWN, "solution": LINES, "tests": "",
                   "code_block": block}
        con.execute(
            "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
            " front, back, payload, due)"
            " VALUES(?, ?, '11', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], "Reorder these lines into working code.",
             block, json.dumps(payload)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID, "answer": ANSWER}
    finally:
        con.close()

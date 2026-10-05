"""Improvement demo: sound-free press micro-interactions (I-80).

Full behavior: the app's real buttons and card actions shrink to
scale(0.97) while pressed over 120ms via transition:transform --
pure CSS, no JS, no sound. A prefers-reduced-motion override renders
the press instant and static, and focus outlines stay untouched.
Status documents the rule; Due and Modules prove the live head wire
on real buttons and whole-card links; terminal beats prove the
budget and the selector coverage.
"""
from __future__ import annotations

import sqlite3

CARD_ID = "demo-pressfx-1"

SCENARIO = {
    "id": "pressfx",
    "kind": "improvement",
    "batch": 12,
    "item": "I-80",
    "title": "Press micro-interactions",
    "blurb": "Buttons and cards press back a touch while you hold them -- silent, instant, and still for reduced-motion users.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 12 - Improvement I-80",
         "title": "Press micro-interactions",
         "subtitle": "Hold any button: it shrinks a touch -- silent, no JS."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b12-pressfx",
         "caption": "Status documents the press: scale(0.97) over 120ms on every real button.",
         "assert_js": "() => { const a = document.querySelector("
                      "'#status-b12-pressfx'); return !!a && "
                      "a.parentElement.innerText.includes('scale(0.97)'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: five selectors, 120ms, silent under reduced motion.",
         "commands": [
             ["python3", "-c",
              "from groundwork import pressfx as m; "
              "print(m.pressfx_css()); "
              "print('duration:', m.duration_ms()); "
              "print('outline-free:', 'outline' not in m.pressfx_css().lower())"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/due",
         "focus": "form[action='/cards/{seed_card_id}/review']",
         "caption": "The live Due form: real buttons carry the 120ms press rule in the head wire.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "const css = Array.from(document.querySelectorAll("
                      "'head style')).map(s => s.textContent).join('\\n'); "
                      "return !!f && !!f.querySelector('button') && "
                      "css.includes('transition:transform 120ms') && "
                      "css.includes('scale(0.97)'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules",
         "focus": ".modcard",
         "caption": "Whole-card links press too -- .card-link carries the same :active rule.",
         "assert_js": "() => { const l = document.querySelector('.card-link'); "
                      "const css = Array.from(document.querySelectorAll("
                      "'head style')).map(s => s.textContent).join('\\n'); "
                      "return !!l && css.includes('.card-link:active'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 12",
         "title": "Press back, softly.",
         "subtitle": "pressfx.py styles the hold -- reduced motion stays still."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Clone one card under a colon-free id as the sole due card.

    Real card ids contain ':' (stripped by scrollpos.card_anchor),
    so the Due form focus needs a planted id like the ratelimit
    pilot. The clone is a textarea-type card (5/6) so the filmed
    form shows a real Submit button.
    """
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT concept_id, exercise_type, front, back, payload"
            " FROM cards WHERE exercise_type IN ('5','6')"
            " ORDER BY due LIMIT 1").fetchone()
        if not row:
            row = con.execute(
                "SELECT concept_id, exercise_type, front, back, payload"
                " FROM cards ORDER BY due LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no cards"}
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        con.execute("DELETE FROM reviews WHERE card_id=?", (CARD_ID,))
        con.execute(
            "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
            " front, back, payload, due)"
            " VALUES(?, ?, ?, ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID,) + tuple(row))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()

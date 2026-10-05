"""Improvement demo: session-complete hero (I-70).

Full behavior: when nothing is due, the queue renders a calm
full-width banner -- static inline-SVG illustration plus today's
answered count, accuracy, and next-due line -- with the next-action
links kept so the no-dead-end contract holds. seed_db empties the
queue; /due shows the hero.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "donehero",
    "kind": "improvement",
    "batch": 11,
    "item": "I-70",
    "title": "Session-complete hero",
    "blurb": "Empty queue, calm banner -- stats plus a next step.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 11 - Improvement I-70",
         "title": "Session-complete hero",
         "subtitle": "All caught up -- and here is what is next."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b11-donehero",
         "caption": "Status homes the hero: answered, accuracy, next due, no dead end.",
         "assert_js": "() => !!document.querySelector('#status-b11-donehero')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: plain ints in, banner out -- garbage coerces to calm.",
         "commands": [
             ["python3", "-c",
              "from groundwork import donehero as m; "
              "print(m.done_hero_html(7, 86, 'tomorrow')[:200]); "
              "print(m.done_hero_html('x', 999, None)[:120])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#done-hero",
         "caption": "The emptied queue wears the hero -- stats up top, links intact.",
         "assert_js": "() => !!document.querySelector('#done-hero') && "
                      "document.body.innerText.includes('All caught up')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 11",
         "title": "Done looks good.",
         "subtitle": "donehero.py celebrates quietly -- no confetti, no dead end."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Empty the queue so the hero renders."""
    con = sqlite3.connect(db_path)
    try:
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        con.commit()
        return {"seeded": True}
    finally:
        con.close()

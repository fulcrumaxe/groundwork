"""Improvement demo: Due queue as a mission briefing (I-73).

Full behavior: the Due queue reads like a briefing -- every card
carries a MISSION 01-style badge via a CSS counter on the existing
#queue article selectors (zero JS), and the #digest Today block
styles as the briefing header. seed_db plants three due cards in one
module; Chrome proves the Status anchor, the digest header, and the
numbered queue.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "briefing",
    "kind": "improvement",
    "batch": 12,
    "item": "I-73",
    "title": "Due briefing",
    "blurb": "The Due queue reads like a briefing -- numbered mission cards, header up top.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 12 - Improvement I-73",
         "title": "Due briefing",
         "subtitle": "The queue reads like a mission board -- numbered cards, header up top."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b12-briefing",
         "caption": "Status documents the briefing: CSS-counter badges, zero JS.",
         "assert_js": "() => !!document.querySelector('#status-b12-briefing')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: MISSION labels pad to 01, bad input fails closed.",
         "commands": [
             ["python3", "-c",
              "from groundwork import briefing as m; "
              "print(m.briefing_number(1), '|', m.briefing_number(3), '|', "
              "m.briefing_number(120), '|', m.briefing_number('x')); "
              "css = m.briefing_css(); "
              "print('counter:', 'counter(mission' in css, "
              "'| style-tag:', '<style' in css.lower())"],
         ]},
        {"type": "chrome", "duration": 9,
         "url_path": "/due",
         "focus": "#digest",
         "caption": "The Today block is the briefing header -- due count up top.",
         "assert_js": "() => !!document.querySelector('#digest') && "
                      "Array.from(document.querySelectorAll('head style')).some("
                      "s => s.textContent.includes('counter-reset:mission'))",
         "assert_want": "True"},
        {"type": "chrome", "duration": 10,
         "url_path": "/due",
         "caption": "Every due card carries a MISSION badge -- counter numbers, no markup.",
         "js": ["() => { const top = document.querySelector('#top'); "
                "if (top) top.remove(); "
                "const q = document.querySelector('#queue'); "
                "if (!q) return 'no-queue'; "
                "Array.from(q.children).forEach(el => { "
                "if (el.tagName !== 'DETAILS' || !el.querySelector('article')) el.remove(); }); "
                "q.querySelectorAll('article').forEach(a => { "
                "a.querySelectorAll('h3 ~ *').forEach(el => el.remove()); }); "
                "return 'pruned:' + q.querySelectorAll('article').length; }"],
         "assert_js": "() => { const arts = document.querySelectorAll('#queue article'); "
                      "if (arts.length < 3) return 'few:' + arts.length; "
                      "const css = Array.from(document.querySelectorAll('head style')).some("
                      "s => s.textContent.includes('counter(mission')); "
                      "if (!css) return 'no-css'; "
                      "return getComputedStyle(arts[0], '::before').getPropertyValue('content'); }",
         "assert_want": "MISSION"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 12",
         "title": "Fly the queue.",
         "subtitle": "briefing.py numbers missions -- snooze or reorder, badges follow."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Three due cards in one module as the sole due queue.

    Same-module cards render inside one queue group so the numbered
    MISSION badges read top to bottom; everything else parks at 2030
    so the digest counts exactly three due now.
    """
    con = sqlite3.connect(db_path)
    try:
        mod = con.execute(
            "SELECT concepts.module_id FROM cards"
            " JOIN concepts ON concepts.id = cards.concept_id"
            " GROUP BY concepts.module_id HAVING COUNT(*) >= 3"
            " ORDER BY COUNT(*) DESC LIMIT 1").fetchone()
        if not mod:
            return {"seeded": False, "reason": "no module with 3 cards"}
        cards = con.execute(
            "SELECT cards.id FROM cards"
            " JOIN concepts ON concepts.id = cards.concept_id"
            " WHERE concepts.module_id = ? ORDER BY cards.id LIMIT 3",
            (mod[0],)).fetchall()
        if len(cards) < 3:
            return {"seeded": False, "reason": "fewer than 3 cards"}
        ids = [c[0] for c in cards]
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        con.execute(
            f"UPDATE cards SET due='2000-01-01T00:00:00Z' WHERE id IN ({','.join('?' * 3)})",
            ids)
        con.commit()
        return {"seeded": True, "card_id": ids[0],
                "card2": ids[1], "card3": ids[2]}
    finally:
        con.close()

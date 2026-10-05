"""Improvement demo: calm Owned celebration banner (I-79).

Full behavior: newly Owned concepts trigger a full-width .ownbanner
block -- garden-echo copy ("taken root"), the existing chip
owned-badge vocabulary, at most one <=250ms fade gated by
prefers-reduced-motion. Status shows the live sample, the head wire
carries the CSS onto every page (proven on a real Due queue), and
terminal beats prove escaping plus the motion budget.
"""
from __future__ import annotations

import sqlite3

CARD_ID = "demo-ownbanner-1"

SCENARIO = {
    "id": "ownbanner",
    "kind": "improvement",
    "batch": 12,
    "item": "I-79",
    "title": "Owned banner",
    "blurb": "Newly Owned concepts get a calm full-width banner -- no confetti, just the milestone.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 12 - Improvement I-79",
         "title": "Owned banner",
         "subtitle": "Owned -- taken root. No confetti, no streaks, just the milestone."},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b12-ownbanner",
         "caption": "Status shows the live banner: Owned chip, garden-echo copy, taken root.",
         "assert_js": "() => { const a = document.querySelector("
                      "'#status-b12-ownbanner'); const b = document.querySelector("
                      "'.ownbanner'); return !!a && !!b && "
                      "b.innerText.includes('taken root'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: escaped name, calm copy, one short fade.",
         "commands": [
             ["python3", "-c",
              "from groundwork import ownbanner as m; "
              "print(m.ownbanner_html('Loops')); "
              "print('fade_ms:', m.fade_ms()); "
              "print('escaped:', '&lt;script&gt;' in m.ownbanner_html('<script>'))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "Every page carries the banner styles in its head wire -- one fade under 250ms.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "const css = Array.from(document.querySelectorAll("
                      "'head style')).map(s => s.textContent).join('\\n'); "
                      "return !!f && css.includes('ownbanner-fade') && "
                      "css.includes('prefers-reduced-motion'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 6,
         "caption": "Calm by the numbers: fade under budget, instant for reduced motion, ASCII-only.",
         "commands": [
             ["python3", "-c",
              "import re; from groundwork import ownbanner as m; "
              "css = m.ownbanner_css(); "
              "print('durations:', re.findall(r'\\d+ms', css)); "
              "print('reduced-motion:', 'prefers-reduced-motion' in css); "
              "print('ascii:', css.isascii() and m.ownbanner_html('Loops').isascii())"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 12",
         "title": "Just the milestone.",
         "subtitle": "ownbanner.py renders the banner -- the head wire styles it everywhere."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Clone one card under a colon-free id as the sole due card.

    Real card ids contain ':' (stripped by scrollpos.card_anchor),
    so #card-{seed} focusing needs a planted id like the ratelimit
    pilot. The clone keeps a valid widget shape (type/front/back).
    """
    con = sqlite3.connect(db_path)
    try:
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
